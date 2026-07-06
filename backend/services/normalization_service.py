from database.connection import db
from models.functional_dependency import FunctionalDependencySet
from models.normalization_report import NormalizationReport
from models.user import User
from services.access_helpers import get_owned_workspace
from services.normalization_algorithms import analyze_normalization
from utils.exceptions import NotFoundError, ValidationError
from utils.normalization_validators import validate_normalization_input


class NormalizationService:
    """Normalization analysis and persistence for a workspace."""

    def analyze(
        self,
        user: User,
        workspace_id: int,
        payload: dict,
        *,
        save_report: bool = False,
        save_fd_set: bool = False,
        fd_set_name: str | None = None,
    ) -> dict:
        workspace = get_owned_workspace(user, workspace_id)

        attributes, dependencies, multivalued = validate_normalization_input(
            payload.get("attributes", []),
            payload.get("functional_dependencies", []),
            payload.get("multivalued_attributes", []),
        )

        closure_of = payload.get("closure_of")
        if closure_of is not None and not isinstance(closure_of, list):
            raise ValidationError("closure_of must be a list of attributes.")

        if closure_of:
            unknown = set(closure_of) - set(attributes)
            if unknown:
                raise ValidationError(
                    f"closure_of references unknown attributes: {', '.join(sorted(unknown))}"
                )

        try:
            report_data = analyze_normalization(
                attributes,
                dependencies,
                multivalued_attributes=multivalued,
                closure_of=closure_of,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        dependency_set_id = None

        if save_fd_set:
            name = (fd_set_name or payload.get("name") or "Default FD Set").strip()
            if not name:
                raise ValidationError("A name is required when saving a functional dependency set.")

            fd_set = FunctionalDependencySet(
                workspace_id=workspace.id,
                name=name,
                attributes=attributes,
                dependencies=dependencies,
            )
            db.session.add(fd_set)
            db.session.flush()
            dependency_set_id = fd_set.id

        report = None
        if save_report:
            report = NormalizationReport(
                workspace_id=workspace.id,
                user_id=user.id,
                dependency_set_id=dependency_set_id,
                attributes=attributes,
                functional_dependencies=dependencies,
                report_data=report_data,
            )
            db.session.add(report)
            db.session.commit()
        elif save_fd_set:
            db.session.commit()

        return {
            "analysis": report_data,
            "report_id": report.id if report else None,
            "dependency_set_id": dependency_set_id,
        }

    def list_reports(self, user: User, workspace_id: int, limit: int = 20) -> list[NormalizationReport]:
        workspace = get_owned_workspace(user, workspace_id)
        return (
            workspace.normalization_reports
            .order_by(NormalizationReport.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_report(self, user: User, workspace_id: int, report_id: int) -> NormalizationReport:
        get_owned_workspace(user, workspace_id)
        report = db.session.get(NormalizationReport, report_id)

        if report is None or report.workspace_id != workspace_id:
            raise NotFoundError("Normalization report not found.")

        return report

    def list_fd_sets(self, user: User, workspace_id: int) -> list[FunctionalDependencySet]:
        workspace = get_owned_workspace(user, workspace_id)
        return workspace.functional_dependency_sets.order_by(FunctionalDependencySet.updated_at.desc()).all()

    def save_fd_set(
        self,
        user: User,
        workspace_id: int,
        name: str,
        attributes: list,
        dependencies: list,
    ) -> FunctionalDependencySet:
        workspace = get_owned_workspace(user, workspace_id)
        cleaned_name = (name or "").strip()
        if not cleaned_name:
            raise ValidationError("Functional dependency set name is required.")

        cleaned_attributes, cleaned_dependencies, _ = validate_normalization_input(
            attributes,
            dependencies,
        )

        fd_set = FunctionalDependencySet(
            workspace_id=workspace.id,
            name=cleaned_name,
            attributes=cleaned_attributes,
            dependencies=cleaned_dependencies,
        )
        db.session.add(fd_set)
        db.session.commit()
        return fd_set
