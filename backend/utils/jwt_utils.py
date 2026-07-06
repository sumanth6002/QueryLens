from datetime import datetime, timezone

import jwt
from flask import current_app


def create_access_token(user_id: int, email: str) -> str:
    expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + expires,
    }

    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
    )
