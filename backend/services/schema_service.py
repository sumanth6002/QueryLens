from copy import deepcopy

from database.connection import db
from models.schema_snapshot import SchemaSnapshot
from models.user import User
from services.access_helpers import get_owned_workspace
from services.er_diagram_service import build_er_diagram
from services.schema_execution_service import execute_schema as run_create_table_statements
from services.schema_sql_generator import build_schema_sql, build_table_sql
from utils.exceptions import ConflictError, NotFoundError
from utils.schema_validators import (
    empty_schema,
    find_table,
    validate_table_payload,
)


class SchemaService:
    """Manage logical schema designs and CREATE TABLE execution per workspace."""

    def get_schema(self, user: User, workspace_id: int) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        return snapshot.to_dict()

    def create_table(self, user: User, workspace_id: int, payload: dict) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        schema_data = deepcopy(snapshot.schema_data or empty_schema())
        existing_names = {table["name"] for table in schema_data.get("tables", [])}

        table = validate_table_payload(payload, existing_table_names=existing_names)
        schema_data.setdefault("tables", []).append(table)

        return self._save_snapshot(snapshot, schema_data)

    def update_table(
        self,
        user: User,
        workspace_id: int,
        table_name: str,
        payload: dict,
    ) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        schema_data = deepcopy(snapshot.schema_data or empty_schema())
        table = find_table(schema_data, table_name)
        existing_names = {name for name in (t["name"] for t in schema_data.get("tables", []))}

        merged = {
            "name": table_name,
            "columns": payload.get("columns", table.get("columns", [])),
            "primary_key": payload.get("primary_key", table.get("primary_key", [])),
            "foreign_keys": payload.get("foreign_keys", table.get("foreign_keys", [])),
        }

        validated = validate_table_payload(
            merged,
            existing_table_names=existing_names - {table_name},
            current_name=table_name,
        )

        tables = []
        for current in schema_data.get("tables", []):
            if current["name"] == table_name:
                tables.append(validated)
            else:
                tables.append(current)

        schema_data["tables"] = tables
        return self._save_snapshot(snapshot, schema_data)

    def delete_table(self, user: User, workspace_id: int, table_name: str) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        schema_data = deepcopy(snapshot.schema_data or empty_schema())

        tables = schema_data.get("tables", [])
        filtered = [table for table in tables if table["name"] != table_name]

        if len(filtered) == len(tables):
            raise NotFoundError(f"Table '{table_name}' not found.")

        for table in filtered:
            for foreign_key in table.get("foreign_keys", []):
                if foreign_key["referenced_table"] == table_name:
                    raise ConflictError(
                        f"Cannot delete '{table_name}' because it is referenced by "
                        f"'{table['name']}'."
                    )

        schema_data["tables"] = filtered
        return self._save_snapshot(snapshot, schema_data)

    def preview_sql(
        self,
        user: User,
        workspace_id: int,
        table_name: str | None = None,
    ) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        schema_data = snapshot.schema_data or empty_schema()

        if not schema_data.get("tables"):
            return {"statements": []}

        if table_name:
            statements = [build_table_sql(schema_data, table_name)]
        else:
            statements = build_schema_sql(schema_data)

        return {"statements": statements}

    def execute_schema(
        self,
        user: User,
        workspace_id: int,
        table_name: str | None = None,
    ) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        schema_data = snapshot.schema_data or empty_schema()

        if not schema_data.get("tables"):
            raise NotFoundError("No tables defined in this workspace schema.")

        get_owned_workspace(user, workspace_id)
        return run_create_table_statements(workspace_id, schema_data, table_name)

    def get_er_diagram(self, user: User, workspace_id: int) -> dict:
        snapshot = self._get_or_create_snapshot(user, workspace_id)
        return build_er_diagram(snapshot.schema_data)

    def _get_or_create_snapshot(self, user: User, workspace_id: int) -> SchemaSnapshot:
        workspace = get_owned_workspace(user, workspace_id)
        snapshot = workspace.schema_snapshot

        if snapshot is None:
            snapshot = SchemaSnapshot(
                workspace_id=workspace.id,
                schema_data=empty_schema(),
                version=1,
            )
            db.session.add(snapshot)
            db.session.commit()

        return snapshot

    def _save_snapshot(self, snapshot: SchemaSnapshot, schema_data: dict) -> dict:
        snapshot.schema_data = schema_data
        snapshot.version += 1
        db.session.commit()
        return snapshot.to_dict()
