from flask import jsonify, request

from models.user import User
from services.normalization_service import NormalizationService
from utils.request_helpers import clamp_limit


class NormalizationController:
    def __init__(self):
        self.normalization_service = NormalizationService()

    def analyze(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        result = self.normalization_service.analyze(
            user,
            workspace_id,
            data,
            save_report=bool(data.get("save_report", False)),
            save_fd_set=bool(data.get("save_fd_set", False)),
            fd_set_name=data.get("name"),
        )
        return jsonify(result), 200

    def list_reports(self, user: User, workspace_id: int):
        limit = clamp_limit(
            request.args.get("limit", default=20, type=int),
            default=20,
        )
        reports = self.normalization_service.list_reports(user, workspace_id, limit=limit)
        return jsonify({
            "reports": [report.to_dict() for report in reports],
            "total": len(reports),
        }), 200

    def get_report(self, user: User, workspace_id: int, report_id: int):
        report = self.normalization_service.get_report(user, workspace_id, report_id)
        return jsonify({"report": report.to_dict()}), 200

    def list_fd_sets(self, user: User, workspace_id: int):
        fd_sets = self.normalization_service.list_fd_sets(user, workspace_id)
        return jsonify({
            "dependency_sets": [fd_set.to_dict() for fd_set in fd_sets],
            "total": len(fd_sets),
        }), 200

    def save_fd_set(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        fd_set = self.normalization_service.save_fd_set(
            user,
            workspace_id,
            name=data.get("name", ""),
            attributes=data.get("attributes", []),
            dependencies=data.get("functional_dependencies", []),
        )
        return jsonify({"dependency_set": fd_set.to_dict()}), 201
