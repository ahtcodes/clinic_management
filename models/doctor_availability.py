from datetime import datetime

from extensions import db


class DoctorAvailability(db.Model):

    __tablename__ = "doctor_availability"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "doctors.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    weekday = db.Column(
        db.Integer,
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    appointment_duration = db.Column(
        db.Integer,
        nullable=False,
        default=20
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIP
    # =====================================================

    doctor = db.relationship(
        "Doctor",
        back_populates="availabilities"
    )

    def __repr__(self):

        return (
            f"<DoctorAvailability "
            f"Doctor={self.doctor_id} "
            f"Day={self.weekday} "
            f"{self.start_time}-{self.end_time}>"
        )