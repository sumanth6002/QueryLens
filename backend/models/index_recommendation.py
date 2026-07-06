from database.connection import db
from models.base import BaseModel


class IndexRecommendation(BaseModel):
    """Stored index advisor output for a workspace query."""

    __tablename__ = "index_recommendations"

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
    sql_text = db.Column(db.Text, nullable=False)
    parsed_query = db.Column(db.JSON, nullable=False, default=dict)
    recommendation_data = db.Column(db.JSON, nullable=False, default=dict)

    workspace = db.relationship("Workspace", back_populates="index_recommendations")
    user = db.relationship("User", back_populates="index_recommendations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "sql_text": self.sql_text,
            "parsed_query": self.parsed_query,
            "recommendation_data": self.recommendation_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
