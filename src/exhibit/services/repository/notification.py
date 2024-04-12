from exhibit.models import tables
from exhibit.services.repository.base import BaseRepository


class NotificationRepo(BaseRepository[tables.Notification]):
    table = tables.Notification
