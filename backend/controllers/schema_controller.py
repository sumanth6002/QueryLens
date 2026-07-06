from flask import jsonify, request

from models.user import User
from services.schema_service import SchemaService


class SchemaController:
    def __init__(self):
        self.schema_service = SchemaService()

    def get_schema(self, user: User, workspace_id: int):
        result = self.schema_service.get_schema(user, workspace_id)
        return jsonify(result), 200

    def create_table(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        result = self.schema_service.create_table(user, workspace_id, data)
        return jsonify(result), 201

    def update_table(self, user: User, workspace_id: int, table_name: str):
        data = request.get_json(silent=True) or {}
        result = self.schema_service.update_table(user, workspace_id, table_name, data)
        return jsonify(result), 200

    def delete_table(self, user: User, workspace_id: int, table_name: str):
        result = self.schema_service.delete_table(user, workspace_id, table_name)
        return jsonify(result), 200

    def preview_sql(self, user: User, workspace_id: int):
        table_name = request.args.get("table")
        result = self.schema_service.preview_sql(user, workspace_id, table_name)
        return jsonify(result), 200

    def execute_schema(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        table_name = data.get("table")
        result = self.schema_service.execute_schema(user, workspace_id, table_name)
        return jsonify(result), 200

    def get_er_diagram(self, user: User, workspace_id: int):
        result = self.schema_service.get_er_diagram(user, workspace_id)
        return jsonify(result), 200
