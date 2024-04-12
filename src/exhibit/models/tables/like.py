import uuid

from sqlalchemy import Column, UUID, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from exhibit.db import Base


class Like(Base):
    """
    The Like model

    """
    __tablename__ = "likes"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    exhibit_id = Column(UUID(as_uuid=True), ForeignKey("exhibits.id"), nullable=False)
    exhibit = relationship("models.tables.exhibit.Exhibit", back_populates="likes")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.id}>'
