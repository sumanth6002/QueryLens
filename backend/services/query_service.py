from database.connection import db
from models.query import Query
from models.query_run import QueryRun
from models.user import User
from services.access_helpers import get_owned_workspace
from services.sql_execution_service import execute_sql as run_sql
from utils.exceptions import NotFoundError, ValidationError


class QueryService:
    """Saved queries and execution history for a workspace."""

    def list_saved_queries(self, user: User, workspace_id: int) -> list[Query]:
        workspace = get_owned_workspace(user, workspace_id)
        return workspace.queries.order_by(Query.updated_at.desc()).all()

    def get_saved_query(self, user: User, workspace_id: int, query_id: int) -> Query:
        return self._get_owned_query(user, workspace_id, query_id)

    def save_query(self, user: User, workspace_id: int, title: str, sql_text: str) -> Query:
        workspace = get_owned_workspace(user, workspace_id)
        query = self._create_query_record(workspace, title, sql_text)
        db.session.commit()
        return query

    def delete_saved_query(self, user: User, workspace_id: int, query_id: int) -> None:
        query = self._get_owned_query(user, workspace_id, query_id)
        db.session.delete(query)
        db.session.commit()

    def list_history(self, user: User, workspace_id: int, limit: int = 50) -> list[QueryRun]:
        workspace = get_owned_workspace(user, workspace_id)
        return (
            workspace.query_runs
            .order_by(QueryRun.created_at.desc())
            .limit(limit)
            .all()
        )

    def execute_sql(
        self,
        user: User,
        workspace_id: int,
        sql_text: str,
        *,
        query_id: int | None = None,
        save_query: bool = False,
        title: str | None = None,
    ) -> dict:
        workspace = get_owned_workspace(user, workspace_id)
        cleaned_sql = (sql_text or "").strip()

        if query_id is not None:
            saved_query = self._get_owned_query(user, workspace_id, query_id)
            cleaned_sql = saved_query.sql_text

        execution = run_sql(workspace.id, cleaned_sql)

        saved_query_id = query_id
        if save_query and title:
            saved_query = self._create_query_record(workspace, title, cleaned_sql)
            saved_query_id = saved_query.id

        query_run = QueryRun(
            workspace_id=workspace.id,
            user_id=user.id,
            query_id=saved_query_id,
            sql_text=cleaned_sql,
            status=execution["status"],
            execution_time_ms=execution["execution_time_ms"],
            row_count=execution.get("row_count"),
            result_columns=execution.get("result_columns"),
            result_preview=execution.get("result_preview"),
            error_message=execution.get("error_message"),
        )
        db.session.add(query_run)
        db.session.commit()

        return {
            "run": query_run.to_dict(),
            "execution": execution,
        }

    def _create_query_record(self, workspace, title: str, sql_text: str) -> Query:
        cleaned_title = (title or "").strip()
        cleaned_sql = (sql_text or "").strip()

        if not cleaned_title:
            raise ValidationError("Query title is required.")

        if not cleaned_sql:
            raise ValidationError("SQL text is required.")

        query = Query(
            workspace_id=workspace.id,
            title=cleaned_title,
            sql_text=cleaned_sql,
        )
        db.session.add(query)
        db.session.flush()
        return query

    def _get_owned_query(self, user: User, workspace_id: int, query_id: int) -> Query:
        get_owned_workspace(user, workspace_id)
        query = db.session.get(Query, query_id)

        if query is None or query.workspace_id != workspace_id:
            raise NotFoundError("Query not found.")

        return query
