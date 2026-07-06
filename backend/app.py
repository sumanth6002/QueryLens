import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from config import config_by_name
from database.connection import db
from middleware.error_handlers import register_error_handlers
from routes import register_blueprints

load_dotenv()

import models  # noqa: E402, F401 — register ORM models with SQLAlchemy metadata


def create_app(config_name: str | None = None) -> Flask:
    """Application factory — creates and configures the Flask app."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    config_class = config_by_name[config_name]
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    db.init_app(app)

    if config_name == "development":
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    register_blueprints(app)
    register_error_handlers(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
