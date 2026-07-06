"""Data models for EXPLAIN analysis API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExplainTreeNode:
    id: str
    label: str
    node_type: str
    scan_category: str
    access_type: str | None = None
    key: str | None = None
    possible_keys: str | None = None
    rows: int | float | None = None
    filtered: float | None = None
    extra: str | None = None
    children: list[ExplainTreeNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "label": self.label,
            "access_type": self.access_type,
            "key": self.key,
            "possible_keys": self.possible_keys,
            "rows": self.rows,
            "filtered": self.filtered,
            "extra": self.extra,
            "scan_category": self.scan_category,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class ExplainSummary:
    table_scans: int = 0
    full_index_scans: int = 0
    index_seeks: int = 0
    other_access: int = 0
    total_tables: int = 0
    join_count: int = 0
    estimated_rows: int = 0
    estimated_cost: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "table_scans": self.table_scans,
            "full_index_scans": self.full_index_scans,
            "index_seeks": self.index_seeks,
            "other_access": self.other_access,
            "total_tables": self.total_tables,
            "join_count": self.join_count,
            "estimated_rows": self.estimated_rows,
        }
        if self.estimated_cost is not None:
            payload["estimated_cost"] = self.estimated_cost
        return payload


@dataclass
class PerformanceIssue:
    severity: str
    category: str
    message: str
    table: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "table": self.table,
        }


@dataclass
class ExplainResult:
    executed: bool
    status: str
    query: str
    database: str
    execution_time_ms: float
    explain_format: str
    tree: dict[str, Any] | None = None
    table_nodes: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] | None = None
    issues: list[dict[str, Any]] = field(default_factory=list)
    explain_json: dict[str, Any] | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "executed": self.executed,
            "status": self.status,
            "message": self.message,
            "execution_time_ms": self.execution_time_ms,
            "query": self.query,
            "database": self.database,
            "explain_format": self.explain_format,
            "tree": self.tree,
            "table_nodes": self.table_nodes,
            "summary": self.summary,
            "issues": self.issues,
        }
        if self.explain_json is not None:
            payload["explain_json"] = self.explain_json
        return payload
