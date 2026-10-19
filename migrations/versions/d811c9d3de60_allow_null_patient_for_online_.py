"""Allow null patient for online appointments

Revision ID: d811c9d3de60
Revises: make_patient_nullable
Create Date: 2026-08-21 16:52:40.092253

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d811c9d3de60"
down_revision = "make_patient_nullable"
branch_labels = None
depends_on = None


def upgrade():

    op.alter_column(
        "appointments",
        "patient_id",
        existing_type=sa.INTEGER(),
        nullable=True
    )


def downgrade():

    op.alter_column(
        "appointments",
        "patient_id",
        existing_type=sa.INTEGER(),
        nullable=False
    )