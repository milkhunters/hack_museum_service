from .base import BaseView
from exhibit.models import schemas


class S3UploadResponse(BaseView):
    content: schemas.PreSignedPostUrl
