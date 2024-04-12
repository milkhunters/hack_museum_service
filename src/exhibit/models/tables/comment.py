import uuid

from sqlalchemy import Column, UUID, VARCHAR, Enum, DateTime, func, ForeignKey, Integer, BigInteger
from sqlalchemy.orm import relationship

from exhibit.db import Base
from exhibit.models.state import CommentState


class Comment(Base):
    """
    The Comment model

    """
    __tablename__ = "comments"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(VARCHAR(1000), nullable=False)
    state = Column(Enum(CommentState), default=CommentState.PUBLISHED)

    owner_id = Column(UUID(as_uuid=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.id}>'


class CommentTree(Base):
    """
    The CommentSubset model
    («Closure Table» и «Adjacency List»)

    # Описание полей
    ancestor: предок
    descendant: потомок
    nearest_ancestor: ближайший предок
    exhibit: пост
    level: уровень вложенности

    """

    __tablename__ = "comment_tree"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger(), primary_key=True, autoincrement=True)
    ancestor_id = Column(UUID(as_uuid=True), nullable=False)
    descendant_id = Column(UUID(as_uuid=True), nullable=False)
    nearest_ancestor_id = Column(UUID(as_uuid=True), nullable=True)
    exhibit_id = Column(UUID(as_uuid=True), ForeignKey("exhibits.id"), nullable=False)
    exhibit = relationship("models.tables.exhibit.Exhibit", back_populates="comments_tree")
    level = Column(Integer())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.id}>'
