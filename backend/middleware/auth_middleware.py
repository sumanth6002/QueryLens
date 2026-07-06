from functools import wraps

import jwt
from flask import g, jsonify, request

from services.auth_service import AuthService
from utils.exceptions import AuthenticationError, NotFoundError


def token_required(fn):
    """Decorator that validates a Bearer JWT and attaches the user to `g.current_user`."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized", "message": "Missing or invalid token."}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Unauthorized", "message": "Missing or invalid token."}), 401

        try:
            from utils.jwt_utils import decode_access_token

            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("Invalid token payload.")

            g.current_user = AuthService().get_user_by_id(int(user_id))
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Unauthorized", "message": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Unauthorized", "message": "Invalid token."}), 401
        except AuthenticationError as exc:
            return jsonify({"error": "Unauthorized", "message": exc.message}), 401
        except NotFoundError:
            return jsonify({"error": "Unauthorized", "message": "User no longer exists."}), 401

        return fn(*args, **kwargs)

    return wrapper
