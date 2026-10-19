
from datetime import datetime

from extensions import db


class Bill(db.Model):

    __tablename__ = "bills"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # BILL CODE
    # =====================================================

    bill_code = db.Column(
        db.String(50),
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
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # APPOINTMENT
    # =====================================================

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "appointments.id"
        ),
        nullable=True
    )

    # =====================================================
    # CONSULTATION FEE
    # =====================================================

    consultation_fee = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # SERVICE FEE
    #
    # Total of selected Consultation Services
    # e.g. Injection, Dressing, Nebulization, etc.
    # =====================================================

    service_fee = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # MEDICINE FEE
    # =====================================================

    medicine_fee = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # LABORATORY FEE
    # =====================================================

    laboratory_fee = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # OTHER CHARGES
    # =====================================================

    other_charges = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # DISCOUNT
    # =====================================================

    discount = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # TOTAL
    # =====================================================

    total_amount = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # PAID
    # =====================================================

    paid_amount = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # REMAINING
    # =====================================================

    remaining_amount = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    payment_status = db.Column(
        db.String(20),
        default="Unpaid",
        nullable=False
    )

    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    payment_method = db.Column(
        db.String(30),
        default="Cash",
        nullable=False
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = db.Column(
        db.Text,
        nullable=True
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

    patient = db.relationship(
        "Patient",
        back_populates="bills"
    )

    appointment = db.relationship(
        "Appointment",
        backref="bills"
    )

    # =====================================================
    # CALCULATE TOTAL
    # =====================================================

    def calculate_total(self):

        # =================================================
        # GET CHARGES
        # =================================================

        consultation_fee = (
            self.consultation_fee or 0
        )

        service_fee = (
            self.service_fee or 0
        )

        medicine_fee = (
            self.medicine_fee or 0
        )

        laboratory_fee = (
            self.laboratory_fee or 0
        )

        other_charges = (
            self.other_charges or 0
        )

        discount = (
            self.discount or 0
        )

        paid_amount = (
            self.paid_amount or 0
        )

        # =================================================
        # SUBTOTAL
        #
        # Consultation
        # + Services
        # + Medicine
        # + Laboratory
        # + Other Charges
        #
        # Temperature Fee is NOT included.
        # =================================================

        subtotal = (

            consultation_fee

            + service_fee

            + medicine_fee

            + laboratory_fee

            + other_charges

        )

        # =================================================
        # TOTAL AFTER DISCOUNT
        # =================================================

        self.total_amount = max(
            subtotal - discount,
            0
        )

        # =================================================
        # REMAINING
        # =================================================

        self.remaining_amount = max(
            self.total_amount - paid_amount,
            0
        )

        # =================================================
        # PAYMENT STATUS
        # =================================================

        if paid_amount <= 0:

            self.payment_status = "Unpaid"

        elif paid_amount < self.total_amount:

            self.payment_status = "Partial"

        else:

            self.payment_status = "Paid"

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<Bill {self.bill_code}>"
        )

