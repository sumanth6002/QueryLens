import os
from datetime import timedelta

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_database_uri() -> str:
    """Use DATABASE_URL when set; otherwise SQLite in development."""
    explicit = os.environ.get("DATABASE_URL")
    if explicit:
        return explicit

    if os.environ.get("FLASK_ENV", "development") == "development":
        instance_dir = os.path.join(BACKEND_DIR, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, "querylens.db").replace("\\", "/")
        return f"sqlite:///{db_path}"

    return "mysql+pymysql://root:password@localhost:3306/querylens"


class Config:
    """Base configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    )

    SQLALCHEMY_DATABASE_URI = resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get("SQLALCHEMY_ECHO", "false").lower() == "true"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080",
        ).split(",")
        if origin.strip()
    ]

    SQL_MAX_RESULT_ROWS = int(os.environ.get("SQL_MAX_RESULT_ROWS", "500"))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app) -> None:
        missing = [
            key for key in ("SECRET_KEY", "DATABASE_URL")
            if not os.environ.get(key)
        ]
        if missing:
            raise ValueError(
                f"Production requires environment variables: {', '.join(missing)}"
            )

        if cls.SECRET_KEY == "dev-secret-change-in-production":
            raise ValueError("SECRET_KEY must be set to a unique value in production.")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:",
    )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
