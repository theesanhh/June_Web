import sqlalchemy as sa
from alembic import op

revision = '0002_admin'
down_revision = '0001_shop_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'admin_account',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('password_hash', sa.String(128), nullable=False),
        sa.CheckConstraint('id = 1', name='only_one_admin'),
    )
    op.create_table(
        'admin_sessions',
        sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('expires_at', sa.Integer, nullable=False),
    )
    op.create_index('ix_admin_sessions_expires_at', 'admin_sessions', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_admin_sessions_expires_at', table_name='admin_sessions')
    op.drop_table('admin_sessions')
    op.drop_table('admin_account')
