from database.connection import db
from models.base import BaseModel


class SchemaSnapshot(BaseModel):
    """Stores the current logical schema design for a workspace."""

    __tablename__ = "schema_snapshots"

    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    schema_data = db.Column(db.JSON, nullable=False, default=lambda: {"tables": []})
    version = db.Column(db.Integer, nullable=False, default=1)

    workspace = db.relationship("Workspace", back_populates="schema_snapshot")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "schema_data": self.schema_data,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<SchemaSnapshot workspace_id={self.workspace_id} version={self.version}>"
