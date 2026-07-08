import os
from datetime import timedelta
from urllib.parse import quote_plus

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_database_uri() -> str:
    """Resolve database URI from env, using SQLite only in development."""
    explicit = os.environ.get("DATABASE_URL")
    if explicit:
        return explicit

    if os.environ.get("FLASK_ENV", "development") == "development":
        instance_dir = os.path.join(BACKEND_DIR, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, "querylens.db").replace("\\", "/")
        return f"sqlite:///{db_path}"

    mysql_host = os.environ.get("MYSQL_HOST", "").strip()
    mysql_user = os.environ.get("MYSQL_USER", "").strip()
    mysql_password = os.environ.get("MYSQL_PASSWORD", "")
    mysql_database = os.environ.get("MYSQL_DATABASE", "").strip()
    mysql_port = os.environ.get("MYSQL_PORT", "3306").strip() or "3306"

    if all((mysql_host, mysql_user, mysql_database)):
        return (
            f"mysql+pymysql://{quote_plus(mysql_user)}:{quote_plus(mysql_password)}"
            f"@{mysql_host}:{mysql_port}/{quote_plus(mysql_database)}"
        )

    raise ValueError(
        "Production database is not configured. Set DATABASE_URL or MYSQL_HOST, "
        "MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE."
    )


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
        has_database_url = bool(os.environ.get("DATABASE_URL"))
        has_mysql_parts = all(
            os.environ.get(key) for key in ("MYSQL_HOST", "MYSQL_USER", "MYSQL_DATABASE")
        )
        missing = ["SECRET_KEY"] if not os.environ.get("SECRET_KEY") else []

        if not has_database_url and not has_mysql_parts:
            missing.append("DATABASE_URL or MYSQL_HOST+MYSQL_USER+MYSQL_PASSWORD+MYSQL_DATABASE")

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
