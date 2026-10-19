from datetime import datetime

from extensions import db


class ConsultationService(db.Model):

    __tablename__ = "consultation_services"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    consultation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "consultations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    doctor_service_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "doctor_services.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # Snapshot of the service name
    # so old bills remain correct even if doctor edits service later
    service_name = db.Column(
        db.String(150),
        nullable=False
    )

    # Snapshot of the fee at the time of consultation
    service_fee = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    consultation = db.relationship(
        "Consultation",
        back_populates="services"
    )

    doctor_service = db.relationship(
        "DoctorService",
        back_populates="consultation_services"
    )

    def __repr__(self):

        return (
            f"<ConsultationService "
            f"{self.service_name} - "
            f"{self.service_fee}>"
        )