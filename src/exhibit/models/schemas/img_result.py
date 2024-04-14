from pydantic import BaseModel

from exhibit.models.schemas import ExhibitSmall


class ImgResult(BaseModel):
    classif: str
    result: list[ExhibitSmall]
