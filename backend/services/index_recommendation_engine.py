from __future__ import annotations


def _index_name(table: str, columns: list[str]) -> str:
    suffix = "_".join(column.lower() for column in columns)
    return f"idx_{table.lower()}_{suffix}"[:64]


def _create_index_sql(table: str, columns: list[str]) -> str:
    column_sql = ", ".join(f"`{column}`" for column in columns)
    return f"CREATE INDEX `{_index_name(table, columns)}` ON `{table}` ({column_sql});"


def _group_columns_by_table(columns: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}

    for column in columns:
        table = column.get("table")
        if not table:
            continue

        grouped.setdefault(table, [])
        if column["column"] not in grouped[table]:
            grouped[table].append(column["column"])

    return grouped


def _recommendation_key(table: str, columns: list[str]) -> tuple:
    return (table, tuple(columns))


def _add_recommendation(
    recommendations: list[dict],
    seen: set[tuple],
    *,
    table: str,
    columns: list[str],
    clause: str,
    priority: str,
    explanation: str,
) -> None:
    if not table or not columns:
        return

    key = _recommendation_key(table, columns)
    if key in seen:
        for item in recommendations:
            if item["table"] == table and tuple(item["columns"]) == tuple(columns):
                if clause not in item.get("clauses", []):
                    item.setdefault("clauses", [item["clause"]])
                    item["clauses"].append(clause)
                    item["explanation"] += f" Also supports {clause}."
                priority_order = {"high": 0, "medium": 1, "low": 2}
                if priority_order[priority] < priority_order[item["priority"]]:
                    item["priority"] = priority
        return

    seen.add(key)
    recommendations.append({
        "table": table,
        "columns": columns,
        "clause": clause,
        "clauses": [clause],
        "priority": priority,
        "index_name": _index_name(table, columns),
        "sql": _create_index_sql(table, columns),
        "explanation": explanation,
    })


def generate_index_recommendations(parsed_query: dict, known_tables: set[str] | None = None) -> dict:
    recommendations: list[dict] = []
    seen: set[tuple] = set()
    known_tables = known_tables or set()

    def table_is_known(table: str) -> bool:
        return not known_tables or table in known_tables

    for table, columns in _group_columns_by_table(parsed_query["where"]["columns"]).items():
        if not table_is_known(table):
            continue

        if len(columns) == 1:
            _add_recommendation(
                recommendations,
                seen,
                table=table,
                columns=columns,
                clause="WHERE",
                priority="high",
                explanation=(
                    f"Column `{columns[0]}` appears in the WHERE clause. "
                    f"An index on `{table}({columns[0]})` can reduce rows examined during filtering."
                ),
            )
        else:
            _add_recommendation(
                recommendations,
                seen,
                table=table,
                columns=columns,
                clause="WHERE",
                priority="high",
                explanation=(
                    f"Multiple WHERE predicates reference {', '.join(columns)} on `{table}`. "
                    f"A composite index on ({', '.join(columns)}) supports combined filtering."
                ),
            )

    for join in parsed_query["joins"]:
        grouped = _group_columns_by_table(join["columns"])
        for table, columns in grouped.items():
            if not table_is_known(table):
                continue

            _add_recommendation(
                recommendations,
                seen,
                table=table,
                columns=columns,
                clause="JOIN",
                priority="high",
                explanation=(
                    f"`{table}` participates in a JOIN via ({', '.join(columns)}). "
                    f"Indexing the join column(s) speeds up nested-loop and hash join lookups."
                ),
            )

    for table, columns in _group_columns_by_table(parsed_query["group_by"]["columns"]).items():
        if not table_is_known(table):
            continue

        _add_recommendation(
            recommendations,
            seen,
            table=table,
            columns=columns,
            clause="GROUP BY",
            priority="medium",
            explanation=(
                f"GROUP BY uses {', '.join(columns)} on `{table}`. "
                f"An index on ({', '.join(columns)}) can avoid filesort during grouping."
            ),
        )

    for table, columns in _group_columns_by_table(parsed_query["order_by"]["columns"]).items():
        if not table_is_known(table):
            continue

        _add_recommendation(
            recommendations,
            seen,
            table=table,
            columns=columns,
            clause="ORDER BY",
            priority="medium",
            explanation=(
                f"ORDER BY references {', '.join(columns)} on `{table}`. "
                f"A matching index helps MySQL return sorted rows without an explicit sort step."
            ),
        )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda item: (priority_order[item["priority"]], item["table"], item["columns"]))

    return {
        "recommendations": recommendations,
        "summary": {
            "total": len(recommendations),
            "high_priority": sum(1 for item in recommendations if item["priority"] == "high"),
            "medium_priority": sum(1 for item in recommendations if item["priority"] == "medium"),
            "by_clause": {
                clause: sum(1 for item in recommendations if item["clause"] == clause)
                for clause in ["WHERE", "JOIN", "GROUP BY", "ORDER BY"]
            },
        },
    }
