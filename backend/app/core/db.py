from edwh_uuid7 import uuid7
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree

from app import crud
from app.core.config import settings
from app.models import Node, NodeList, User
from app.schemas.users import UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> None:
    # 1. Ensure First Superuser exists
    user = session.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).scalar_one_or_none()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.users.create_user(session=session, user_create=user_in)

    # 2. Create default hierarchical list if it doesn't exist
    list_title = "Weekend Getaway: Chamonix"
    db_list = session.execute(
        select(NodeList).where(NodeList.title == list_title)
    ).scalar_one_or_none()

    if not db_list:
        db_list = NodeList(
            title=list_title,
            description="Logistics and gear for the trip",
            owner_id=user.id,
        )
        session.add(db_list)
        session.flush()

        def add_node(content, position, parent_id=None):
            node_id = uuid7()
            node = Node(
                id=node_id,
                content=content,
                position=float(position),
                nodelist_id=db_list.id,
                parent_id=parent_id,
            )
            if parent_id:
                parent = session.get(Node, parent_id)
                if not parent:
                    raise ValueError(f"Parent node {parent_id} not found")
                node.level = parent.level + 1
                node.path = Ltree(f"{parent.path}.{node_id.hex}")
            else:
                node.level = 0
                node.path = Ltree(node_id.hex)

            session.add(node)
            session.flush()
            return node

        # Roots (Level 0)
        logistics = add_node("Logistical Prep", 1000)
        add_node("Grocery Run (Whole Foods)", 2000)
        gear = add_node("Gear & Packing", 3000)

        # Children of Logistics (Level 1)
        transport = add_node("Transportation", 1000, logistics.id)
        add_node("Confirm Airbnb check-in time", 2000, logistics.id)

        # Sub-children of Transportation (Level 2)
        add_node("Book Eurotunnel tickets", 1000, transport.id)
        add_node("Refill windshield washer fluid", 2000, transport.id)

        # Children of Gear (Level 1)
        hiking = add_node("Hiking boots (waterproof)", 1000, gear.id)
        add_node("Power bank", 2000, gear.id)

        # Sub-child of Hiking (Level 2)
        add_node("Apply waterproof spray", 1000, hiking.id)

        session.commit()
