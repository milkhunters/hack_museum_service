import uuid

from sqlalchemy import select, bindparam, text, UUID, Integer, delete

from exhibit.models import tables
from exhibit.services.repository.base import BaseRepository


class CommentRepo(BaseRepository[tables.Comment]):
    table = tables.Comment

    async def get(self, **kwargs) -> tables.Comment:
        return (await self._session.execute(select(self.table).filter_by(**kwargs))).scalars().first()

    async def delete_comments_by_exhibit(self, exhibit_id: uuid.UUID) -> None:
        select_query = (
            select(tables.CommentTree.descendant_id)
            .where(tables.CommentTree.ancestor_id == tables.CommentTree.descendant_id)
            .where(tables.CommentTree.exhibit_id == exhibit_id)
        )

        delete_query = (
            delete(self.table)
            .where(self.table.id.in_(select_query))
        )

        delete_branch_query = (
            delete(tables.CommentTree)
            .where(tables.CommentTree.exhibit_id == exhibit_id)
        )

        await self.session.execute(delete_query)
        await self.session.execute(delete_branch_query)
        await self.session.commit()


class CommentTreeRepo(BaseRepository[tables.CommentTree]):
    table = tables.CommentTree

    async def create_branch(
            self,
            parent_id: uuid.UUID,
            new_comment_id: uuid.UUID,
            exhibit_id: uuid.UUID,
            parent_level: int
    ):
        sql_raw = text("""
            INSERT INTO comment_tree (ancestor_id, descendant_id, nearest_ancestor_id, exhibit_id, level)
            SELECT ancestor_id, :new_comment_id, :parent_id, :exhibit_id, :parent_level
            FROM comment_tree
            WHERE descendant_id = :parent_id
            UNION ALL SELECT :new_comment_id, :new_comment_id, :parent_id, :exhibit_id, :parent_level
        """)
        params = {
            'new_comment_id': new_comment_id,
            'parent_id': parent_id,
            'exhibit_id': exhibit_id,
            'parent_level': parent_level + 1,
        }
        sql_raw = sql_raw.bindparams(
            bindparam('new_comment_id', type_=UUID),
            bindparam('parent_id', type_=UUID),
            bindparam('exhibit_id', type_=UUID),
            bindparam('parent_level', type_=Integer),
        ).columns()
        result = await self.session.execute(sql_raw, params)
        await self.session.commit()
        return result

    async def get_comments(self, exhibit_id: uuid.UUID):
        # sql_raw = """
        #             SELECT
        #                 tableData.id,
        #                 tableData.content,
        #                 tableData.owner_id,
        #                 tableUser.first_name,
        #                 tableUser.last_name,
        #                 tableUser.username,
        #                 tableTree.nearest_ancestor_id,
        #                 tableTree.exhibit_id,
        #                 tableData.state,
        #                 tableData.create_time,
        #                 tableData.update_time
        #             FROM comment AS tableData
        #             JOIN "user" AS tableUser
        #                 ON tableUser.id = tableData.owner_id
        #             JOIN comment_tree AS tableTree
        #                 ON tableData.id = tableTree.descendant_id
        #             WHERE tableTree.exhibit_id = $1
        #                 AND tableTree.ancestor_id = tableData.id
        #             ORDER BY tableData.id ASC
        #         """
        # smt = select(tables.Comment, tables.CommentTree).select_from(
        #     tables.Comment.join(tables.CommentTree)
        # ).where(tables.CommentTree.exhibit_id == exhibit_id)

        query = (
            select(
                tables.Comment,
                self.table.nearest_ancestor_id,
                self.table.level,
            )
            .join(self.table, tables.Comment.id == self.table.descendant_id)
            .where(self.table.exhibit_id == exhibit_id)
            .where(self.table.ancestor_id == tables.Comment.id)
            .order_by(tables.Comment.id.asc())
        )
        result = await self.session.execute(query)
        return result.fetchall()
