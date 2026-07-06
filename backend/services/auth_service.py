from database.connection import db
from models.user import User
from utils.exceptions import AuthenticationError, ConflictError, NotFoundError
from utils.jwt_utils import create_access_token
from utils.password_utils import hash_password, verify_password
from utils.validators import validate_login, validate_registration


class AuthService:
    """Handles user registration, login, and session token issuance."""

    def register(self, email: str, username: str, password: str) -> dict:
        validate_registration(email, username, password)

        email = email.strip().lower()
        username = username.strip()

        if User.query.filter_by(email=email).first():
            raise ConflictError("An account with this email already exists.")

        if User.query.filter_by(username=username).first():
            raise ConflictError("This username is already taken.")

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.commit()

        return self._build_auth_response(user)

    def login(self, email: str, password: str) -> dict:
        validate_login(email, password)

        user = User.query.filter_by(email=email.strip().lower()).first()
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")

        return self._build_auth_response(user)

    def get_user_by_id(self, user_id: int) -> User:
        user = db.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    def _build_auth_response(self, user: User) -> dict:
        token = create_access_token(user.id, user.email)
        return {
            "user": user.to_dict(),
            "access_token": token,
            "token_type": "Bearer",
        }
