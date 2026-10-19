from datetime import datetime

from extensions import db


class Consultation(db.Model):

    __tablename__ = "consultations"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # CONSULTATION CODE
    # =====================================================

    consultation_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    # =====================================================
    # APPOINTMENT
    # =====================================================

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "appointments.id",
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
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    # =====================================================
    # SYMPTOMS
    # =====================================================

    symptoms = db.Column(
        db.Text,
        nullable=True
    )

    # =====================================================
    # BLOOD PRESSURE
    # =====================================================

    blood_pressure = db.Column(
        db.String(20),
        nullable=True
    )

    # =====================================================
    # TEMPERATURE
    # =====================================================

    temperature = db.Column(
        db.String(20),
        nullable=True
    )

    # =====================================================
    # TEMPERATURE CHECK
    # =====================================================

    temperature_checked = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    # =====================================================
    # TEMPERATURE FEE
    # =====================================================

    temperature_fee = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # =====================================================
    # WEIGHT
    # =====================================================

    weight = db.Column(
        db.String(20),
        nullable=True
    )

    # =====================================================
    # DIAGNOSIS
    # =====================================================

    diagnosis = db.Column(
        db.Text,
        nullable=True
    )

    # =====================================================
    # CLINICAL NOTES
    # =====================================================

    clinical_notes = db.Column(
        db.Text,
        nullable=True
    )

    # =====================================================
    # TREATMENT NOTES
    # =====================================================

    treatment_notes = db.Column(
        db.Text,
        nullable=True
    )

    # =====================================================
    # FOLLOW UP DATE
    # =====================================================

    follow_up_date = db.Column(
        db.Date,
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

    appointment = db.relationship(
        "Appointment",
        back_populates="consultation"
    )

    patient = db.relationship(
        "Patient",
        back_populates="consultations"
    )

    doctor = db.relationship(
        "Doctor",
        backref="consultations"
    )

    # =====================================================
    # PRESCRIPTIONS
    # =====================================================

    prescriptions = db.relationship(
        "Prescription",
        back_populates="consultation",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # =====================================================
    # ADDITIONAL SERVICES
    # =====================================================

    services = db.relationship(
        "ConsultationService",
        back_populates="consultation",
        cascade="all, delete-orphan",
        lazy=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<Consultation "
            f"{self.consultation_code}>"
        )