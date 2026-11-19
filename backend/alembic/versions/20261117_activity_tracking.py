"""Add private search and listing-view signals for recommendations."""

import sqlalchemy as sa

from alembic import op

revision = "20261117_activity"
down_revision = "20261105_recommendations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("normalized_query", sa.String(length=200), nullable=False),
        sa.Column(
            "search_count", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "last_searched_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "normalized_query", name="uq_search_history_user_query"
        ),
    )
    op.create_index(
        "ix_search_history_user_recent",
        "search_history",
        ["user_id", "last_searched_at"],
    )

    op.create_table(
        "listing_views",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "first_viewed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_viewed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["listing_id"], ["listings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "listing_id"),
    )
    op.create_index(
        "ix_listing_views_user_recent",
        "listing_views",
        ["user_id", "last_viewed_at"],
    )


def downgrade():
    op.drop_index("ix_listing_views_user_recent", table_name="listing_views")
    op.drop_table("listing_views")
    op.drop_index("ix_search_history_user_recent", table_name="search_history")
    op.drop_table("search_history")
