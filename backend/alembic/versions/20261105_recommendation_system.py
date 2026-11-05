"""Replace chatbot tables with recommendation embeddings."""

from alembic import op
import sqlalchemy as sa

revision = "20261105_recommendations"
down_revision = "588284b3c252"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # Drop chatbot tables only when they exist.
    # Child tables must be dropped before their parent tables.
    for table_name in (
        "chat_feedback",
        "chat_messages",
        "chat_sessions",
        "ai_queries",
    ):
        inspector = sa.inspect(bind)

        if inspector.has_table(table_name):
            op.drop_table(table_name)

    # Store JSON-serialized embedding vectors in a TEXT column.
    inspector = sa.inspect(bind)

    if inspector.has_table("ai_embeddings"):
        columns = inspector.get_columns("ai_embeddings")
        vector_column = next(
            (column for column in columns if column["name"] == "vector_ref"),
            None,
        )

        if vector_column and not isinstance(vector_column["type"], sa.Text):
            op.alter_column(
                "ai_embeddings",
                "vector_ref",
                existing_type=vector_column["type"],
                type_=sa.Text(),
                existing_nullable=False,
            )

def downgrade():
    op.alter_column(
        "ai_embeddings",
        "vector_ref",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=False,
    )

    op.create_table(
        "ai_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("query_text", sa.String(1000), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_ai_queries_created", "ai_queries", ["created_at"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("guest_token_hash", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_activity_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("guest_token_hash"),
    )
    op.create_index(
        "ix_chat_sessions_user_created",
        "chat_sessions",
        ["user_id", "created_at"],
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_chat_messages_session_created",
        "chat_messages",
        ["session_id", "created_at"],
    )

    op.create_table(
        "chat_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.String(20), nullable=False),
        sa.Column("comments", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["chat_messages.id"], ondelete="SET NULL"
        ),
    )
