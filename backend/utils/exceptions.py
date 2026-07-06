class AppError(Exception):
    """Base application error with HTTP status code."""

    status_code = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationError(AppError):
    status_code = 400


class AuthenticationError(AppError):
    status_code = 401


class ConflictError(AppError):
    status_code = 409


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403
