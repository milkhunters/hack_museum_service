import uuid

from fastapi import APIRouter, Depends
from fastapi import status as http_status

from exhibit.dependencies.services import get_services
from exhibit.models import schemas
from exhibit.services import ServiceFactory
from exhibit.views import ExhibitsResponse
from exhibit.views.exhibit import FileUploadResponse

router = APIRouter()


@router.post(
    "",
    response_model=FileUploadResponse,
    status_code=http_status.HTTP_200_OK
)
async def make_upload_url_file(
        data: schemas.FileCreate,
        services: ServiceFactory = Depends(get_services)
):
    """
    Загрузить файл для поиска

    Требуемое состояние: ACTIVE

    Требуемые права доступа: GET_EXHIBITS

    """
    return FileUploadResponse(content=await services.img_searcher.make_upload_url_file(data))


@router.post("/task/{file_id}", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def make_search_task(
        file_id: uuid.UUID,
        services: ServiceFactory = Depends(get_services)
):
    """
    Создать таску на поиск по изображению

    Требуемое состояние: ACTIVE

    Требуемые права доступа: GET_EXHIBITS

    """
    return await services.img_searcher.make_search_task(file_id)


@router.get("/task/{task_id}", response_model=ExhibitsResponse, status_code=http_status.HTTP_201_CREATED)
async def get_task_result(
        task_id: uuid.UUID,
        services: ServiceFactory = Depends(get_services)
):
    """
    Получить результат поиска по изображению

    """
    return ExhibitsResponse(content=await services.img_searcher.get_task_result(task_id))
