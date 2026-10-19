from datetime import datetime

from extensions import db


class ChatConversation(db.Model):

    __tablename__ = "chat_conversations"

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
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # UPDATED AT
    # =====================================================

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    doctor = db.relationship(
        "Doctor",
        backref=db.backref(
            "chat_conversations",
            lazy=True
        )
    )

    patient = db.relationship(
        "Patient",
        back_populates="chat_conversations"
    )

    # =====================================================
    # MESSAGES
    # =====================================================

    messages = db.relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.created_at",
        lazy=True
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<ChatConversation "
            f"{self.id}: "
            f"Doctor {self.doctor_id} - "
            f"Patient {self.patient_id}>"
        )