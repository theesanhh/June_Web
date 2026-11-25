import sqlalchemy as sa
from alembic import op

revision = '0001_shop_settings'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    settings = op.create_table(
        'shop_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.String(200), nullable=False),
    )
    op.bulk_insert(settings, [{'key': 'shop_name', 'value': 'June'}])


def downgrade() -> None:
    op.drop_table('shop_settings')
