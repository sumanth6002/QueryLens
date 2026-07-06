from database.connection import db
from models.base import BaseModel


class User(BaseModel):
    """Application user with hashed credentials for JWT authentication."""

    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    workspaces = db.relationship(
        "Workspace",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    query_runs = db.relationship(
        "QueryRun",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    normalization_reports = db.relationship(
        "NormalizationReport",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    index_recommendations = db.relationship(
        "IndexRecommendation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
