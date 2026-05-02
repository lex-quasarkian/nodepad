import uuid

from sqlalchemy.orm import Session

from app import models


def get_list(session: Session, *, id: uuid.UUID) -> models.NodeList | None:
    return session.get(models.NodeList, id)
