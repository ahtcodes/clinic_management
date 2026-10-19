
"""Add medicine batches

Revision ID: 14df95d2b7c5
Revises: c0d7afbc6eda
Create Date: 2026-09-02 16:06:51.201324
"""

from alembic import op
import sqlalchemy as sa


# =========================================================
# ALEMBIC REVISION
# =========================================================

revision = "14df95d2b7c5"
down_revision = "c0d7afbc6eda"
branch_labels = None
depends_on = None


# =========================================================
# UPGRADE
# =========================================================

def upgrade():

    # =====================================================
    # CREATE MEDICINE BATCHES TABLE
    # =====================================================

    op.create_table(
        "medicine_batches",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            "medicine_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "batch_number",
            sa.String(100),
            nullable=False
        ),

        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default="0"
        ),

        sa.Column(
            "price",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0"
        ),

        sa.Column(
            "expiry_date",
            sa.Date(),
            nullable=True
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true()
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["medicine_id"],
            ["medicines.id"],
            ondelete="CASCADE"
        ),

        sa.UniqueConstraint(
            "medicine_id",
            "batch_number",
            name="uq_medicine_batch_number"
        )
    )

    # =====================================================
    # INDEXES
    # =====================================================

    op.create_index(
        "ix_medicine_batches_medicine_id",
        "medicine_batches",
        ["medicine_id"]
    )

    op.create_index(
        "ix_medicine_batches_expiry_date",
        "medicine_batches",
        ["expiry_date"]
    )

    # =====================================================
    # ADD BATCH_ID TO MEDICINE PROVISIONS
    # =====================================================

    op.add_column(
        "medicine_provisions",
        sa.Column(
            "batch_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_index(
        "ix_medicine_provisions_batch_id",
        "medicine_provisions",
        ["batch_id"]
    )

    op.create_foreign_key(
        "fk_medicine_provisions_batch_id",
        "medicine_provisions",
        "medicine_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL"
    )

    # =====================================================
    # MIGRATE EXISTING MEDICINES
    # ONE OLD MEDICINE = ONE LEGACY BATCH
    # =====================================================

    connection = op.get_bind()

    medicines = connection.execute(
        sa.text("""
            SELECT
                id,
                quantity,
                price,
                expiry_date
            FROM medicines
        """)
    ).fetchall()

    for medicine in medicines:

        connection.execute(
            sa.text("""
                INSERT INTO medicine_batches
                (
                    medicine_id,
                    batch_number,
                    quantity,
                    price,
                    expiry_date,
                    is_active,
                    created_at
                )
                VALUES
                (
                    :medicine_id,
                    :batch_number,
                    :quantity,
                    :price,
                    :expiry_date,
                    TRUE,
                    CURRENT_TIMESTAMP
                )
            """),
            {
                "medicine_id": medicine.id,
                "batch_number": f"LEGACY-{medicine.id}",
                "quantity": medicine.quantity or 0,
                "price": medicine.price or 0,
                "expiry_date": medicine.expiry_date
            }
        )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade():

    op.drop_constraint(
        "fk_medicine_provisions_batch_id",
        "medicine_provisions",
        type_="foreignkey"
    )

    op.drop_index(
        "ix_medicine_provisions_batch_id",
        table_name="medicine_provisions"
    )

    op.drop_column(
        "medicine_provisions",
        "batch_id"
    )

    op.drop_index(
        "ix_medicine_batches_expiry_date",
        table_name="medicine_batches"
    )

    op.drop_index(
        "ix_medicine_batches_medicine_id",
        table_name="medicine_batches"
    )

    op.drop_table(
        "medicine_batches"
    )

