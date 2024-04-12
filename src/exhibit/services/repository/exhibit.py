import uuid

from sqlalchemy import select, text, func, or_, and_
from sqlalchemy.orm import subqueryload

from exhibit.models import tables
from .base import BaseRepository
from ...models.tables import Like


class ExhibitRepo(BaseRepository[tables.Exhibit]):
    table = tables.Exhibit

    async def add_tag(self, exhibit_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        obj = await self.table.get(id=exhibit_id)
        obj.tags.add(tables.Tag.get(id=tag_id))
        await obj.save()

    async def search(
            self,
            query: str,
            fields: list[str],
            limit: int = 100,
            offset: int = 0,
            order_by: str = "created_at",
            **kwargs
    ) -> list[tables.Exhibit]:
        return await self.__get_range(
            query=query,
            fields=fields,
            limit=limit,
            offset=offset,
            order_by=order_by,
            **kwargs
        )

    async def get_all(
            self, limit: int = 100,
            offset: int = 0,
            order_by: str = "id",
            **kwargs
    ) -> list[tables.Exhibit]:
        return await self.__get_range(
            limit=limit,
            offset=offset,
            order_by=order_by,
            **kwargs
        )

    async def get(self, **kwargs) -> tables.Exhibit:
        stmt = select(self.table).filter_by(**kwargs).options(subqueryload(self.table.tags))
        return (await self._session.execute(stmt)).scalars().first()

    async def __get_range(
            self,
            *,
            query: str = None,
            fields: list[str] = None,
            limit: int = 100,
            offset: int = 0,
            order_by: str = "id",
            **kwargs
    ) -> list[tables.Exhibit]:
        # Лайки
        subquery = (
            select(
                Like.exhibit_id,
                func.count(Like.id).label('likes_count')
            )
            .group_by(Like.exhibit_id)
            .subquery()
        )

        # Основной запрос
        stmt = (
            select(
                self.table,
                subquery.c.likes_count
            )
            .outerjoin(subquery, self.table.id == subquery.c.exhibit_id)
            .options(subqueryload(self.table.tags))
            .order_by(text(order_by))
            .limit(limit)
            .offset(offset)
        )

        # Фильтры kwargs
        stmt = stmt.where(
            and_(*[getattr(self.table, field) == value for field, value in kwargs.items()])
        )

        # Поиск
        if query and fields:
            stmt = stmt.where(
                or_(*[getattr(self.table, field).ilike(f"%{query}%") for field in fields])
            )

        result = await self._session.execute(stmt)
        exhibits_with_likes = []
        for row in result:
            exhibit = row[0]
            likes_count = row[1]
            exhibit.likes_count = likes_count if likes_count else 0
            exhibits_with_likes.append(exhibit)

        return exhibits_with_likes
