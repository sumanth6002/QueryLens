import re

from utils.exceptions import ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,100}$")


def validate_registration(email: str, username: str, password: str) -> None:
    if not email or not EMAIL_PATTERN.match(email):
        raise ValidationError("A valid email address is required.")

    if not username or not USERNAME_PATTERN.match(username):
        raise ValidationError(
            "Username must be 3–100 characters and contain only letters, numbers, or underscores."
        )

    if not password or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")


def validate_login(email: str, password: str) -> None:
    if not email or not password:
        raise ValidationError("Email and password are required.")


def validate_workspace_name(name: str) -> str:
    cleaned = (name or "").strip()

    if not cleaned:
        raise ValidationError("Workspace name is required.")

    if len(cleaned) > 150:
        raise ValidationError("Workspace name must be 150 characters or fewer.")

    return cleaned
