from database.connection import db
from models.base import BaseModel


class Query(BaseModel):
    """A saved SQL query within a workspace."""

    __tablename__ = "queries"

    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(150), nullable=False)
    sql_text = db.Column(db.Text, nullable=False)

    workspace = db.relationship("Workspace", back_populates="queries")
    runs = db.relationship(
        "QueryRun",
        back_populates="query",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "sql_text": self.sql_text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Query id={self.id} title={self.title!r}>"
