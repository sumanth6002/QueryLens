"""Temporary request context used while authentication is disabled."""

from sqlalchemy.exc import IntegrityError

from database.connection import db
from models.user import User
from utils.password_utils import hash_password

GUEST_EMAIL = "guest@querylens.local"
GUEST_USERNAME = "guest"


def get_request_user() -> User:
    """Return a default guest user for development without login."""
    user = User.query.filter_by(username=GUEST_USERNAME).first()
    if user is not None:
        return user

    user = User(
        email=GUEST_EMAIL,
        username=GUEST_USERNAME,
        password_hash=hash_password("guest"),
    )
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        user = User.query.filter_by(username=GUEST_USERNAME).first()
        if user is None:
            raise

    return user
