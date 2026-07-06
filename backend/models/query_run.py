from database.connection import db
from models.base import BaseModel


class QueryRun(BaseModel):
    """Execution history for SQL run in a workspace sandbox."""

    __tablename__ = "query_runs"

    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_id = db.Column(
        db.Integer,
        db.ForeignKey("queries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sql_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    execution_time_ms = db.Column(db.Float, nullable=False, default=0.0)
    row_count = db.Column(db.Integer, nullable=True)
    result_columns = db.Column(db.JSON, nullable=True)
    result_preview = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    workspace = db.relationship("Workspace", back_populates="query_runs")
    user = db.relationship("User", back_populates="query_runs")
    query = db.relationship("Query", back_populates="runs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "query_id": self.query_id,
            "sql_text": self.sql_text,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "result_columns": self.result_columns,
            "result_preview": self.result_preview,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<QueryRun id={self.id} status={self.status!r}>"
