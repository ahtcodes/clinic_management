from datetime import datetime, timezone

from extensions import db


class ChatMessage(db.Model):

    __tablename__ = "chat_messages"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # CONVERSATION
    # =====================================================

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "chat_conversations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # SENDER TYPE
    # =====================================================

    sender_type = db.Column(
        db.String(20),
        nullable=False
    )

    # =====================================================
    # SENDER ID
    # =====================================================

    sender_id = db.Column(
        db.Integer,
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
    # READ STATUS
    # =====================================================

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    # =====================================================
    # CREATED AT
    # =====================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # =====================================================
    # RELATIONSHIP
    # =====================================================

    conversation = db.relationship(
        "ChatConversation",
        back_populates="messages"
    )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"<ChatMessage "
            f"{self.id} - "
            f"{self.sender_type}:{self.sender_id}>"
        )
