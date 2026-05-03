import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models, services
from app.schemas.lists import NodeCreate, NodeUpdate


def get_position_between(
    session: Session,
    left_id: uuid.UUID,
    right_id: uuid.UUID,
) -> Decimal:
    query = text("""
        SELECT (l.position + r.position) / 2 AS pos
        FROM node l
        JOIN node r ON (l.parent_id = r.parent_id OR (l.parent_id IS NULL AND r.parent_id IS NULL))
        WHERE l.id = :left_id AND r.id = :right_id
        FOR UPDATE
    """)
    result = session.execute(
        query,
        {
            "left_id": left_id,
            "right_id": right_id,
        },
    ).scalar()
    return result


def get_position_start(
    session: Session,
    nodelist_id: uuid.UUID,
    parent_id: uuid.UUID | None,
) -> Decimal:
    query = text("""
        SELECT position - 1000
        FROM node
        WHERE nodelist_id = :nodelist_id
          AND (parent_id = :parent_id OR (parent_id IS NULL AND :parent_id IS NULL))
        ORDER BY position ASC
        LIMIT 1
        FOR UPDATE
    """)
    result = session.execute(
        query,
        {
            "nodelist_id": nodelist_id,
            "parent_id": parent_id,
        },
    ).scalar()
    return result if result is not None else Decimal("1000")


def get_position_end(
    session: Session,
    nodelist_id: uuid.UUID,
    parent_id: uuid.UUID | None,
) -> Decimal:
    query = text("""
        SELECT position + 1000
        FROM node
        WHERE nodelist_id = :nodelist_id
          AND (parent_id = :parent_id OR (parent_id IS NULL AND :parent_id IS NULL))
        ORDER BY position DESC
        LIMIT 1
        FOR UPDATE
    """)
    result = session.execute(
        query,
        {
            "nodelist_id": nodelist_id,
            "parent_id": parent_id,
        },
    ).scalar()
    return result if result is not None else Decimal("1000")


def reindex_nodes(
    session: Session, nodelist_id: uuid.UUID, parent_id: uuid.UUID | None
):
    query = text("""
        WITH ordered AS (
            SELECT id,
                   ROW_NUMBER() OVER (ORDER BY position) * 1000 AS new_pos
            FROM node
            WHERE nodelist_id = :nodelist_id
              AND (parent_id = :parent_id OR (parent_id IS NULL AND :parent_id IS NULL))
        )
        UPDATE node n
        SET position = o.new_pos
        FROM ordered o
        WHERE n.id = o.id;
    """)
    session.execute(query, {"nodelist_id": nodelist_id, "parent_id": parent_id})


def apply_cascading_path_update(
    session: Session,
    *,
    node_id: uuid.UUID,
    old_path: str,
    new_path: str,
):
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
            "node_id": node_id,
        },
    )


def apply_cascading_level_update(
    session: Session,
    *,
    node_id: uuid.UUID,
    old_path: str,
    level_diff: int,
):
    session.execute(
        text("""
        UPDATE node
        SET level = level + :diff
        WHERE path <@ :old_path AND id != :node_id
    """),
        {
            "diff": level_diff,
            "old_path": old_path,
            "node_id": node_id,
        },
    )


def update_parent_list_timestamp(session: Session, nodelist_id: uuid.UUID):
    db_list = session.get(models.NodeList, nodelist_id)
    if db_list:
        db_list.updated_at = datetime.now(timezone.utc)
        session.add(db_list)


def create_node(
    session: Session, *, node_in: NodeCreate, nodelist_id: uuid.UUID
) -> models.Node:
    from edwh_uuid7 import uuid7

    node_id = node_in.id or uuid7()
    parent_id = node_in.parent_id

    # Calculate position
    pos = get_position_end(session, nodelist_id, parent_id)

    # Fetch parent for path/level calculation
    parent = session.get(models.Node, parent_id) if parent_id else None
    path, level = services.nodes.calculate_path_and_level(
        node_id,
        parent.path if parent else None,
        parent.level if parent else None,
    )

    db_node = models.Node(
        **node_in.model_dump(exclude={"id", "position"}),
        id=node_id,
        nodelist_id=nodelist_id,
        position=pos,
        path=path,
        level=level,
    )
    session.add(db_node)
    update_parent_list_timestamp(session, nodelist_id)
    session.commit()
    session.refresh(db_node)
    return db_node


def update_node(
    session: Session, *, db_node: models.Node, node_in: NodeUpdate
) -> models.Node:
    node_data = node_in.model_dump(exclude_unset=True)

    # Handle parent change
    if "parent_id" in node_data and node_data["parent_id"] != db_node.parent_id:
        parent_id = node_data["parent_id"]
        old_path = str(db_node.path)
        db_node.parent_id = parent_id

        parent = session.get(models.Node, parent_id) if parent_id else None
        new_path, new_level = services.nodes.calculate_path_and_level(
            db_node.id,
            parent.path if parent else None,
            parent.level if parent else None,
        )

        db_node.path = new_path
        db_node.level = new_level

        apply_cascading_path_update(
            session,
            node_id=db_node.id,
            old_path=old_path,
            new_path=str(new_path),
        )

    # Handle level change (cascading to descendants)
    if "level" in node_data and node_data["level"] != db_node.level:
        level_diff = node_data["level"] - db_node.level
        old_path = str(db_node.path)
        apply_cascading_level_update(
            session, node_id=db_node.id, old_path=old_path, level_diff=level_diff
        )

    # Update other fields (content, position etc)
    for field in node_data:
        if field != "parent_id" and hasattr(db_node, field):
            setattr(db_node, field, node_data[field])

    session.add(db_node)
    update_parent_list_timestamp(session, db_node.nodelist_id)
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
    nodelist_id = db_node.nodelist_id
    parent_id = db_node.parent_id

    if before_id and after_id:
        new_pos = get_position_between(session, after_id, before_id)
    elif before_id:
        new_pos = get_position_start(session, nodelist_id, parent_id)
    elif after_id:
        new_pos = get_position_end(session, nodelist_id, parent_id)
    else:
        return db_node

    db_node.position = new_pos
    session.add(db_node)
    update_parent_list_timestamp(session, nodelist_id)
    session.commit()
    session.refresh(db_node)
    return db_node
