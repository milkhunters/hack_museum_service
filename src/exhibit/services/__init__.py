from exhibit.models.auth import BaseUser
from . import auth
from . import repository
from .exhibit import ExhibitApplicationService
from .comment import CommentApplicationService
from .img_searcher import ImgSearcherApplicationService, ImgSearchAdapter
from .notification import NotificationApplicationService
from .permission import PermissionApplicationService
from .stats import StatsApplicationService


class ServiceFactory:
    def __init__(
            self,
            repo_factory: repository.RepoFactory,
            *,
            current_user: BaseUser,
            config,
            file_storage,
            isa,
            task_result
    ):
        self._repo = repo_factory
        self._current_user = current_user
        self._config = config
        self._file_storage = file_storage
        self._isa = isa
        self._task_result = task_result

    @property
    def exhibit(self) -> ExhibitApplicationService:
        return ExhibitApplicationService(
            self._current_user,
            exhibit_repo=self._repo.exhibit,
            tag_repo=self._repo.tag,
            comment_repo=self._repo.comment,
            comment_tree_repo=self._repo.comment_tree,
            like_repo=self._repo.like,
            file_repo=self._repo.file,
            file_storage=self._file_storage,
            isa=ImgSearchAdapter
        )

    @property
    def comment(self) -> CommentApplicationService:
        return CommentApplicationService(
            self._current_user,
            comment_repo=self._repo.comment,
            comment_tree_repo=self._repo.comment_tree,
            notify_repo=self._repo.notification,
            exhibit_repo=self._repo.exhibit
        )

    @property
    def notification(self) -> NotificationApplicationService:
        return NotificationApplicationService(self._current_user, notify_repo=self._repo.notification)

    @property
    def stats(self) -> StatsApplicationService:
        return StatsApplicationService(config=self._config)

    @property
    def permission(self) -> PermissionApplicationService:
        return PermissionApplicationService()

    @property
    def img_searcher(self) -> ImgSearcherApplicationService:
        return ImgSearcherApplicationService(
            current_user=self._current_user,
            exhibit_repo=self._repo.exhibit,
            file_storage=self._file_storage,
            isa=self._isa,
            task_result=self._task_result
        )
