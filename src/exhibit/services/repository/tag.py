from exhibit.models import tables
from exhibit.services.repository.base import BaseRepository


class TagRepo(BaseRepository[tables.Tag]):
    table = tables.Tag
