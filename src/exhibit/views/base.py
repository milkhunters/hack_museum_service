from typing import Any

from pydantic import BaseModel

from exhibit.models.schemas import Error


class BaseView(BaseModel):
    content: Any = None
    error: Error = None
