import uuid

from sqlalchemy import Column, UUID, VARCHAR, Enum, DateTime, func, ForeignKey, BIGINT
from sqlalchemy.orm import relationship

from exhibit.db import Base

from exhibit.models.state import ExhibitState


class Exhibit(Base):
    """
    The Exhibit model
    """
    __tablename__ = "exhibits"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(VARCHAR(255), nullable=False)
    poster = Column(UUID(as_uuid=True), nullable=True)
    content = Column(VARCHAR(32000), nullable=False)
    state = Column(Enum(ExhibitState), default=ExhibitState.DRAFT)
    views = Column(BIGINT(), nullable=False, default=0)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    likes = relationship("models.tables.like.Like", back_populates="exhibit")
    tags = relationship('models.tables.tag.Tag', secondary='exhibit_tags', back_populates='exhibits')
    comments_tree = relationship("models.tables.comment.CommentTree", back_populates="exhibit")
    files = relationship("models.tables.file.File", back_populates="exhibit")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.id}>'


class ExhibitTag(Base):
    """
    Many-to-many table for Exhibit and Tag
    """
    __tablename__ = "exhibit_tags"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exhibit_id = Column(UUID(as_uuid=True), ForeignKey("exhibits.id"), nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.id}>'
