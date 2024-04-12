from fastapi import APIRouter

from exhibit.controllers import stats
from exhibit.controllers import notify
from exhibit.controllers import exhibits
from exhibit.controllers import comments
from exhibit.controllers import permission


def register_api_router(is_debug: bool) -> APIRouter:
    root_api_router = APIRouter(prefix="/api/v1" if is_debug else "")

    root_api_router.include_router(exhibits.router, prefix="/exhibit", tags=["Exhibit"])
    root_api_router.include_router(comments.router, prefix="/comment", tags=["Comment"])
    root_api_router.include_router(notify.router, prefix="/notification", tags=["Notification"])
    root_api_router.include_router(permission.router, prefix="/permission", tags=["Permission"])
    root_api_router.include_router(stats.router, prefix="", tags=["Stats"])

    return root_api_router
