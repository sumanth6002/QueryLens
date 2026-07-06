from database.connection import db
from models.base import BaseModel


class FunctionalDependencySet(BaseModel):
    """Reusable attribute and functional dependency definitions for a workspace."""

    __tablename__ = "functional_dependencies"

    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    attributes = db.Column(db.JSON, nullable=False, default=list)
    dependencies = db.Column(db.JSON, nullable=False, default=list)

    workspace = db.relationship("Workspace", back_populates="functional_dependency_sets")
    reports = db.relationship(
        "NormalizationReport",
        back_populates="dependency_set",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "attributes": self.attributes,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
