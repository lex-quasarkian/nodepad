from fastapi import APIRouter

from app.api.routes import (
    lists_router,
    login_router,
    nodes_router,
    private_router,
    users_router,
    utils_router,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login_router)
api_router.include_router(users_router)
api_router.include_router(utils_router)
api_router.include_router(lists_router)
api_router.include_router(nodes_router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private_router)
