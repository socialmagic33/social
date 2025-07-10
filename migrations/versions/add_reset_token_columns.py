"""Add reset token columns

Revision ID: add_reset_token_columns
Create Date: 2024-01-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_reset_token_columns'
down_revision = 'add_media_processing_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add reset token columns
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))
    
    # Add indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_media_user_id', 'media', ['user_id'])
    op.create_index('idx_media_jobsite_id', 'media', ['jobsite_id'])
    op.create_index('idx_posts_user_id', 'posts', ['user_id'])
    op.create_index('idx_posts_scheduled_for', 'posts', ['scheduled_for'])

def downgrade():
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'reset_token_expires')
    
    op.drop_index('idx_users_email')
    op.drop_index('idx_media_user_id')
    op.drop_index('idx_media_jobsite_id')
    op.drop_index('idx_posts_user_id')
    op.drop_index('idx_posts_scheduled_for')