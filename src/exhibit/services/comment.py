import uuid
from datetime import timedelta, datetime

import pytz

from exhibit.models import schemas
from exhibit.models.permission import Permission
from exhibit.models.auth import BaseUser
from exhibit.models.state import CommentState, ExhibitState, UserState
from exhibit.models.state import NotificationType

from exhibit import exceptions
from exhibit.services.auth.filters import state_filter
from exhibit.services.auth.filters import permission_filter
from exhibit.services.repository import CommentRepo, ExhibitRepo
from exhibit.services.repository import CommentTreeRepo
from exhibit.services.repository import NotificationRepo


class CommentApplicationService:
    def __init__(
            self,
            current_user: BaseUser,
            comment_repo: CommentRepo,
            comment_tree_repo: CommentTreeRepo,
            notify_repo: NotificationRepo,
            exhibit_repo: ExhibitRepo
    ):
        self._current_user = current_user
        self._repo = comment_repo
        self._tree_repo = comment_tree_repo
        self._notification_repo = notify_repo
        self._exhibit_repo = exhibit_repo

    @permission_filter(Permission.CREATE_COMMENT)
    @state_filter(UserState.ACTIVE)
    async def add_comment(
            self,
            exhibit_id: uuid.UUID,
            data: schemas.CommentCreate,
            parent_id: uuid.UUID = None
    ) -> schemas.Comment:
        """
        Добавить комментарий к экспонату

        :param exhibit_id: идентификатор экспонату
        :param data: данные комментария
        :param parent_id: идентификатор родительского комментария
        :return:

        """

        exhibit = await self._exhibit_repo.get(id=exhibit_id)
        if exhibit is None:
            raise exceptions.NotFound("Публикация не найдена")

        if exhibit.state != ExhibitState.PUBLISHED:
            raise exceptions.BadRequest("Нельзя добавить комментарий к неопубликованной экспонату")

        parent = None
        parent_level = -1
        if parent_id is not None:
            parent = await self._repo.get(id=parent_id)
            if parent is None:
                raise exceptions.NotFound("Родительский комментарий не найден")

            parent_as_node = await self._tree_repo.get(ancestor_id=parent_id, descendant_id=parent_id)
            if parent_as_node is None:
                raise exceptions.NotFound("Родительский комментарий не связан с публикацией")

            if parent_as_node.exhibit_id != exhibit_id:
                raise exceptions.BadRequest(f"Комментарий не принадлежит экспонату с id:{exhibit_id}")

            parent_level = parent_as_node.level

        if parent and parent.state == CommentState.DELETED:
            raise exceptions.BadRequest("Родительский комментарий удален")

        new_comment = await self._repo.create(
            content=data.content,
            owner_id=self._current_user.id,
        )

        if parent and parent.owner_id != new_comment.owner_id:
            await self._notification_repo.create(
                owner_id=parent.owner_id,
                type_id=NotificationType.COMMENT_ANSWER,
                content_id=new_comment.id,
                content=f"{new_comment.owner.username} ответил на Ваш комментарий"
            )

        await self._tree_repo.create_branch(
            parent_id=parent_id,
            new_comment_id=new_comment.id,
            exhibit_id=exhibit_id,
            parent_level=parent_level
        )
        return schemas.Comment.model_validate(new_comment)

    async def get_comment(self, comment_id: uuid.UUID) -> schemas.Comment:
        comment = await self._repo.get(id=comment_id)
        if comment is None:
            raise exceptions.NotFound(f"Комментарий c id:{comment_id} не найден")

        if comment.state == CommentState.DELETED:

            if Permission.GET_DELETED_COMMENTS.value not in self._current_user.permissions:
                raise exceptions.AccessDenied("Комментарий удален")
            else:
                comment.content = f"(Комментарий удален): {comment.content}"

        elif (
                comment.state == CommentState.PUBLISHED and
                Permission.GET_PUBLIC_COMMENTS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать публичные комментарии")

        return schemas.Comment.model_validate(comment)

    @permission_filter(Permission.GET_PUBLIC_COMMENTS)
    async def get_comments(self, exhibit_id: uuid.UUID) -> list[schemas.CommentNode]:
        """
        Получить все комментарии экспонату

        """
        exhibit = await self._exhibit_repo.get(id=exhibit_id)
        if exhibit is None:
            raise exceptions.NotFound("Публикация не найдена")

        raw = await self._tree_repo.get_comments(exhibit_id)

        # Подготовка
        comment_list = []
        for obj, nearest_ancestor_id, level in raw:
            comment = schemas.Comment.model_validate(obj)
            if comment.state == CommentState.DELETED:
                if Permission.GET_DELETED_COMMENTS.value not in self._current_user.permissions:
                    comment.content = "Комментарий удален"
                else:
                    comment.content = f"(Комментарий удален): {comment.content}"

            comment_list.append(schemas.CommentNode(
                **comment.model_dump(),
                answers=[],
                parent_id=nearest_ancestor_id,
                level=level
            ))

        # Сортировка
        comment_tree = []
        for comment in comment_list:
            if comment.level == 0:
                comment_tree.append(comment)
            for descendant in comment_list:
                if descendant.parent_id == comment.id:
                    comment.answers.append(descendant)
        return comment_tree

    @state_filter(UserState.ACTIVE)
    async def delete_comment(self, comment_id: uuid.UUID) -> None:
        """
        Удалить комментарий
        """
        comment = await self._repo.get(id=comment_id)
        if comment is None:
            raise exceptions.NotFound(f"Комментарий c id:{comment_id} не найден")

        if comment.state == CommentState.DELETED:
            raise exceptions.BadRequest(f"Комментарий c id:{comment_id} уже удален")

        if (
                comment.owner_id != self._current_user.id and
                Permission.DELETE_USER_COMMENT.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Нельзя удалить чужой комментарий")

        if (
                comment.owner_id == self._current_user.id and
                Permission.DELETE_SELF_COMMENT.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Нельзя удалить свой комментарий")

        await self._repo.update(id=comment_id, state=CommentState.DELETED)

    @permission_filter(Permission.DELETE_USER_COMMENT)
    @state_filter(UserState.ACTIVE)
    async def delete_all_comments(self, exhibit_id: uuid) -> None:
        """
        Удалить все комментарии экспонату
        """
        exhibit = await self._exhibit_repo.get(id=exhibit_id)
        if exhibit is None:
            raise exceptions.NotFound("Публикация не найдена")

        await self._repo.delete_comments_by_exhibit(exhibit_id)

    @state_filter(UserState.ACTIVE)
    async def update_comment(self, comment_id: uuid.UUID, data: schemas.CommentUpdate) -> None:
        """
        Изменить комментарий

        """
        comment = await self._repo.get(id=comment_id)
        if comment is None:
            raise exceptions.NotFound(f"Комментарий c id:{comment_id} не найден")

        if comment.state == CommentState.DELETED:
            raise exceptions.BadRequest(f"Комментарий c id:{comment_id} уже удален")

        if (
                comment.owner_id != self._current_user.id and
                Permission.UPDATE_USER_COMMENT.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Нельзя изменить чужой комментарий")

        if (
                comment.owner_id == self._current_user.id and
                Permission.UPDATE_SELF_COMMENT.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Нельзя изменить свой комментарий")

        if (
                (comment.created_at + timedelta(days=1) < datetime.now(pytz.utc)) and
                Permission.UPDATE_USER_COMMENT.value not in self._current_user.permissions
        ):
            raise exceptions.BadRequest("Нельзя изменить комментарий старше 24 часов")

        await self._repo.update(id=comment_id, **data.model_dump(exclude_unset=True))
