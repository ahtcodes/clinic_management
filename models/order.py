from datetime import datetime

from extensions import db


class Order(db.Model):

    __tablename__ = "orders"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # ORDER CODE
    # =====================================================

    order_code = db.Column(
        db.String(30),
        unique=True,
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
    # These remain even after patient is deleted
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
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    # =====================================================
    # CONSULTATION
    # =====================================================

    consultation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "consultations.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =====================================================
    # PRESCRIPTION
    # =====================================================

    prescription_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "prescriptions.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =====================================================
    # ORDER STATUS
    # =====================================================

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    # =====================================================
    # TOTAL
    # =====================================================

    total_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = db.Column(
        db.Text,
        nullable=True
    )

    # =====================================================
    # DATES
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    confirmed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    cancelled_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    patient = db.relationship(
        "Patient",
        backref=db.backref(
            "orders",
            lazy=True,
            passive_deletes=True
        )
    )

    doctor = db.relationship(
        "Doctor",
        backref=db.backref(
            "orders",
            lazy=True
        )
    )

    consultation = db.relationship(
        "Consultation",
        backref=db.backref(
            "orders",
            lazy=True
        )
    )

    prescription = db.relationship(
        "Prescription",
        backref=db.backref(
            "orders",
            lazy=True
        )
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<Order "
            f"{self.order_code} "
            f"status={self.status}>"
        )


class OrderItem(db.Model):

    __tablename__ = "order_items"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # ORDER
    # =====================================================

    order_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "orders.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # MEDICINE
    # =====================================================

    medicine_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "medicines.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    # =====================================================
    # MEDICINE SNAPSHOT
    # =====================================================

    medicine_name = db.Column(
        db.String(150),
        nullable=False
    )

    unit = db.Column(
        db.String(50),
        nullable=False,
        default="Tablet"
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

    total_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    order = db.relationship(
        "Order",
        back_populates="items"
    )

    medicine = db.relationship(
        "Medicine",
        backref=db.backref(
            "order_items",
            lazy=True
        )
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<OrderItem "
            f"order_id={self.order_id} "
            f"medicine_id={self.medicine_id} "
            f"quantity={self.quantity}>"
        )