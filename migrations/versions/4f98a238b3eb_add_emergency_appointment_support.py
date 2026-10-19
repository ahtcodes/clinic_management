"""Add emergency appointment support

Revision ID: 4f98a238b3eb
Revises: 8f3e323fec73
Create Date: 2026-08-24
"""

from alembic import op
import sqlalchemy as sa


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision = "4f98a238b3eb"

down_revision = "8f3e323fec73"

branch_labels = None

depends_on = None


# =========================================================
# UPGRADE
# =========================================================

def upgrade():

    with op.batch_alter_table(
        "appointments",
        schema=None
    ) as batch_op:

        # -------------------------------------------------
        # APPOINTMENT TYPE
        # -------------------------------------------------

        batch_op.add_column(
            sa.Column(
                "appointment_type",
                sa.String(length=20),
                nullable=False,
                server_default="NORMAL"
            )
        )

        # -------------------------------------------------
        # EMERGENCY FLAG
        # -------------------------------------------------

        batch_op.add_column(
            sa.Column(
                "is_emergency",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false")
            )
        )

        # -------------------------------------------------
        # EMERGENCY PRIORITY
        # -------------------------------------------------

        batch_op.add_column(
            sa.Column(
                "emergency_priority",
                sa.String(length=20),
                nullable=True
            )
        )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade():

    with op.batch_alter_table(
        "appointments",
        schema=None
    ) as batch_op:

        # -------------------------------------------------
        # REMOVE EMERGENCY PRIORITY
        # -------------------------------------------------

        batch_op.drop_column(
            "emergency_priority"
        )

        # -------------------------------------------------
        # REMOVE EMERGENCY FLAG
        # -------------------------------------------------

        batch_op.drop_column(
            "is_emergency"
        )

        # -------------------------------------------------
        # REMOVE APPOINTMENT TYPE
        # -------------------------------------------------

        batch_op.drop_column(
            "appointment_type"
        )