from fastapi import Depends
from fastapi.requests import Request

from exhibit.dependencies.repos import get_repos
from exhibit.services import ServiceFactory
from exhibit.services.repository import RepoFactory


async def get_services(
        request: Request,
        repos: RepoFactory = Depends(get_repos)
) -> ServiceFactory:
    global_scope = request.app.state
    local_scope = request.scope

    yield ServiceFactory(
        repos,
        current_user=local_scope.get("user"),
        config=global_scope.config,
        file_storage=global_scope.file_storage,
        isa=global_scope.isa,
        task_result=global_scope.task_result
    )
