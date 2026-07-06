"""Test MySQL connectivity for EXPLAIN / workspace execution."""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv

from config import BACKEND_DIR

load_dotenv(os.path.join(BACKEND_DIR, ".env"))


def main() -> int:
    from explain.database import get_connection_manager

    manager = get_connection_manager()
    if not manager.is_configured:
        print(json.dumps({"status": "error", "message": "Set MYSQL_* in backend/.env"}, indent=2))
        return 1

    result = manager.test_connection()
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
