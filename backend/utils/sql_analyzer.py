import re

import sqlparse

from utils.exceptions import ValidationError

SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "CROSS", "ON",
    "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "ASC", "DESC", "AND", "OR", "NOT",
    "IN", "IS", "NULL", "LIKE", "BETWEEN", "AS", "DISTINCT", "UNION", "ALL",
}

COLUMN_REFERENCE_PATTERN = re.compile(
    r"(?:`?([A-Za-z_][A-Za-z0-9_]*)`?\.)?`?([A-Za-z_][A-Za-z0-9_]*)`?"
)


def normalize_sql(sql: str) -> str:
    formatted = sqlparse.format(
        sql,
        strip_comments=True,
        reindent=False,
        keyword_case="upper",
    )
    return re.sub(r"\s+", " ", formatted).strip()


def _extract_clause(sql: str, start_keyword: str, stop_keywords: list[str]) -> str | None:
    stop_pattern = "|".join(rf"\b{keyword}\b" for keyword in stop_keywords)
    pattern = rf"\b{start_keyword}\b\s+(.+?)(?={stop_pattern}|$)"
    match = re.search(pattern, sql, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _build_alias_map(sql: str) -> dict[str, str]:
    alias_map: dict[str, str] = {}

    from_pattern = re.compile(
        r"\bFROM\s+`?([A-Za-z_][A-Za-z0-9_]*)`?(?:\s+(?:AS\s+)?`?([A-Za-z_][A-Za-z0-9_]*)`?)?",
        re.IGNORECASE,
    )
    join_pattern = re.compile(
        r"\b(?:INNER|LEFT|RIGHT|CROSS)?\s*JOIN\s+`?([A-Za-z_][A-Za-z0-9_]*)`?"
        r"(?:\s+(?:AS\s+)?`?([A-Za-z_][A-Za-z0-9_]*)`?)?",
        re.IGNORECASE,
    )

    from_match = from_pattern.search(sql)
    if from_match:
        table, alias = from_match.group(1), from_match.group(2) or from_match.group(1)
        alias_map[alias.lower()] = table
        alias_map[table.lower()] = table

    for table, alias in join_pattern.findall(sql):
        resolved_alias = alias or table
        alias_map[resolved_alias.lower()] = table
        alias_map[table.lower()] = table

    return alias_map


def _resolve_column(table_or_alias: str | None, column: str, alias_map: dict[str, str]) -> dict:
    if table_or_alias:
        table = alias_map.get(table_or_alias.lower(), table_or_alias)
        return {"table": table, "column": column, "reference": f"{table_or_alias}.{column}"}

    return {"table": None, "column": column, "reference": column}


def _strip_string_literals(expression: str) -> str:
    return re.sub(r"'[^']*'", "''", expression)


def _extract_columns(expression: str, alias_map: dict[str, str]) -> list[dict]:
    columns = []
    seen = set()
    cleaned_expression = _strip_string_literals(expression)

    for match in COLUMN_REFERENCE_PATTERN.finditer(cleaned_expression):
        table_or_alias = match.group(1)
        column = match.group(2)

        if column.upper() in SQL_KEYWORDS:
            continue

        resolved = _resolve_column(table_or_alias or None, column, alias_map)
        key = (resolved.get("table"), resolved["column"])
        if key in seen:
            continue
        seen.add(key)
        columns.append(resolved)

    return columns


def _extract_join_clauses(sql: str) -> list[dict]:
    join_pattern = re.compile(
        r"\b(?:INNER|LEFT|RIGHT|CROSS)?\s*JOIN\s+`?([A-Za-z_][A-Za-z0-9_]*)`?"
        r"(?:\s+(?:AS\s+)?`?([A-Za-z_][A-Za-z0-9_]*)`?)?\s+ON\s+(.+?)"
        r"(?=\b(?:INNER|LEFT|RIGHT|CROSS)?\s*JOIN\b|\bWHERE\b|\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|$)",
        re.IGNORECASE,
    )

    joins = []
    for table, alias, condition in join_pattern.findall(sql):
        joins.append({
            "table": table,
            "alias": alias or table,
            "condition": condition.strip(),
        })

    return joins


def parse_select_query(sql: str) -> dict:
    normalized = normalize_sql(sql)
    alias_map = _build_alias_map(normalized)

    where_clause = _extract_clause(normalized, "WHERE", ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"])
    group_clause = _extract_clause(normalized, "GROUP BY", ["ORDER BY", "LIMIT", "HAVING"])
    order_clause = _extract_clause(normalized, "ORDER BY", ["LIMIT", "HAVING"])

    joins = _extract_join_clauses(normalized)

    return {
        "normalized_sql": normalized,
        "tables": sorted(set(alias_map.values())),
        "aliases": alias_map,
        "where": {
            "clause": where_clause,
            "columns": _extract_columns(where_clause, alias_map) if where_clause else [],
        },
        "joins": [
            {
                **join,
                "columns": _extract_columns(join["condition"], alias_map),
            }
            for join in joins
        ],
        "group_by": {
            "clause": group_clause,
            "columns": _extract_columns(group_clause, alias_map) if group_clause else [],
        },
        "order_by": {
            "clause": order_clause,
            "columns": _extract_columns(order_clause, alias_map) if order_clause else [],
        },
    }


def validate_index_advisor_query(sql: str) -> str:
    cleaned = (sql or "").strip()
    if not cleaned:
        raise ValidationError("SQL query is required.")

    normalized = normalize_sql(cleaned)
    if not normalized.upper().startswith("SELECT"):
        raise ValidationError("Index advisor supports SELECT queries only.")

    return cleaned
