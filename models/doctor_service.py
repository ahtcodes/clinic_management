from datetime import datetime

from extensions import db


class DoctorService(db.Model):

    __tablename__ = "doctor_services"

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
    # SERVICE NAME
    # =====================================================

    service_name = db.Column(
        db.String(150),
        nullable=False
    )

    # =====================================================
    # SERVICE FEE
    # =====================================================

    fee = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # =====================================================
    # ACTIVE / DISABLED
    # =====================================================

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # =====================================================
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # =====================================================
    # DOCTOR RELATIONSHIP
    # =====================================================

    doctor = db.relationship(
        "Doctor",
        back_populates="services"
    )

    # =====================================================
    # CONSULTATION SERVICES
    # =====================================================

    consultation_services = db.relationship(
        "ConsultationService",
        back_populates="doctor_service",
        lazy=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<DoctorService "
            f"{self.service_name} - "
            f"{self.fee}>"
        )