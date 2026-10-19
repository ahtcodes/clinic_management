
from datetime import datetime

from extensions import db


class Medicine(db.Model):

    __tablename__ = "medicines"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # DOCTOR
    # =====================================================

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "doctors.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # MEDICINE INFORMATION
    # =====================================================

    medicine_name = db.Column(
        db.String(150),
        nullable=False
    )

    generic_name = db.Column(
        db.String(150),
        nullable=True
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    strength = db.Column(
        db.String(100),
        nullable=True
    )

    unit = db.Column(
        db.String(50),
        nullable=False,
        default="Tablet"
    )

    # =====================================================
    # STOCK
    # =====================================================

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    # =====================================================
    # LEGACY / CURRENT PRICE
    # =====================================================

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # LEGACY / CURRENT EXPIRY
    # =====================================================

    expiry_date = db.Column(
        db.Date,
        nullable=True
    )

    # =====================================================
    # STATUS
    # =====================================================

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # =====================================================
    # BATCHES
    # =====================================================

    batches = db.relationship(
        "MedicineBatch",
        back_populates="medicine",
        cascade="all, delete-orphan",
        order_by="MedicineBatch.expiry_date.asc()"
    )

    # =====================================================
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    doctor = db.relationship(
        "Doctor",
        backref=db.backref(
            "medicines",
            cascade="all, delete-orphan",
            lazy=True
        )
    )

    provisions = db.relationship(
        "MedicineProvision",
        back_populates="medicine",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<Medicine "
            f"{self.medicine_name} - "
            f"Doctor {self.doctor_id}>"
        )

