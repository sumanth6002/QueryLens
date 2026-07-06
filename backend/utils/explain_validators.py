import re

from utils.exceptions import ValidationError
from utils.sql_safety import get_statement_type, parse_and_validate_sql

EXPLAIN_PREFIX = re.compile(r"^EXPLAIN\s+(?:FORMAT\s*=\s*\w+\s+)?", re.IGNORECASE)


def normalize_select_query(sql: str) -> str:
    cleaned = (sql or "").strip()

    if not cleaned:
        raise ValidationError("SQL query is required.")

    cleaned = EXPLAIN_PREFIX.sub("", cleaned).strip()
    statements = parse_and_validate_sql(cleaned)

    if len(statements) != 1:
        raise ValidationError("EXPLAIN supports exactly one SELECT statement.")

    statement = statements[0]
    statement_type = get_statement_type(statement)

    if statement_type != "SELECT":
        raise ValidationError("Only SELECT queries can be explained.")

    return statement
