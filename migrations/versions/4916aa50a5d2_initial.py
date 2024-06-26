"""initial

Revision ID: 4916aa50a5d2
Revises: 
Create Date: 2024-04-12 22:41:01.180801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4916aa50a5d2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('content', sa.VARCHAR(length=1000), nullable=False),
    sa.Column('state', sa.Enum('DELETED', 'PUBLISHED', name='commentstate'), nullable=True),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exhibits',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=255), nullable=False),
    sa.Column('poster', sa.UUID(), nullable=True),
    sa.Column('content', sa.VARCHAR(length=32000), nullable=False),
    sa.Column('state', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', 'DELETED', name='exhibitstate'), nullable=True),
    sa.Column('views', sa.BIGINT(), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('type', sa.Enum('COMMENT_ANSWER', name='notificationtype'), nullable=True),
    sa.Column('content_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.VARCHAR(length=64), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tags',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('comment_tree',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('ancestor_id', sa.UUID(), nullable=False),
    sa.Column('descendant_id', sa.UUID(), nullable=False),
    sa.Column('nearest_ancestor_id', sa.UUID(), nullable=True),
    sa.Column('exhibit_id', sa.UUID(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['exhibit_id'], ['exhibits.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exhibit_tags',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('exhibit_id', sa.UUID(), nullable=False),
    sa.Column('tag_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['exhibit_id'], ['exhibits.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('files',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.VARCHAR(length=255), nullable=False),
    sa.Column('exhibit_id', sa.UUID(), nullable=False),
    sa.Column('content_type', sa.VARCHAR(length=255), nullable=False),
    sa.Column('is_uploaded', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['exhibit_id'], ['exhibits.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('likes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('exhibit_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['exhibit_id'], ['exhibits.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('likes')
    op.drop_table('files')
    op.drop_table('exhibit_tags')
    op.drop_table('comment_tree')
    op.drop_table('tags')
    op.drop_table('notifications')
    op.drop_table('exhibits')
    op.drop_table('comments')
    # ### end Alembic commands ###
