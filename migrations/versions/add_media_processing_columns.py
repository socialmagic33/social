"""Add media processing columns

Revision ID: add_media_processing_columns
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_media_processing_columns'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Add JSON columns for processed URLs and metadata
    op.add_column('media', sa.Column('processed_urls', postgresql.JSON, nullable=True))
    op.add_column('media', sa.Column('metadata', postgresql.JSON, nullable=True))

def downgrade():
    op.drop_column('media', 'processed_urls')
    op.drop_column('media', 'metadata')