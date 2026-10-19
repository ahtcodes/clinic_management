from datetime import datetime

from extensions import db


class MedicineDispense(db.Model):

    __tablename__ = "medicine_dispenses"

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
        nullable=False
    )

    # =====================================================
    # CONSULTATION
    # =====================================================

    consultation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "consultations.id",
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
            ondelete="CASCADE"
        ),
        nullable=False
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
    # QUANTITY
    # =====================================================

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    # =====================================================
    # DOSAGE
    # =====================================================

    dosage = db.Column(
        db.String(100),
        nullable=True
    )

    # =====================================================
    # FREQUENCY
    # =====================================================

    frequency = db.Column(
        db.String(100),
        nullable=True
    )

    # =====================================================
    # DURATION
    # =====================================================

    duration = db.Column(
        db.String(100),
        nullable=True
    )

    # =====================================================
    # INSTRUCTIONS
    # =====================================================

    instructions = db.Column(
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

    medicine = db.relationship(
        "Medicine",
        backref=db.backref(
            "dispenses",
            lazy=True
        )
    )

    consultation = db.relationship(
        "Consultation",
        backref=db.backref(
            "dispensed_medicines",
            cascade="all, delete-orphan",
            lazy=True
        )
    )

    patient = db.relationship(
        "Patient",
        backref=db.backref(
            "medicine_dispenses",
            lazy=True
        )
    )

    doctor = db.relationship(
        "Doctor",
        backref=db.backref(
            "medicine_dispenses",
            lazy=True
        )
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<MedicineDispense "
            f"{self.medicine_id} - "
            f"Patient {self.patient_id}>"
        )