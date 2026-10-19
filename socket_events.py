
from flask import request, url_for
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from extensions import socketio, db

from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.chat_conversation import ChatConversation
from models.chat_message import ChatMessage
from models.activity_notification import ActivityNotification
from models.user import User


# =========================================================
# ROOM NAME HELPERS
# =========================================================

def conversation_room(conversation_id):
    return f"conversation_{conversation_id}"


def user_room(user_id):
    return f"user_{user_id}"


# =========================================================
# GET LOGGED-IN PATIENT
# =========================================================

def get_logged_in_patient_id():

    if not current_user.is_authenticated:
        return None

    if not current_user.is_patient():
        return None

    if not current_user.patient_id:
        return None

    return current_user.patient_id


# =========================================================
# GET LOGGED-IN DOCTOR
# =========================================================

def get_logged_in_doctor_id():

    if not current_user.is_authenticated:
        return None

    if not current_user.is_doctor():
        return None

    if not current_user.doctor_id:
        return None

    return current_user.doctor_id


# =========================================================
# CHECK DOCTOR-PATIENT RELATIONSHIP
# =========================================================

def doctor_patient_relationship(doctor_id, patient_id):

    return (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient_id
        )
        .first()
    )


# =========================================================
# JOIN USER NOTIFICATION ROOM
# =========================================================
#
# IMPORTANT:
# We do NOT use a connect() handler here.
# This prevents the Socket.IO connection from being rejected.
#
# base.html should emit:
#
# socket.emit("join_notification_room");
#
# =========================================================

@socketio.on("join_notification_room")
def handle_join_notification_room():

    if not current_user.is_authenticated:
        return

    room = user_room(current_user.id)

    join_room(room)

    print(
        f"Notification room joined: {room}"
    )


# =========================================================
# JOIN CONVERSATION
# =========================================================

@socketio.on("join_conversation")
def handle_join_conversation(data):

    if not current_user.is_authenticated:

        emit(
            "chat_error",
            {
                "message": "You must be logged in."
            }
        )

        return

    try:

        conversation_id = int(
            data.get("conversation_id")
        )

    except (TypeError, ValueError):

        emit(
            "chat_error",
            {
                "message": "Invalid conversation."
            }
        )

        return

    conversation = ChatConversation.query.get(
        conversation_id
    )

    if not conversation:

        emit(
            "chat_error",
            {
                "message": "Conversation not found."
            }
        )

        return

    doctor_id = get_logged_in_doctor_id()
    patient_id = get_logged_in_patient_id()

    # -----------------------------------------------------
    # DOCTOR ACCESS
    # -----------------------------------------------------

    if doctor_id:

        if conversation.doctor_id != doctor_id:

            emit(
                "chat_error",
                {
                    "message": "You cannot access this conversation."
                }
            )

            return

    # -----------------------------------------------------
    # PATIENT ACCESS
    # -----------------------------------------------------

    elif patient_id:

        if conversation.patient_id != patient_id:

            emit(
                "chat_error",
                {
                    "message": "You cannot access this conversation."
                }
            )

            return

    else:

        emit(
            "chat_error",
            {
                "message": "Invalid user."
            }
        )

        return

    room = conversation_room(
        conversation.id
    )

    join_room(room)

    print(
        f"User {current_user.id} joined {room}"
    )

    emit(
        "conversation_joined",
        {
            "conversation_id": conversation.id
        }
    )


# =========================================================
# LEAVE CONVERSATION
# =========================================================

@socketio.on("leave_conversation")
def handle_leave_conversation(data):

    try:

        conversation_id = int(
            data.get("conversation_id")
        )

    except (TypeError, ValueError):

        return

    room = conversation_room(
        conversation_id
    )

    leave_room(room)


# =========================================================
# SEND MESSAGE
# =========================================================

@socketio.on("send_message")
def handle_send_message(data):

    # -----------------------------------------------------
    # AUTHENTICATION
    # -----------------------------------------------------

    if not current_user.is_authenticated:

        emit(
            "chat_error",
            {
                "message": "You must be logged in."
            }
        )

        return

    # -----------------------------------------------------
    # GET CONVERSATION ID
    # -----------------------------------------------------

    try:

        conversation_id = int(
            data.get("conversation_id")
        )

    except (TypeError, ValueError):

        emit(
            "chat_error",
            {
                "message": "Invalid conversation."
            }
        )

        return

    # -----------------------------------------------------
    # GET MESSAGE
    # -----------------------------------------------------

    message_text = (
        data.get("message", "")
        .strip()
    )

    if not message_text:

        emit(
            "chat_error",
            {
                "message": "Message cannot be empty."
            }
        )

        return

    # -----------------------------------------------------
    # GET CONVERSATION
    # -----------------------------------------------------

    conversation = ChatConversation.query.get(
        conversation_id
    )

    if not conversation:

        emit(
            "chat_error",
            {
                "message": "Conversation not found."
            }
        )

        return

    doctor_id = get_logged_in_doctor_id()
    patient_id = get_logged_in_patient_id()

    # -----------------------------------------------------
    # DETERMINE SENDER
    # -----------------------------------------------------

    if doctor_id:

        if conversation.doctor_id != doctor_id:

            emit(
                "chat_error",
                {
                    "message": "You cannot send messages here."
                }
            )

            return

        sender_type = "doctor"
        sender_id = doctor_id

    elif patient_id:

        if conversation.patient_id != patient_id:

            emit(
                "chat_error",
                {
                    "message": "You cannot send messages here."
                }
            )

            return

        sender_type = "patient"
        sender_id = patient_id

    else:

        emit(
            "chat_error",
            {
                "message": "Invalid user."
            }
        )

        return

    # -----------------------------------------------------
    # EXTRA SECURITY
    # -----------------------------------------------------

    relationship = doctor_patient_relationship(
        conversation.doctor_id,
        conversation.patient_id
    )

    if not relationship:

        emit(
            "chat_error",
            {
                "message": "Doctor and patient are not connected."
            }
        )

        return

    # =====================================================
    # CREATE MESSAGE
    # =====================================================

    message = ChatMessage(
        conversation_id=conversation.id,
        sender_type=sender_type,
        sender_id=sender_id,
        message=message_text,
        is_read=False
    )

    db.session.add(message)

    conversation.updated_at = db.func.now()

    # =====================================================
    # GET DOCTOR + PATIENT
    # =====================================================

    patient = Patient.query.get(
        conversation.patient_id
    )

    doctor = Doctor.query.get(
        conversation.doctor_id
    )

    # =====================================================
    # CREATE NOTIFICATION
    # =====================================================

    notification = None

    # =====================================================
    # PATIENT → DOCTOR
    # =====================================================

    if sender_type == "patient":

        doctor_user = (
            User.query
            .filter(
                User.doctor_id == conversation.doctor_id,
                User.role.ilike("doctor")
            )
            .first()
        )

        if doctor_user and patient:

            patient_name = (
                patient.full_name
                if getattr(
                    patient,
                    "full_name",
                    None
                )
                else "Patient"
            )

            notification = ActivityNotification(
                user_id=doctor_user.id,
                activity_type="chat_message",
                title="New Patient Message",
                message=(
                    f"{patient_name} sent you "
                    f"a new message."
                ),
                reference_id=patient.id,
                reference_type="patient",
                action_url=url_for(
                    "chat.doctor_chat",
                    patient_id=patient.id
                ),
                is_read=False
            )

            db.session.add(notification)

            print(
                "Creating notification for doctor:",
                doctor_user.id
            )

    # =====================================================
    # DOCTOR → PATIENT
    # =====================================================

    elif sender_type == "doctor":

        patient_user = (
            User.query
            .filter(
                User.patient_id == conversation.patient_id,
                User.role.ilike("patient")
            )
            .first()
        )

        if patient_user and doctor:

            doctor_name = (
                doctor.full_name
                if getattr(
                    doctor,
                    "full_name",
                    None
                )
                else "Doctor"
            )

            # ---------------------------------------------
            # PATIENT KO SIRF DOCTOR KA NAAM DIKHAYEGA
            # ---------------------------------------------

            notification = ActivityNotification(
                user_id=patient_user.id,
                activity_type="chat_message",
                title="New Doctor Message",
                message=(
                    f"Dr. {doctor_name} "
                    f"sent you a new message."
                ),
                reference_id=doctor.id,
                reference_type="doctor",
                action_url=url_for(
                    "chat.patient_chat",
                    doctor_id=doctor.id
                ),
                is_read=False
            )

            db.session.add(notification)

            print(
                "Creating notification for patient:",
                patient_user.id
            )

    # =====================================================
    # SINGLE DATABASE COMMIT
    # =====================================================

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "CHAT SAVE ERROR:",
            e
        )

        emit(
            "chat_error",
            {
                "message": "Unable to send message."
            }
        )

        return

    # =====================================================
    # MESSAGE DATA
    # =====================================================

    message_data = {
        "id": message.id,
        "conversation_id": conversation.id,
        "sender_type": message.sender_type,
        "sender_id": message.sender_id,
        "message": message.message,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat()
    }

    # =====================================================
    # SEND MESSAGE TO CONVERSATION
    # =====================================================

    emit(
        "new_message",
        message_data,
        room=conversation_room(
            conversation.id
        )
    )

    # =====================================================
    # SEND REAL-TIME NOTIFICATION
    # =====================================================

    if notification:

        notification_data = {
            "id": notification.id,
            "user_id": notification.user_id,
            "activity_type": notification.activity_type,
            "title": notification.title,
            "message": notification.message,
            "reference_id": notification.reference_id,
            "reference_type": notification.reference_type,
            "action_url": notification.action_url,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.isoformat()
            )
        }

        print(
            "========================================"
        )

        print(
            "ACTIVITY NOTIFICATION"
        )

        print(
            "Receiver User ID:",
            notification.user_id
        )

        print(
            "Notification Room:",
            user_room(
                notification.user_id
            )
        )

        print(
            "Notification:",
            notification_data
        )

        print(
            "========================================"
        )

        socketio.emit(
            "activity_notification",
            notification_data,
            room=user_room(
                notification.user_id
            )
        )


# =========================================================
# MARK MESSAGE AS READ
# =========================================================

@socketio.on("mark_messages_read")
def handle_mark_messages_read(data):

    if not current_user.is_authenticated:

        return

    try:

        conversation_id = int(
            data.get("conversation_id")
        )

    except (TypeError, ValueError):

        return

    conversation = ChatConversation.query.get(
        conversation_id
    )

    if not conversation:

        return

    doctor_id = get_logged_in_doctor_id()
    patient_id = get_logged_in_patient_id()

    # -----------------------------------------------------
    # VERIFY ACCESS
    # -----------------------------------------------------

    if doctor_id:

        if conversation.doctor_id != doctor_id:

            return

        sender_type_to_mark = "patient"

    elif patient_id:

        if conversation.patient_id != patient_id:

            return

        sender_type_to_mark = "doctor"

    else:

        return

    # -----------------------------------------------------
    # MARK UNREAD MESSAGES
    # -----------------------------------------------------

    messages = (
        ChatMessage.query
        .filter(
            ChatMessage.conversation_id == conversation.id,
            ChatMessage.sender_type == sender_type_to_mark,
            ChatMessage.is_read.is_(False)
        )
        .all()
    )

    if not messages:

        return

    for message in messages:

        message.is_read = True

    db.session.commit()

    # -----------------------------------------------------
    # NOTIFY CHAT ROOM
    # -----------------------------------------------------

    emit(
        "messages_read",
        {
            "conversation_id": conversation.id,
            "reader_type": (
                "doctor"
                if doctor_id
                else "patient"
            )
        },
        room=conversation_room(
            conversation.id
        )
    )
