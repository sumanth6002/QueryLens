import re

import sqlparse

from utils.exceptions import ValidationError

MAX_STATEMENTS = 5
MAX_SQL_LENGTH = 10000

ALLOWED_STATEMENT_TYPES = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "SHOW", "DESCRIBE", "EXPLAIN",
}

BLOCKED_KEYWORDS = {
    "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE", "CALL",
    "EXEC", "EXECUTE", "LOAD", "REPLACE", "RENAME", "LOCK", "UNLOCK",
    "SET", "USE", "INTO OUTFILE", "INTO DUMPFILE",
}


def get_statement_type(statement: str) -> str:
    parsed = sqlparse.parse(statement)[0]
    statement_type = (parsed.get_type() or "UNKNOWN").upper()

    if statement_type != "UNKNOWN":
        return statement_type

    first_token = parsed.token_first(skip_cm=True)
    if first_token is None:
        return "UNKNOWN"

    return first_token.normalized.upper()


def _contains_blocked_keyword(statement: str) -> str | None:
    upper_statement = statement.upper()

    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", upper_statement):
            return keyword

    return None


def parse_and_validate_sql(sql: str) -> list[str]:
    cleaned = (sql or "").strip()

    if not cleaned:
        raise ValidationError("SQL cannot be empty.")

    if len(cleaned) > MAX_SQL_LENGTH:
        raise ValidationError(f"SQL must be {MAX_SQL_LENGTH} characters or fewer.")

    statements = [statement.strip() for statement in sqlparse.split(cleaned) if statement.strip()]

    if not statements:
        raise ValidationError("SQL cannot be empty.")

    if len(statements) > MAX_STATEMENTS:
        raise ValidationError(f"A maximum of {MAX_STATEMENTS} statements is allowed per request.")

    for statement in statements:
        blocked = _contains_blocked_keyword(statement)
        if blocked:
            raise ValidationError(f"Keyword '{blocked}' is not allowed in the SQL editor.")

        statement_type = get_statement_type(statement)
        if statement_type not in ALLOWED_STATEMENT_TYPES:
            raise ValidationError(
                f"Statement type '{statement_type}' is not allowed. "
                f"Allowed types: {', '.join(sorted(ALLOWED_STATEMENT_TYPES))}."
            )

    return statements
