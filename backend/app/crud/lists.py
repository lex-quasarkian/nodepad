import uuid

from sqlalchemy.orm import Session

from app import models
from app.schemas import NodeListCreate


def create_list(
    *, session: Session, list_in: NodeListCreate, owner_id: uuid.UUID
) -> models.NodeList:
    db_list = models.NodeList(**list_in.model_dump(), owner_id=owner_id)

    session.add(db_list)
    session.commit()
    session.refresh(db_list)

    return db_list
