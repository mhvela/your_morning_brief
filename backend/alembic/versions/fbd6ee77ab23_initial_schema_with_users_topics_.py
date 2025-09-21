"""Initial schema with users, topics, sources, articles

Revision ID: fbd6ee77ab23
Revises:
Create Date: 2025-09-21 20:14:00.160499

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fbd6ee77ab23"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create sources table
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("feed_url", sa.String(length=512), nullable=False),
        sa.Column("credibility_score", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(length=1024), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sources_feed_url"), "sources", ["feed_url"], unique=True)
    op.create_index(op.f("ix_sources_id"), "sources", ["id"], unique=False)
    op.create_index(op.f("ix_sources_url"), "sources", ["url"], unique=True)

    # Create topics table
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topics_id"), "topics", ["id"], unique=False)

    # Create articles table
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("link", sa.String(length=1024), nullable=False),
        sa.Column("summary_raw", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_content_hash", "articles", ["content_hash"], unique=False)
    op.create_index("idx_published_at", "articles", ["published_at"], unique=False)
    op.create_index(
        "idx_source_published", "articles", ["source_id", "published_at"], unique=False
    )
    op.create_index(
        op.f("ix_articles_content_hash"), "articles", ["content_hash"], unique=True
    )
    op.create_index(op.f("ix_articles_id"), "articles", ["id"], unique=False)

    # Create article_summaries table
    op.create_table(
        "article_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "model", name="uq_article_model"),
    )
    op.create_index(
        op.f("ix_article_summaries_id"), "article_summaries", ["id"], unique=False
    )

    # Create deliveries table
    op.create_table(
        "deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("delivery_date", sa.Date(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "topic_id", "delivery_date", "article_id", name="uq_topic_date_article"
        ),
        sa.UniqueConstraint(
            "topic_id", "delivery_date", "position", name="uq_topic_date_position"
        ),
    )
    op.create_index(op.f("ix_deliveries_id"), "deliveries", ["id"], unique=False)

    # Create feedback table
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("delivery_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.String(length=10), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["deliveries.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feedback_delivery_id"), "feedback", ["delivery_id"], unique=True
    )
    op.create_index(op.f("ix_feedback_id"), "feedback", ["id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("feedback")
    op.drop_table("deliveries")
    op.drop_table("article_summaries")
    op.drop_table("articles")
    op.drop_table("topics")
    op.drop_table("sources")
    op.drop_table("users")
