from database.connection import db
from services.access_helpers import get_owned_workspace
from models.user import User
from models.workspace import Workspace
from utils.exceptions import ConflictError
from utils.validators import validate_workspace_name


class WorkspaceService:
    """Workspace CRUD scoped to the authenticated user."""

    def list_workspaces(self, user: User) -> list[Workspace]:
        return (
            Workspace.query
            .filter_by(user_id=user.id)
            .order_by(Workspace.created_at.desc())
            .all()
        )

    def get_dashboard(self, user: User) -> dict:
        workspaces = self.list_workspaces(user)

        return {
            "user": user.to_dict(),
            "workspaces": [workspace.to_dict() for workspace in workspaces],
            "stats": {
                "workspace_count": len(workspaces),
            },
        }

    def create_workspace(
        self,
        user: User,
        name: str,
        description: str | None = None,
    ) -> Workspace:
        cleaned_name = validate_workspace_name(name)
        cleaned_description = description.strip() if description else None

        duplicate = Workspace.query.filter_by(user_id=user.id, name=cleaned_name).first()
        if duplicate:
            raise ConflictError(f"Workspace '{cleaned_name}' already exists.")

        workspace = Workspace(
            name=cleaned_name,
            description=cleaned_description or None,
            user_id=user.id,
        )
        db.session.add(workspace)
        db.session.commit()

        return workspace

    def delete_workspace(self, user: User, workspace_id: int) -> None:
        workspace = get_owned_workspace(user, workspace_id)
        db.session.delete(workspace)
        db.session.commit()

