import uuid
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


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
