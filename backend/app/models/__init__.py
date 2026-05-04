from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all models.
    """

    pass


from app.models.lists import Node, NodeList  # noqa: F401, E402
from app.models.users import User  # noqa: F401, E402
