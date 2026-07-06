from flask import Blueprint

from controllers.auth_controller import AuthController
from middleware.auth_middleware import token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
controller = AuthController()


@auth_bp.route("/register", methods=["POST"])
def register():
    return controller.register()


@auth_bp.route("/login", methods=["POST"])
def login():
    return controller.login()


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    return controller.logout()


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    return controller.me()
