import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from exhibit.models.file_type import FileType
from exhibit.models.schemas.s3 import PreSignedPostUrl
from exhibit.models.state import ExhibitState


class ExhibitTagItem(BaseModel):
    id: uuid.UUID
    title: str

    class Config:
        from_attributes = True


class Exhibit(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    poster: uuid.UUID | None
    views: int
    likes_count: int
    tags: list[ExhibitTagItem]
    state: ExhibitState
    owner_id: uuid.UUID

    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ExhibitSmall(BaseModel):
    id: uuid.UUID
    title: str
    poster: uuid.UUID | None
    views: int
    likes_count: int
    tags: list[ExhibitTagItem]
    state: ExhibitState
    owner_id: uuid.UUID

    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ExhibitCreate(BaseModel):
    title: str
    content: str
    state: ExhibitState
    tags: list[str]

    @field_validator('content')
    def content_must_be_valid(cls, value):
        if not value:
            raise ValueError("Публикация не может быть пустой")

        if len(value) > 32000:
            raise ValueError("Публикация не может содержать более 32000 символов")
        return value

    @field_validator('title')
    def title_must_be_valid(cls, value):
        if not value:
            raise ValueError("Заголовок не может быть пустым")

        if len(value) > 255:
            raise ValueError("Заголовок не может содержать больше 255 символов")
        return value

    @field_validator('tags')
    def tags_must_be_valid(cls, value):
        for tag in value:
            if len(tag) > 32:
                raise ValueError("Тег не может содержать больше 32 символов")
        return value


class ExhibitUpdate(BaseModel):
    title: str = None
    content: str = None
    state: ExhibitState = None
    tags: list[str] = None

    class Config:
        extra = 'ignore'

    @field_validator('content')
    def content_must_be_valid(cls, value):
        if value and len(value) > 32000:
            raise ValueError("Контент не может содержать больше 32000 символов")
        return value

    @field_validator('title')
    def title_must_be_valid(cls, value):
        if value and len(value) > 255:
            raise ValueError("Заголовок не может содержать больше 255 символов")
        return value

    @field_validator('tags')
    def tags_must_be_valid(cls, value):
        for tag in value:
            if len(tag) > 32:
                raise ValueError("Тег не может содержать больше 32 символов")
        return value


class ExhibitFile(BaseModel):
    id: uuid.UUID
    filename: str
    exhibit_id: uuid.UUID
    content_type: str
    is_uploaded: bool

    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ExhibitFileItem(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    url: str

    created_at: datetime
    updated_at: datetime | None


class ExhibitFileCreate(BaseModel):
    filename: str
    content_type: FileType


class ExhibitFileUpload(BaseModel):
    file_id: uuid.UUID
    upload_url: PreSignedPostUrl
