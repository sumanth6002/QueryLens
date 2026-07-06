from __future__ import annotations

from copy import deepcopy
from typing import Any


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


def _next_id(counter: list[int]) -> str:
    counter[0] += 1
    return f"node-{counter[0]}"


def _build_table_node(table: dict[str, Any], counter: list[int]) -> dict[str, Any]:
    access_type = table.get("access_type")
    key = table.get("key")
    scan_category = classify_scan(access_type, key)

    return {
        "id": _next_id(counter),
        "node_type": "table",
        "label": table.get("table_name") or table.get("table") or "unknown_table",
        "access_type": access_type,
        "key": key,
        "possible_keys": table.get("possible_keys"),
        "rows": table.get("rows_examined_per_scan") or table.get("rows"),
        "filtered": table.get("filtered"),
        "extra": table.get("attached_condition") or table.get("message"),
        "scan_category": scan_category,
        "children": [],
    }


def _build_operation_node(label: str, children: list[dict[str, Any]], counter: list[int]) -> dict[str, Any]:
    return {
        "id": _next_id(counter),
        "node_type": "operation",
        "label": label,
        "access_type": None,
        "key": None,
        "possible_keys": None,
        "rows": None,
        "filtered": None,
        "extra": None,
        "scan_category": "operation",
        "children": children,
    }


def _parse_block(block: Any, counter: list[int]) -> dict[str, Any] | None:
    if not isinstance(block, dict):
        return None

    if "table" in block:
        return _build_table_node(block["table"], counter)

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
        children = []

        for child_block in child_blocks:
            if key in {"grouping_operation", "ordering_operation", "duplicates_removal", "buffer_result", "materialize"}:
                if isinstance(child_block, dict):
                    nested = _parse_block(child_block, counter)
                    if nested:
                        children.append(nested)
            else:
                nested = _parse_block(child_block, counter)
                if nested:
                    children.append(nested)

        return _build_operation_node(label, children, counter)

    if "query_block" in block:
        return _parse_block(block["query_block"], counter)

    return None


def _collect_table_nodes(node: dict[str, Any] | None) -> list[dict[str, Any]]:
    if node is None:
        return []

    if node.get("node_type") == "table":
        return [node]

    collected = []
    for child in node.get("children", []):
        collected.extend(_collect_table_nodes(child))

    return collected


def _build_summary(table_nodes: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "table_scans": 0,
        "full_index_scans": 0,
        "index_seeks": 0,
        "other_access": 0,
        "total_tables": len(table_nodes),
    }

    for node in table_nodes:
        category = node.get("scan_category")
        if category == "table_scan":
            summary["table_scans"] += 1
        elif category == "full_index_scan":
            summary["full_index_scans"] += 1
        elif category == "index_seek":
            summary["index_seeks"] += 1
        else:
            summary["other_access"] += 1

    return summary


def parse_explain_json(explain_data: dict[str, Any]) -> dict[str, Any]:
    counter = [0]
    tree = _parse_block(explain_data, counter)

    if tree is None:
        tree = _build_operation_node("Query", [], counter)

    table_nodes = _collect_table_nodes(tree)
    summary = _build_summary(table_nodes)

    return {
        "tree": tree,
        "table_nodes": [
            {
                "id": node["id"],
                "label": node["label"],
                "access_type": node["access_type"],
                "key": node["key"],
                "scan_category": node["scan_category"],
                "rows": node["rows"],
            }
            for node in table_nodes
        ],
        "summary": summary,
    }


SAMPLE_EXPLAIN_TREE = {
    "tree": {
        "id": "node-1",
        "node_type": "operation",
        "label": "Nested Loop",
        "access_type": None,
        "key": None,
        "possible_keys": None,
        "rows": None,
        "filtered": None,
        "extra": None,
        "scan_category": "operation",
        "children": [
            {
                "id": "node-2",
                "node_type": "table",
                "label": "orders",
                "access_type": "ALL",
                "key": None,
                "possible_keys": ["idx_orders_user_id"],
                "rows": 1200,
                "filtered": 100.0,
                "extra": "Using where",
                "scan_category": "table_scan",
                "children": [],
            },
            {
                "id": "node-3",
                "node_type": "table",
                "label": "users",
                "access_type": "eq_ref",
                "key": "PRIMARY",
                "possible_keys": ["PRIMARY"],
                "rows": 1,
                "filtered": 100.0,
                "extra": None,
                "scan_category": "index_seek",
                "children": [],
            },
        ],
    },
    "table_nodes": [
        {
            "id": "node-2",
            "label": "orders",
            "access_type": "ALL",
            "key": None,
            "scan_category": "table_scan",
            "rows": 1200,
        },
        {
            "id": "node-3",
            "label": "users",
            "access_type": "eq_ref",
            "key": "PRIMARY",
            "scan_category": "index_seek",
            "rows": 1,
        },
    ],
    "summary": {
        "table_scans": 1,
        "full_index_scans": 0,
        "index_seeks": 1,
        "other_access": 0,
        "total_tables": 2,
    },
}


def get_sample_explain_result() -> dict[str, Any]:
    return deepcopy(SAMPLE_EXPLAIN_TREE)
