from datetime import datetime

from extensions import db


class Appointment(db.Model):

    __tablename__ = "appointments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # APPOINTMENT CODE
    # =====================================================

    appointment_code = db.Column(
        db.String(20),
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
        nullable=True
    )

    # =====================================================
    # DOCTOR
    # =====================================================

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "doctors.id"
        ),
        nullable=False
    )

    # =====================================================
    # DATE & TIME
    # =====================================================

    appointment_date = db.Column(
        db.Date,
        nullable=False
    )

    appointment_time = db.Column(
        db.Time,
        nullable=False
    )

    # =====================================================
    # APPOINTMENT TYPE
    # Normal / Emergency
    # =====================================================

    appointment_type = db.Column(
        db.String(20),
        nullable=False,
        default="Normal"
    )

    # =====================================================
    # EMERGENCY
    # =====================================================

    is_emergency = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    emergency_priority = db.Column(
        db.String(20),
        nullable=False,
        default="Normal"
    )

    # =====================================================
    # REASON
    # =====================================================

    reason = db.Column(
        db.Text
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Scheduled"
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = db.Column(
        db.Text
    )

    # =====================================================
    # ONLINE APPOINTMENT
    # =====================================================

    is_online = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    patient_name = db.Column(
        db.String(150)
    )

    patient_phone = db.Column(
        db.String(30)
    )

    patient_email = db.Column(
        db.String(150)
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
        back_populates="appointments"
    )

    doctor = db.relationship(
        "Doctor",
        back_populates="appointments"
    )

    consultation = db.relationship(
        "Consultation",
        back_populates="appointment",
        uselist=False
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        appointment_type = (
            "Emergency"
            if self.is_emergency
            else "Normal"
        )

        return (
            f"<Appointment "
            f"{self.appointment_code} "
            f"{appointment_type}>"
        )