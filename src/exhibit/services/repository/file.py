from exhibit.models import tables
from exhibit.services.repository.base import BaseRepository


class FileRepo(BaseRepository[tables.File]):
    table = tables.File
