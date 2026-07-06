from database.connection import db
from models.workspace import Workspace
from utils.exceptions import NotFoundError


def get_workspace(workspace_id: int) -> Workspace:
    workspace = db.session.get(Workspace, workspace_id)

    if workspace is None:
        raise NotFoundError("Workspace not found.")

    return workspace


def get_owned_workspace(user, workspace_id: int) -> Workspace:
    """Return a workspace owned by the given user."""
    workspace = get_workspace(workspace_id)

    if workspace.user_id != user.id:
        raise NotFoundError("Workspace not found.")

    return workspace
