import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi import status as http_status

from exhibit.dependencies.services import get_services
from exhibit.models import schemas
from exhibit.models.state import ExhibitState, RateState
from exhibit.services import ServiceFactory
from exhibit.views import ExhibitResponse, ExhibitsResponse
from exhibit.views.exhibit import ExhibitFilesResponse, ExhibitFileUploadResponse, ExhibitFileResponse

router = APIRouter()


@router.get("", response_model=ExhibitsResponse, status_code=http_status.HTTP_200_OK)
async def get_exhibits(
        page: int = 1,
        per_page: int = 10,
        order_by: Literal["title", "updated_at", "created_at"] = "created_at",
        query: str = None,
        state: ExhibitState = ExhibitState.PUBLISHED,
        owner_id: uuid.UUID = None,
        services: ServiceFactory = Depends(get_services)
):
    """
    Получить список экспонатов

    Требуемое состояние: -

    Требуемые права доступа: GET_PUBLIC_EXHIBITS / GET_PRIVATE_EXHIBITS / GET_SELF_EXHIBITS

    Если указан owner_id, то возвращаются только экспоната этого пользователя,
    причем пользователь с доступом GET_PRIVATE_EXHIBITS может просматривать чужие публикации.
    """
    return ExhibitsResponse(
        content=await services.exhibit.get_exhibits(page, per_page, order_by, query, state, owner_id)
    )


@router.post("", response_model=ExhibitResponse, status_code=http_status.HTTP_201_CREATED)
async def new_exhibit(exhibit: schemas.ExhibitCreate, services: ServiceFactory = Depends(get_services)):
    """
    Создать экспонат

    Требуемое состояние: ACTIVE

    Требуемые права доступа: CREATE_SELF_EXHIBITS

    Максимальный размер экспоната - 32000 символов
    """
    return ExhibitResponse(content=await services.exhibit.create_exhibit(exhibit))


@router.get("/{exhibit_id}", response_model=ExhibitResponse, status_code=http_status.HTTP_200_OK)
async def get_exhibit(exhibit_id: uuid.UUID, services: ServiceFactory = Depends(get_services)):
    """
    Получить экспонат по id

    Требуемое состояние: -

    Требуемые права доступа: GET_PUBLIC_EXHIBITS / GET_PRIVATE_EXHIBITS / GET_SELF_EXHIBITS
    """
    return ExhibitResponse(content=await services.exhibit.get_exhibit(exhibit_id))


@router.put("/{exhibit_id}", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def update_exhibit(
        exhibit_id: uuid.UUID,
        data: schemas.ExhibitUpdate,
        services: ServiceFactory = Depends(get_services)
):
    """
    Обновить экспонат по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: UPDATE_SELF_EXHIBITS / UPDATE_USER_EXHIBITS

    Причем пользователь с доступом UPDATE_USER_EXHIBITS может редактировать чужие публикации.
    """
    await services.exhibit.update_exhibit(exhibit_id, data)


@router.delete("/{exhibit_id}", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_exhibit(exhibit_id: uuid.UUID, services: ServiceFactory = Depends(get_services)):
    """
    Удалить экспонат по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: DELETE_SELF_EXHIBITS / DELETE_USER_EXHIBITS

    Причем пользователь с доступом DELETE_USER_EXHIBITS может удалять чужие публикации.
    """
    await services.exhibit.delete_exhibit(exhibit_id)


@router.post("/rate/{exhibit_id}", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def rate_exhibit(exhibit_id: uuid.UUID, state: RateState, services: ServiceFactory = Depends(get_services)):
    """
    Оценить экспонат по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: RATE_EXHIBITS
    """
    await services.exhibit.rate_exhibit(exhibit_id, state)


@router.get("/files/{exhibit_id}", response_model=ExhibitFilesResponse, status_code=http_status.HTTP_200_OK)
async def get_exhibit_files(exhibit_id: uuid.UUID, services: ServiceFactory = Depends(get_services)):
    """
    Получить список файлов экспоната по id

    Требуемое состояние: -

    Требуемые права доступа: GET_PUBLIC_EXHIBITS / GET_PRIVATE_EXHIBITS / GET_SELF_EXHIBITS
    """
    return ExhibitFilesResponse(content=await services.exhibit.get_exhibit_files(exhibit_id))


@router.get("/files/{exhibit_id}/{file_id}", response_model=ExhibitFileResponse, status_code=http_status.HTTP_200_OK)
async def get_exhibit_file(
        exhibit_id: uuid.UUID,
        file_id: uuid.UUID,
        download: bool = False,
        services: ServiceFactory = Depends(get_services)
):
    """
    Получить файл экспоната по id

    Требуемое состояние: -

    Требуемые права доступа: GET_PUBLIC_EXHIBITS / GET_PRIVATE_EXHIBITS / GET_SELF_EXHIBITS
    """
    return ExhibitFileResponse(content=await services.exhibit.get_exhibit_file(exhibit_id, file_id, download))


@router.post(
    "/files/{exhibit_id}",
    response_model=ExhibitFileUploadResponse,
    status_code=http_status.HTTP_200_OK
)
async def upload_exhibit_file(
        exhibit_id: uuid.UUID,
        data: schemas.ExhibitFileCreate,
        services: ServiceFactory = Depends(get_services)
):
    """
    Загрузить файл экспоната по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: UPDATE_SELF_EXHIBITS / UPDATE_USER_EXHIBITS

    Причем пользователь с доступом UPDATE_USER_EXHIBITS может редактировать чужие публикации.
    """
    return ExhibitFileUploadResponse(content=await services.exhibit.upload_exhibit_file(exhibit_id, data))


@router.post("/files/{exhibit_id}/{file_id}", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def confirm_exhibit_file(
        exhibit_id: uuid.UUID,
        file_id: uuid.UUID,
        services: ServiceFactory = Depends(get_services)
):
    """
    Подтвердить загрузку файла экспоната по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: UPDATE_SELF_EXHIBITS / UPDATE_USER_EXHIBITS

    Причем пользователь с доступом UPDATE_USER_EXHIBITS может редактировать чужие публикации.
    """
    await services.exhibit.confirm_exhibit_file_upload(exhibit_id, file_id)


@router.delete("/files/{exhibit_id}/{file_id}", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_exhibit_file(
        exhibit_id: uuid.UUID,
        file_id: uuid.UUID,
        services: ServiceFactory = Depends(get_services)
):
    """
    Удалить файл экспоната по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: UPDATE_SELF_EXHIBITS / UPDATE_USER_EXHIBITS

    Причем пользователь с доступом UPDATE_USER_EXHIBITS может редактировать чужие публикации.
    """
    await services.exhibit.delete_exhibit_file(exhibit_id, file_id)


@router.post("/poster", response_model=None, status_code=http_status.HTTP_204_NO_CONTENT)
async def set_poster(
        exhibit_id: uuid.UUID,
        file_id: uuid.UUID,
        services: ServiceFactory = Depends(get_services)
):
    """
    Установить постер экспоната по id

    Требуемое состояние: ACTIVE

    Требуемые права доступа: UPDATE_SELF_EXHIBITS / UPDATE_USER_EXHIBITS

    Причем пользователь с доступом UPDATE_USER_EXHIBITS может редактировать чужие публикации.
    """
    await services.exhibit.set_exhibit_poster(exhibit_id, file_id)
