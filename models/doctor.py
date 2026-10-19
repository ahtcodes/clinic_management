from datetime import datetime

from extensions import db


class Doctor(db.Model):

    __tablename__ = "doctors"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # DOCTOR CODE
    # =====================================================

    doctor_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    specialization = db.Column(
        db.String(150)
    )

    phone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(150)
    )

    qualification = db.Column(
        db.String(200)
    )

    # =====================================================
    # CONSULTATION FEE
    # =====================================================

    consultation_fee = db.Column(
        db.Numeric(10, 2),
        default=0
    )

    # =====================================================
    # ROOM
    # =====================================================

    room_number = db.Column(
        db.String(30)
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
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # DOCTOR AVAILABILITY
    # =====================================================

    availabilities = db.relationship(
        "DoctorAvailability",
        back_populates="doctor",
        cascade="all, delete-orphan",
        lazy=True
    )

    # =====================================================
    # DOCTOR SERVICES
    #
    # Example:
    # Blood Pressure Check = 50 PKR
    # Blood Sugar Test     = 100 PKR
    # Nebulization         = 200 PKR
    # =====================================================

    services = db.relationship(
        "DoctorService",
        back_populates="doctor",
        cascade="all, delete-orphan",
        lazy=True
    )

    # =====================================================
    # APPOINTMENTS
    # =====================================================

    appointments = db.relationship(
        "Appointment",
        back_populates="doctor",
        lazy=True
    )

    # =====================================================
    # MEDICINE PROVISIONS
    # =====================================================

    medicine_provisions = db.relationship(
        "MedicineProvision",
        back_populates="doctor",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<Doctor "
            f"{self.doctor_code} - "
            f"{self.full_name}>"
        )