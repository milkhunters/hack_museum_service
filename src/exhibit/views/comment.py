from .base import BaseView
from exhibit.models import schemas


class CommentResponse(BaseView):
    content: schemas.Comment


class CommentsResponse(BaseView):
    content: list[schemas.CommentNode]
