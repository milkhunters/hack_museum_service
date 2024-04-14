from exhibit.models import schemas
from exhibit.views import BaseView


class ImgSearchResultResponse(BaseView):
    content: schemas.ImgResult
