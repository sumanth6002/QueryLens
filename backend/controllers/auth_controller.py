from flask import g, jsonify, request

from services.auth_service import AuthService


class AuthController:
    def __init__(self):
        self.auth_service = AuthService()

    def register(self):
        data = request.get_json(silent=True) or {}
        result = self.auth_service.register(
            email=data.get("email", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
        )
        return jsonify(result), 201

    def login(self):
        data = request.get_json(silent=True) or {}
        result = self.auth_service.login(
            email=data.get("email", ""),
            password=data.get("password", ""),
        )
        return jsonify(result), 200

    def logout(self):
        return jsonify({"message": "Logged out successfully."}), 200

    def me(self):
        return jsonify({"user": g.current_user.to_dict()}), 200
