
from datetime import datetime

from extensions import db


class ActivityNotification(db.Model):

    __tablename__ = "activity_notifications"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # RECEIVER USER
    # =====================================================

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # =====================================================
    # ACTIVITY TYPE
    # =====================================================

    activity_type = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    # Examples:
    # message
    # order
    # appointment
    # prescription
    # consultation
    # billing
    # medicine
    # general

    # =====================================================
    # TITLE
    # =====================================================

    title = db.Column(
        db.String(200),
        nullable=False
    )

    # =====================================================
    # MESSAGE
    # =====================================================

    message = db.Column(
        db.Text,
        nullable=False
    )

    # =====================================================
    # REFERENCE ID
    # =====================================================

    reference_id = db.Column(
        db.Integer,
        nullable=True
    )

    # Example:
    # Order ID
    # Appointment ID
    # Prescription ID
    # Consultation ID
    # Message ID

    # =====================================================
    # REFERENCE TYPE
    # =====================================================

    reference_type = db.Column(
        db.String(50),
        nullable=True
    )

    # Example:
    # order
    # appointment
    # prescription
    # consultation
    # message

    # =====================================================
    # ACTION URL
    # =====================================================

    action_url = db.Column(
        db.String(500),
        nullable=True
    )

    # =====================================================
    # READ STATUS
    # =====================================================

    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    # =====================================================
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # =====================================================
    # RELATIONSHIP
    # =====================================================

    user = db.relationship(
        "User",
        backref=db.backref(
            "activity_notifications",
            lazy="dynamic"
        )
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<ActivityNotification "
            f"{self.id} "
            f"{self.activity_type} "
            f"{self.title}>"
        )

