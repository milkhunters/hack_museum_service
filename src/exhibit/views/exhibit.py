from .base import BaseView
from exhibit.models import schemas


class ExhibitResponse(BaseView):
    content: schemas.Exhibit


class ExhibitsResponse(BaseView):
    content: list[schemas.ExhibitSmall]


class ExhibitFilesResponse(BaseView):
    content: list[schemas.ExhibitFileItem]


class ExhibitFileResponse(BaseView):
    content: schemas.ExhibitFileItem


class ExhibitFileUploadResponse(BaseView):
    content: schemas.ExhibitFileUpload
