import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import List, ListCreate, ListPublic, ListsPublic, ListUpdate, Message

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/", response_model=ListsPublic)
def read_lists(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve lists.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(List)
        count = session.exec(count_statement).one()
        statement = (
            select(List).order_by(col(List.created_at).desc()).offset(skip).limit(limit)
        )
        lists = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(List)
            .where(List.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(List)
            .where(List.owner_id == current_user.id)
            .order_by(col(List.created_at).desc())
            .offset(skip)
            .limit(limit)
        )
        lists = session.exec(statement).all()

    return ListsPublic(data=lists, count=count)


@router.get("/{id}", response_model=ListPublic)
def read_list(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get list by ID.
    """
    list = session.get(List, id)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    if not current_user.is_superuser and (list.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return list


@router.post("/", response_model=ListPublic)
def create_list(
    *, session: SessionDep, current_user: CurrentUser, list_in: ListCreate
) -> Any:
    """
    Create new list.
    """
    list = List.model_validate(list_in, update={"owner_id": current_user.id})
    session.add(list)
    session.commit()
    session.refresh(list)
    return list


@router.put("/{id}", response_model=ListPublic)
def update_list(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    list_in: ListUpdate,
) -> Any:
    """
    Update a list.
    """
    list = session.get(List, id)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    if not current_user.is_superuser and (list.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = list_in.model_dump(exclude_unset=True)
    list.sqlmodel_update(update_dict)
    session.add(list)
    session.commit()
    session.refresh(list)
    return list


@router.delete("/{id}")
def delete_list(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a list.
    """
    list = session.get(List, id)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    if not current_user.is_superuser and (list.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(list)
    session.commit()
    return Message(message="List deleted successfully")
