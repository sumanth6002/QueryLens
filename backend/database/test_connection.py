"""
Standalone script to verify MySQL connectivity.

Usage (from backend/):
    python -m database.test_connection
"""

import json
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    from config import resolve_database_uri
    from database.utils import test_connection

    database_url = resolve_database_uri()

    result = test_connection(database_url)
    print(json.dumps(result, indent=2))

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
