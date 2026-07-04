"""Review dismissal: status/dismissed_at/dismissed_by on review_schedules.

Additive only. Existing rows backfill to status='active' via the server
default, so the reviews-due queue is unchanged until an admin dismisses a row.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "review_schedules",
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
    )
    op.add_column("review_schedules", sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("review_schedules", sa.Column("dismissed_by", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("review_schedules", "dismissed_by")
    op.drop_column("review_schedules", "dismissed_at")
    op.drop_column("review_schedules", "status")
