
from datetime import datetime

from extensions import db


class MedicineBatch(db.Model):

    __tablename__ = "medicine_batches"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # MEDICINE
    # =====================================================

    medicine_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "medicines.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # =====================================================
    # BATCH NUMBER
    # =====================================================

    batch_number = db.Column(
        db.String(100),
        nullable=False
    )

     # =====================================================
     # supplier name
     # =====================================================

    supplier_name = db.Column(
    db.String(200),
    nullable=True
    )


    # =====================================================
    # QUANTITY
    # =====================================================

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    # =====================================================
    # PURCHASE PRICE
    # =====================================================

    purchase_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # SELLING PRICE
    # =====================================================

    selling_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # EXPIRY DATE
    # =====================================================

    expiry_date = db.Column(
        db.Date,
        nullable=True,
        index=True
    )

    # =====================================================
    # ACTIVE
    # =====================================================

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # =====================================================
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    medicine = db.relationship(
        "Medicine",
        back_populates="batches"
    )

    provisions = db.relationship(
        "MedicineProvision",
        back_populates="batch",
        passive_deletes=True
    )

    # =====================================================
    # UNIQUE CONSTRAINT
    # =====================================================

    __table_args__ = (
        db.UniqueConstraint(
            "medicine_id",
            "batch_number",
            name="uq_medicine_batch_number"
        ),
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<MedicineBatch "
            f"{self.medicine_id} "
            f"{self.batch_number}>"
        )


