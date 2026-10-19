from datetime import datetime

from extensions import db


class MedicineProvision(db.Model):

    __tablename__ = "medicine_provisions"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # BATCH
    # =====================================================

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "medicine_batches.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # =====================================================
    # ORDER ITEM
    # =====================================================

    order_item_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "order_items.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
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
        nullable=False
    )

    # =====================================================
    # PATIENT
    # =====================================================

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "patients.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # =====================================================
    # PATIENT SNAPSHOT
    # These remain after patient deletion
    # =====================================================

    patient_name = db.Column(
        db.String(150),
        nullable=True
    )

    patient_code = db.Column(
        db.String(20),
        nullable=True
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
    # BILL
    # =====================================================

    bill_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "bills.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =====================================================
    # QUANTITY
    # =====================================================

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    # =====================================================
    # PRICE
    # =====================================================

    unit_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    total_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # PROVISION STATUS
    # =====================================================

    provision_status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    payment_status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = db.Column(
        db.Text,
        nullable=True
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    medicine = db.relationship(
        "Medicine",
        back_populates="provisions"
    )

    batch = db.relationship(
        "MedicineBatch",
        back_populates="provisions"
    )

    order_item = db.relationship(
        "OrderItem",
        backref=db.backref(
            "medicine_provisions",
            lazy=True
        )
    )

    patient = db.relationship(
        "Patient",
        backref=db.backref(
            "medicine_provisions",
            lazy=True,
            passive_deletes=True
        )
    )

    doctor = db.relationship(
        "Doctor",
        back_populates="medicine_provisions"
    )

    bill = db.relationship(
        "Bill",
        backref=db.backref(
            "medicine_provisions",
            lazy=True
        )
    )

    # =====================================================
    # DATES
    # =====================================================

    provided_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    paid_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<MedicineProvision "
            f"id={self.id} "
            f"medicine_id={self.medicine_id} "
            f"patient_id={self.patient_id} "
            f"status={self.provision_status} "
            f"payment={self.payment_status}>"
        )