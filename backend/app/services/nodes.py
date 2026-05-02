import uuid
from datetime import datetime, timezone

from edwh_uuid7 import uuid7
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree

from app import models
from app.crud import nodes as crud_nodes
from app.schemas.lists import NodeCreate, NodeUpdate


def update_node(
    session: Session, *, db_node: models.Node, node_in: NodeUpdate
) -> models.Node:
    node_data = node_in.model_dump(exclude_unset=True)

    # Handle parent change
    if "parent_id" in node_data and node_data["parent_id"] != db_node.parent_id:
        parent_id = node_data["parent_id"]
        old_path = str(db_node.path)
        db_node.parent_id = parent_id

        # Calculate new path and level for the node itself
        if parent_id is None:
            db_node.path = Ltree(db_node.id.hex)
            db_node.level = 0
        else:
            parent = session.get(models.Node, parent_id)
            if parent:
                db_node.path = Ltree(f"{parent.path}.{db_node.id.hex}")
                db_node.level = parent.level + 1
            else:
                db_node.path = Ltree(db_node.id.hex)
                db_node.level = 0

        new_path = str(db_node.path)

        # Cascading update for descendants: update both path and level
        session.execute(
            text("""
            UPDATE node
            SET
                path = :new_path || subpath(path, nlevel(:old_path)),
                level = level + (nlevel(:new_path) - nlevel(:old_path))
            WHERE path <@ :old_path AND id != :node_id
        """),
            {
                "new_path": new_path,
                "old_path": old_path,
                "node_id": db_node.id,
            },
        )

    # Handle level change (cascading to descendants)
    if "level" in node_data and node_data["level"] != db_node.level:
        level_diff = node_data["level"] - db_node.level
        old_path = str(db_node.path)
        session.execute(
            text("""
            UPDATE node
            SET level = level + :diff
            WHERE path <@ :old_path AND id != :node_id
        """),
            {
                "diff": level_diff,
                "old_path": old_path,
                "node_id": db_node.id,
            },
        )

    # Update other fields (content, position etc)
    for field in node_data:
        if field != "parent_id" and hasattr(db_node, field):
            setattr(db_node, field, node_data[field])

    session.add(db_node)

    # Update parent list's updated_at
    db_list = session.get(models.NodeList, db_node.nodelist_id)
    if db_list:
        db_list.updated_at = datetime.now(timezone.utc)
        session.add(db_list)

    session.commit()
    session.refresh(db_node)
    return db_node


def create_node(
    session: Session, *, node_in: NodeCreate, nodelist_id: uuid.UUID
) -> models.Node:
    node_id = node_in.id or uuid7()
    parent_id = node_in.parent_id

    # Calculate position
    pos = crud_nodes.get_position_end(session, nodelist_id, parent_id)

    # Calculate path and level
    if parent_id is None:
        path = Ltree(node_id.hex)
        level = 0
    else:
        parent = session.get(models.Node, parent_id)
        if parent:
            path = Ltree(f"{parent.path}.{node_id.hex}")
            level = parent.level + 1
        else:
            path = Ltree(node_id.hex)
            level = 0

    db_node = models.Node(
        **node_in.model_dump(exclude={"id", "position"}),
        id=node_id,
        nodelist_id=nodelist_id,
        position=pos,
        path=path,
        level=level,
    )
    session.add(db_node)

    # Update parent list's updated_at
    db_list = session.get(models.NodeList, db_node.nodelist_id)
    if db_list:
        db_list.updated_at = datetime.now(timezone.utc)
        session.add(db_list)

    session.commit()
    session.refresh(db_node)
    return db_node


def reorder_node(
    session: Session,
    *,
    db_node: models.Node,
    before_id: uuid.UUID | None = None,
    after_id: uuid.UUID | None = None,
) -> models.Node:
    """
    Reorder node among its siblings.
    If before_id and after_id are provided, place between them.
    If only before_id, place at start.
    If only after_id, place at end.
    """
    nodelist_id = db_node.nodelist_id
    parent_id = db_node.parent_id

    if before_id and after_id:
        new_pos = crud_nodes.get_position_between(session, after_id, before_id)
    elif before_id:
        new_pos = crud_nodes.get_position_start(session, nodelist_id, parent_id)
    elif after_id:
        new_pos = crud_nodes.get_position_end(session, nodelist_id, parent_id)
    else:
        return db_node

    db_node.position = new_pos
    session.add(db_node)

    # Update parent list's updated_at
    db_list = session.get(models.NodeList, nodelist_id)
    if db_list:
        db_list.updated_at = datetime.now(timezone.utc)
        session.add(db_list)

    session.commit()
    session.refresh(db_node)
    return db_node
