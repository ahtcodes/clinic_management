"""Make patient_id nullable for online appointments

Revision ID: make_patient_nullable
Revises: 34df2acd7ecb
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "make_patient_nullable"
down_revision = "34df2acd7ecb"
branch_labels = None
depends_on = None


def upgrade():

    op.execute(
        "ALTER TABLE appointments "
        "ALTER COLUMN patient_id DROP NOT NULL"
    )


def downgrade():

    op.execute(
        "ALTER TABLE appointments "
        "ALTER COLUMN patient_id SET NOT NULL"
    )