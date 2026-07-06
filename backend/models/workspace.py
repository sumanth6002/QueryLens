from database.connection import db
from models.base import BaseModel


class Workspace(BaseModel):
    """A user-owned sandbox for schemas, queries, and analysis."""

    __tablename__ = "workspaces"

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner = db.relationship("User", back_populates="workspaces")
    schema_snapshot = db.relationship(
        "SchemaSnapshot",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
    )
    queries = db.relationship(
        "Query",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    query_runs = db.relationship(
        "QueryRun",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    functional_dependency_sets = db.relationship(
        "FunctionalDependencySet",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    normalization_reports = db.relationship(
        "NormalizationReport",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    index_recommendations = db.relationship(
        "IndexRecommendation",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Workspace id={self.id} name={self.name!r} user_id={self.user_id}>"
