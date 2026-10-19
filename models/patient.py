from datetime import datetime

from extensions import db


class Patient(db.Model):

    __tablename__ = "patients"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    father_name = db.Column(
        db.String(150)
    )

    gender = db.Column(
        db.String(20)
    )

    date_of_birth = db.Column(
        db.Date
    )

    phone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(150)
    )

    address = db.Column(
        db.Text
    )

    blood_group = db.Column(
        db.String(10)
    )

    emergency_contact = db.Column(
        db.String(30)
    )

    medical_history = db.Column(
        db.Text
    )

    allergies = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    appointments = db.relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    consultations = db.relationship(
        "Consultation",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    prescriptions = db.relationship(
        "Prescription",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    bills = db.relationship(
        "Bill",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    chat_conversations = db.relationship(
        "ChatConversation",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):

        return (
            f"<Patient "
            f"{self.patient_code} - "
            f"{self.full_name}>"
        )