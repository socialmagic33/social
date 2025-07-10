"""Initial schema

Revision ID: initial_schema
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verification_token', sa.String(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('values', sa.String(), nullable=True),
        sa.Column('specialties', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), server_default='free_trial'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create jobsites table
    op.create_table(
        'jobsites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create media_groupings table
    op.create_table(
        'media_groupings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jobsite_id', sa.Integer(), nullable=False),
        sa.Column('generated_caption', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['jobsite_id'], ['jobsites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create media table
    op.create_table(
        'media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('star_rating', sa.Integer(), nullable=True),
        sa.Column('earliest_upload', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('before', 'in_progress', 'after', name='mediastatus'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('jobsite_id', sa.Integer(), nullable=False),
        sa.Column('grouping_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['grouping_id'], ['media_groupings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['jobsite_id'], ['jobsites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create social_accounts table
    op.create_table(
        'social_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('account_id', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create posts table
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('jobsite_id', sa.Integer(), nullable=False),
        sa.Column('grouping_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'not_scheduled', 'scheduled', 'published', name='poststatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['grouping_id'], ['media_groupings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['jobsite_id'], ['jobsites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grouping_id')
    )

def downgrade():
    op.drop_table('posts')
    op.drop_table('social_accounts')
    op.drop_table('media')
    op.drop_table('media_groupings')
    op.drop_table('jobsites')
    op.drop_table('users')
    op.execute('DROP TYPE mediastatus')
    op.execute('DROP TYPE poststatus')