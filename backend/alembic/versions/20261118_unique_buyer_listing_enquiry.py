"""Ensure one enquiry thread per buyer and listing."""

import sqlalchemy as sa

from alembic import op

revision = "20261118_unique_enquiry"
down_revision = "20261117_close_reports"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    enquiries = sa.table(
        "enquiries",
        sa.column("id", sa.Integer),
        sa.column("listing_id", sa.Integer),
        sa.column("buyer_id", sa.Integer),
    )
    messages = sa.table(
        "enquiry_messages",
        sa.column("id", sa.Integer),
        sa.column("enquiry_id", sa.Integer),
    )

    # Preserve the oldest thread and move messages from duplicate threads into it.
    duplicate_groups = bind.execute(
        sa.select(
            enquiries.c.listing_id,
            enquiries.c.buyer_id,
        )
        .group_by(enquiries.c.listing_id, enquiries.c.buyer_id)
        .having(sa.func.count(enquiries.c.id) > 1)
    ).all()

    for listing_id, buyer_id in duplicate_groups:
        ids = bind.execute(
            sa.select(enquiries.c.id)
            .where(
                enquiries.c.listing_id == listing_id,
                enquiries.c.buyer_id == buyer_id,
            )
            .order_by(enquiries.c.id.asc())
        ).scalars().all()
        keep_id, duplicate_ids = ids[0], ids[1:]
        bind.execute(
            sa.update(messages)
            .where(messages.c.enquiry_id.in_(duplicate_ids))
            .values(enquiry_id=keep_id)
        )
        bind.execute(
            sa.delete(enquiries).where(enquiries.c.id.in_(duplicate_ids))
        )

    op.create_unique_constraint(
        "uq_enquiries_listing_buyer",
        "enquiries",
        ["listing_id", "buyer_id"],
    )


def downgrade():
    op.drop_constraint(
        "uq_enquiries_listing_buyer",
        "enquiries",
        type_="unique",
    )
