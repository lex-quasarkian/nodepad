import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud, models
from app.api.deps import CurrentUser, SessionDep
from app.models import Node
from app.schemas.lists import Node as NodePublic
from app.schemas.lists import NodeCreate, NodeUpdate

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("/", response_model=NodePublic)
def create_node(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    nodelist_id: uuid.UUID,
    node_in: NodeCreate,
) -> Any:
    """
    Create a new node.
    """
    db_list = session.get(models.NodeList, nodelist_id)
    if not db_list:
        raise HTTPException(status_code=404, detail="List not found")

    if not current_user.is_superuser and (db_list.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.nodes.create_node(
        session=session, node_in=node_in, nodelist_id=nodelist_id
    )


@router.patch("/{id}", response_model=NodePublic)
def patch_node(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    node_in: NodeUpdate,
) -> Any:
    """
    Update a node.
    """
    db_node = session.get(Node, id)
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Check permissions (owner of the list)
    if not current_user.is_superuser and (db_node.nodelist.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_node = crud.nodes.update_node(session=session, db_node=db_node, node_in=node_in)

    return db_node


@router.post("/{id}/reorder", response_model=NodePublic)
def reorder_node(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    before_id: uuid.UUID | None = None,
    after_id: uuid.UUID | None = None,
) -> Any:
    """
    Reorder node.
    """
    db_node = session.get(Node, id)
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")

    if not current_user.is_superuser and (db_node.nodelist.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.nodes.reorder_node(
        session=session, db_node=db_node, before_id=before_id, after_id=after_id
    )
