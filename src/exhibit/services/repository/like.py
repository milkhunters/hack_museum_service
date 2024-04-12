from exhibit.models import tables
from exhibit.services.repository.base import BaseRepository


class LikeRepo(BaseRepository[tables.Like]):
    table = tables.Like
