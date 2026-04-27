import uuid

from sqlalchemy.orm import Session

from app import models
from app.schemas import NodeListCreate


def create_list(
    *, session: Session, list_in: NodeListCreate, owner_id: uuid.UUID
) -> models.NodeList:
    db_list = models.NodeList(
        **list_in.model_dump(exclude_unset=True, exclude={"nodes"}), owner_id=owner_id
    )
    session.add(db_list)

    if list_in.nodes:
        for i, node_in in enumerate(list_in.nodes):
            if node_in:
                node_data = node_in.model_dump()
                # Ensure position is set if missing
                if node_data.get("position") is None:
                    node_data["position"] = float(i + 1)

                db_node = models.Node(**node_data)
                db_list.nodes.append(db_node)
                session.add(db_node)

    session.commit()
    session.refresh(db_list)

    return db_list
