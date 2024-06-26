from typing import Any

from exhibit.models.error import ErrorType
from pydantic import BaseModel


class Error(BaseModel):
    type: ErrorType
    content: Any


class FieldErrorItem(BaseModel):
    field: Any
    location: list[Any]
    message: str
    type: str
