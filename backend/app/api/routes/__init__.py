from app.api.routes.lists import lists_router
from app.api.routes.login import login_router
from app.api.routes.nodes import nodes_router
from app.api.routes.private import private_router
from app.api.routes.users import users_router
from app.api.routes.utils import utils_router

__all__ = [
    login_router,
    users_router,
    utils_router,
    lists_router,
    nodes_router,
    private_router,
]
