"""Record who closed moderation reports and when."""
import sqlalchemy as sa

from alembic import op

revision = "20261117_close_reports"
down_revision = "20261117_activity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reports", sa.Column("closed_by", sa.Integer(), nullable=True))
    op.add_column("reports", sa.Column("closed_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_reports_closed_by_users", "reports", "users", ["closed_by"], ["id"], ondelete="SET NULL")


def downgrade():
    op.drop_constraint("fk_reports_closed_by_users", "reports", type_="foreignkey")
    op.drop_column("reports", "closed_at")
    op.drop_column("reports", "closed_by")
