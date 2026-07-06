from database.connection import db
from models.base import BaseModel


class NormalizationReport(BaseModel):
    """Stored normalization analysis output for a workspace."""

    __tablename__ = "normalization_reports"

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
    dependency_set_id = db.Column(
        db.Integer,
        db.ForeignKey("functional_dependencies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    attributes = db.Column(db.JSON, nullable=False, default=list)
    functional_dependencies = db.Column(db.JSON, nullable=False, default=list)
    report_data = db.Column(db.JSON, nullable=False, default=dict)

    workspace = db.relationship("Workspace", back_populates="normalization_reports")
    user = db.relationship("User", back_populates="normalization_reports")
    dependency_set = db.relationship("FunctionalDependencySet", back_populates="reports")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "dependency_set_id": self.dependency_set_id,
            "attributes": self.attributes,
            "functional_dependencies": self.functional_dependencies,
            "report_data": self.report_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
