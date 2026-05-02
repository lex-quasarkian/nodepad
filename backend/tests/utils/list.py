from sqlalchemy.orm import Session

from app import services
from app.models import NodeList
from app.schemas import NodeListCreate
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_list(db: Session) -> NodeList:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None
    title = random_lower_string()
    description = random_lower_string()
    list_in = NodeListCreate(title=title, description=description)

    return services.lists.create_list(session=db, list_in=list_in, owner_id=owner_id)
