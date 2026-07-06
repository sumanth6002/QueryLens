from datetime import datetime, timezone

from database.connection import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BaseModel(db.Model):
    """Abstract base with integer primary key and timestamps."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    def to_dict(self) -> dict:
        raise NotImplementedError
