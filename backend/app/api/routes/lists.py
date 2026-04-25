import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import NodeList
from app.schemas import (
    Message,
    NodeListCreate,
    NodeListPublic,
    NodeListsPublic,
    NodeListUpdate,
)

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/", response_model=NodeListsPublic)
def read_lists(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve lists.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(NodeList)
        count = session.scalar(count_statement)
        statement = (
            select(NodeList)
            .order_by(NodeList.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        lists = list(session.scalars(statement).all())
    else:
        count_statement = (
            select(func.count())
            .select_from(NodeList)
            .where(NodeList.owner_id == current_user.id)
        )
        count = session.scalar(count_statement)
        statement = (
            select(NodeList)
            .where(NodeList.owner_id == current_user.id)
            .order_by(NodeList.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        lists = list(session.scalars(statement).all())

    return NodeListsPublic(data=lists, count=count)


@router.get("/{id}", response_model=NodeListPublic)
def read_list(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get list by ID.
    """
    list = session.get(NodeList, id)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    if not current_user.is_superuser and (list.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return list


@router.post("/", response_model=NodeListPublic)
def create_list(
    *, session: SessionDep, current_user: CurrentUser, list_in: NodeListCreate
) -> Any:
    """
    Create new list.
    """

    list_obj = crud.lists.create_list(
        session=session, list_in=list_in, owner_id=current_user.id
    )
    return list_obj


@router.put("/{id}", response_model=NodeListPublic)
def update_list(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    list_in: NodeListUpdate,
) -> Any:
    """
    Update a list.
    """
    list_obj = session.get(NodeList, id)
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    if not current_user.is_superuser and (list_obj.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = list_in.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(list_obj, key, value)

    session.add(list_obj)
    session.commit()
    session.refresh(list_obj)

    return list_obj


@router.delete("/{id}")
def delete_list(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a list.
    """
    list_obj = session.get(NodeList, id)
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    if not current_user.is_superuser and (list_obj.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(list_obj)
    session.commit()
    return Message(message="List deleted successfully")
