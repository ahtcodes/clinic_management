from datetime import datetime

from extensions import db


class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # USER
    # =====================================================

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
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
            "appointments.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    # =====================================================
    # NOTIFICATION CONTENT
    # =====================================================

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        default="general"
    )

    # =====================================================
    # READ STATUS
    # =====================================================

    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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

    user = db.relationship(
        "User",
        backref=db.backref(
            "notifications",
            lazy="dynamic"
        )
    )

    appointment = db.relationship(
        "Appointment",
        backref=db.backref(
            "notifications",
            lazy="dynamic"
        )
    )

    def __repr__(self):

        return (
            f"<Notification "
            f"{self.id} "
            f"{self.title}>"
        )