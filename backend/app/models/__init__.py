from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all models.
    """

    pass


from app.models.lists import Node, NodeList
from app.models.users import User

__all__ = ["Base", "Node", "NodeList", "User"]
