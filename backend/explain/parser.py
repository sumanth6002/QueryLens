"""Execution-plan parsers for MySQL EXPLAIN output."""

from __future__ import annotations

from typing import Any

from explain.models import ExplainSummary, ExplainTreeNode, PerformanceIssue


def classify_scan(access_type: str | None, key: str | None) -> str:
    if not access_type:
        return "operation"
    normalized = access_type.upper()
    if normalized == "ALL":
        return "table_scan"
    if normalized == "INDEX":
        return "full_index_scan"
    if normalized in {"REF", "EQ_REF", "CONST", "SYSTEM", "RANGE"} and key:
        return "index_seek"
    if key:
        return "index_seek"
    return "other"


class _NodeIdFactory:
    def __init__(self) -> None:
        self._counter = 0

    def next_id(self) -> str:
        self._counter += 1
        return f"node-{self._counter}"


def _build_table_node(table: dict[str, Any], ids: _NodeIdFactory) -> ExplainTreeNode:
    access_type = table.get("access_type") or table.get("type")
    key = table.get("key")
    possible_keys = table.get("possible_keys")
    if isinstance(possible_keys, list):
        possible_keys = ", ".join(possible_keys)
    extra = table.get("extra") or table.get("Extra") or table.get("attached_condition") or table.get("message")
    rows = table.get("rows_examined_per_scan") or table.get("rows") or table.get("rows_produced_per_join")
    return ExplainTreeNode(
        id=ids.next_id(),
        node_type="table",
        label=table.get("table_name") or table.get("table") or "unknown_table",
        access_type=access_type,
        key=key,
        possible_keys=possible_keys,
        rows=rows,
        filtered=table.get("filtered"),
        extra=extra,
        scan_category=classify_scan(access_type, key),
    )


def _build_operation_node(label: str, children: list[ExplainTreeNode], ids: _NodeIdFactory) -> ExplainTreeNode:
    return ExplainTreeNode(
        id=ids.next_id(),
        node_type="operation",
        label=label,
        scan_category="operation",
        children=children,
    )


def _parse_json_block(block: Any, ids: _NodeIdFactory) -> ExplainTreeNode | None:
    if not isinstance(block, dict):
        return None
    if "table" in block:
        return _build_table_node(block["table"], ids)

    operation_map = {
        "nested_loop": "Nested Loop",
        "hash_join": "Hash Join",
        "block_nested_loop": "Block Nested Loop",
        "grouping_operation": "Grouping",
        "ordering_operation": "Ordering",
        "duplicates_removal": "Duplicates Removal",
        "buffer_result": "Buffer Result",
        "materialize": "Materialize",
    }
    for key, label in operation_map.items():
        if key not in block:
            continue
        payload = block[key]
        child_blocks = payload if isinstance(payload, list) else [payload]
        children: list[ExplainTreeNode] = []
        for child_block in child_blocks:
            if key in {"grouping_operation", "ordering_operation", "duplicates_removal", "buffer_result", "materialize"}:
                if isinstance(child_block, dict):
                    nested = _parse_json_block(child_block, ids)
                    if nested:
                        children.append(nested)
            else:
                nested = _parse_json_block(child_block, ids)
                if nested:
                    children.append(nested)
        return _build_operation_node(label, children, ids)

    if "query_block" in block:
        return _parse_json_block(block["query_block"], ids)
    return None


def _collect_table_nodes(node: ExplainTreeNode | None) -> list[ExplainTreeNode]:
    if node is None:
        return []
    if node.node_type == "table":
        return [node]
    collected: list[ExplainTreeNode] = []
    for child in node.children:
        collected.extend(_collect_table_nodes(child))
    return collected


def _count_joins(node: ExplainTreeNode | None) -> int:
    if node is None:
        return 0
    joins = 0
    if node.node_type == "operation" and node.label == "Nested Loop":
        joins += max(len(node.children) - 1, 0)
    for child in node.children:
        joins += _count_joins(child)
    return joins


def _extract_estimated_cost(explain_data: dict[str, Any]) -> float | None:
    query_block = explain_data.get("query_block", explain_data)
    if not isinstance(query_block, dict):
        return None
    cost_info = query_block.get("cost_info")
    if isinstance(cost_info, dict) and cost_info.get("query_cost") is not None:
        try:
            return float(cost_info["query_cost"])
        except (TypeError, ValueError):
            return None
    return None


def _build_summary(table_nodes: list[ExplainTreeNode], tree: ExplainTreeNode, explain_data: dict[str, Any] | None) -> ExplainSummary:
    summary = ExplainSummary(total_tables=len(table_nodes))
    for node in table_nodes:
        if node.scan_category == "table_scan":
            summary.table_scans += 1
        elif node.scan_category == "full_index_scan":
            summary.full_index_scans += 1
        elif node.scan_category == "index_seek":
            summary.index_seeks += 1
        else:
            summary.other_access += 1
        if node.rows is not None:
            try:
                summary.estimated_rows += int(node.rows)
            except (TypeError, ValueError):
                pass
    summary.join_count = max(_count_joins(tree), max(summary.total_tables - 1, 0))
    if explain_data is not None:
        summary.estimated_cost = _extract_estimated_cost(explain_data)
    return summary


def _detect_issues(table_nodes: list[ExplainTreeNode], tree: ExplainTreeNode) -> list[PerformanceIssue]:
    issues: list[PerformanceIssue] = []
    for node in table_nodes:
        access = (node.access_type or "").upper()
        extra = (node.extra or "").lower()
        table_name = node.label
        if access == "ALL":
            issues.append(PerformanceIssue(
                severity="high", category="full_table_scan",
                message=f"Full table scan on '{table_name}' (type ALL). Consider adding an index.",
                table=table_name,
            ))
        if node.possible_keys and not node.key and access in {"ALL", "INDEX", "RANGE"}:
            issues.append(PerformanceIssue(
                severity="medium", category="missing_index",
                message=f"Possible keys ({node.possible_keys}) exist for '{table_name}' but none were used.",
                table=table_name,
            ))
        if "using filesort" in extra:
            issues.append(PerformanceIssue(
                severity="medium", category="filesort",
                message=f"Filesort detected for '{table_name}'.", table=table_name,
            ))
        if "using temporary" in extra:
            issues.append(PerformanceIssue(
                severity="medium", category="temporary_table",
                message=f"Temporary table usage detected for '{table_name}'.", table=table_name,
            ))

    def walk_operations(node: ExplainTreeNode) -> None:
        if node.node_type == "operation" and node.label == "Nested Loop":
            issues.append(PerformanceIssue(
                severity="low", category="nested_loop_join",
                message="Nested loop join detected. May be slow on large result sets.",
            ))
        for child in node.children:
            walk_operations(child)

    walk_operations(tree)
    return issues


def _serialize_table_nodes(table_nodes: list[ExplainTreeNode]) -> list[dict[str, Any]]:
    return [
        {
            "id": node.id,
            "label": node.label,
            "access_type": node.access_type,
            "key": node.key,
            "possible_keys": node.possible_keys,
            "rows": node.rows,
            "filtered": node.filtered,
            "extra": node.extra,
            "scan_category": node.scan_category,
        }
        for node in table_nodes
    ]


def parse_explain_json(explain_data: dict[str, Any]) -> dict[str, Any]:
    ids = _NodeIdFactory()
    tree = _parse_json_block(explain_data, ids) or _build_operation_node("Query", [], ids)
    table_nodes = _collect_table_nodes(tree)
    summary = _build_summary(table_nodes, tree, explain_data)
    issues = _detect_issues(table_nodes, tree)
    return {
        "tree": tree.to_dict(),
        "table_nodes": _serialize_table_nodes(table_nodes),
        "summary": summary.to_dict(),
        "issues": [issue.to_dict() for issue in issues],
    }


def parse_explain_tabular(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ids = _NodeIdFactory()
    table_nodes: list[ExplainTreeNode] = []
    for row in rows:
        if not row.get("table"):
            continue
        table_nodes.append(_build_table_node({
            "table": row.get("table"),
            "type": row.get("type"),
            "possible_keys": row.get("possible_keys"),
            "key": row.get("key"),
            "rows": row.get("rows"),
            "filtered": row.get("filtered"),
            "Extra": row.get("Extra") or row.get("extra"),
        }, ids))
    tree = _build_operation_node("Query", table_nodes, ids)
    summary = _build_summary(table_nodes, tree, None)
    issues = _detect_issues(table_nodes, tree)
    return {
        "tree": tree.to_dict(),
        "table_nodes": _serialize_table_nodes(table_nodes),
        "summary": summary.to_dict(),
        "issues": [issue.to_dict() for issue in issues],
    }
