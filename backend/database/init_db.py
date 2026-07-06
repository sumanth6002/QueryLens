"""
Initialize the QueryLens MySQL database and create tables.

Usage (from backend/):
    python -m database.init_db
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    from app import create_app
    from database.connection import db
    from database.utils import ensure_database_exists, test_connection
    import models  # noqa: F401 — register ORM models with SQLAlchemy

    from config import resolve_database_uri

    database_url = resolve_database_uri()

    if database_url.startswith("sqlite"):
        print(f"Using SQLite database: {database_url}")
    else:
        print("Ensuring database exists...")
        try:
            ensure_database_exists(database_url)
        except Exception as exc:
            print(f"Failed to create database: {exc}", file=sys.stderr)
            print(
                "Tip: set DATABASE_URL in backend/.env or unset it to use SQLite for development.",
                file=sys.stderr,
            )
            return 1

    print("Testing connection...")
    result = test_connection(database_url)
    if result["status"] != "ok":
        print(f"Connection failed: {result.get('message')}", file=sys.stderr)
        return 1

    if database_url.startswith("sqlite"):
        print(f"Connected to SQLite database at `{result['database']}`")
    else:
        print(f"Connected to `{result['database']}` (MySQL {result['mysql_version']})")

    app = create_app()
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Tables created successfully:")
        for table_name in sorted(db.metadata.tables.keys()):
            print(f"  - {table_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
