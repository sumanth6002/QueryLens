from database.connection import db
from models.index_recommendation import IndexRecommendation
from models.user import User
from models.workspace import Workspace
from services.access_helpers import get_owned_workspace
from services.index_recommendation_engine import generate_index_recommendations
from utils.exceptions import NotFoundError
from utils.sql_analyzer import parse_select_query, validate_index_advisor_query


class IndexAdvisorService:
    """Analyze SELECT queries and recommend indexes."""

    def analyze(self, user: User, workspace_id: int, sql: str, *, save: bool = False) -> dict:
        workspace = get_owned_workspace(user, workspace_id)
        cleaned_sql = validate_index_advisor_query(sql)
        parsed_query = parse_select_query(cleaned_sql)
        known_tables = self._known_tables(workspace)
        recommendation_data = generate_index_recommendations(parsed_query, known_tables)

        result = {
            "sql": cleaned_sql,
            "parsed_query": parsed_query,
            **recommendation_data,
        }

        if save:
            record = IndexRecommendation(
                workspace_id=workspace.id,
                user_id=user.id,
                sql_text=cleaned_sql,
                parsed_query=parsed_query,
                recommendation_data=recommendation_data,
            )
            db.session.add(record)
            db.session.commit()
            result["recommendation_id"] = record.id

        return result

    def list_recommendations(self, user: User, workspace_id: int, limit: int = 20) -> list:
        workspace = get_owned_workspace(user, workspace_id)
        return (
            workspace.index_recommendations
            .order_by(IndexRecommendation.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recommendation(self, user: User, workspace_id: int, recommendation_id: int):
        get_owned_workspace(user, workspace_id)
        record = db.session.get(IndexRecommendation, recommendation_id)

        if record is None or record.workspace_id != workspace_id:
            raise NotFoundError("Index recommendation not found.")

        return record

    def _known_tables(self, workspace: Workspace) -> set[str]:
        snapshot = workspace.schema_snapshot
        if snapshot is None or not snapshot.schema_data:
            return set()

        return {
            table["name"]
            for table in snapshot.schema_data.get("tables", [])
        }
