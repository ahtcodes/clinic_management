from datetime import datetime

from extensions import db


class Prescription(db.Model):

    __tablename__ = "prescriptions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    prescription_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    consultation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "consultations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "patients.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    medicine_name = db.Column(
        db.String(200),
        nullable=False
    )

    dosage = db.Column(
        db.String(100),
        nullable=True
    )

    frequency = db.Column(
        db.String(100),
        nullable=True
    )

    duration = db.Column(
        db.String(100),
        nullable=True
    )

    instructions = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    consultation = db.relationship(
        "Consultation",
        back_populates="prescriptions"
    )

    patient = db.relationship(
        "Patient",
        back_populates="prescriptions"
    )

    doctor = db.relationship(
        "Doctor",
        backref="prescriptions"
    )

    def __repr__(self):

        return f"<Prescription {self.prescription_code}>"