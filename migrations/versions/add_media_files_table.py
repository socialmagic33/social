"""Add media files table for database storage

Revision ID: add_media_files_table
Revises: add_reset_token_columns
Create Date: 2024-01-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_media_files_table'
down_revision = 'add_reset_token_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Create media_files table for storing file data
    op.create_table(
        'media_files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index for faster lookups
    op.create_index('idx_media_files_created_at', 'media_files', ['created_at'])

def downgrade():
    op.drop_index('idx_media_files_created_at')
    op.drop_table('media_files')