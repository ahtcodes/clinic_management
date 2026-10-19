from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.chat_conversation import ChatConversation
from models.chat_message import ChatMessage


patient_chat_bp = Blueprint(
    "patient_chat",
    __name__,
    url_prefix="/patient/chat"
)


# ============================================================
# GET LOGGED-IN PATIENT
# ============================================================

def get_logged_in_patient():
    if not current_user.is_authenticated:
        return None

    if not current_user.is_patient():
        return None

    if not current_user.patient_id:
        return None

    return Patient.query.get(current_user.patient_id)


# ============================================================
# GET PATIENT'S DOCTORS
# ============================================================

def get_patient_doctors(patient_id):

    appointments = (
        Appointment.query
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id.isnot(None)
        )
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        )
        .all()
    )

    doctors = []
    doctor_ids = set()

    for appointment in appointments:

        if not appointment.doctor:
            continue

        doctor = appointment.doctor

        if doctor.id in doctor_ids:
            continue

        doctor_ids.add(doctor.id)
        doctors.append(doctor)

    return doctors


# ============================================================
# PATIENT CHAT HOME
# ============================================================

@patient_chat_bp.route("/")
@login_required
def chat_home():

    patient = get_logged_in_patient()

    if not patient:
        flash(
            "Patient account is not properly linked.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    doctors = get_patient_doctors(patient.id)

    conversations = (
        ChatConversation.query
        .filter(
            ChatConversation.patient_id == patient.id
        )
        .order_by(
            ChatConversation.updated_at.desc()
        )
        .all()
    )

    return render_template(
        "chat/patient_chat.html",
        patient=patient,
        doctors=doctors,
        conversations=conversations,
        conversation=None,
        doctor=None,
        messages=[]
    )


# ============================================================
# OPEN CHAT WITH DOCTOR
# ============================================================

@patient_chat_bp.route("/doctor/<int:doctor_id>")
@login_required
def doctor_chat(doctor_id):

    patient = get_logged_in_patient()

    if not patient:
        flash(
            "Patient account is not properly linked.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    doctor = Doctor.query.get_or_404(doctor_id)

    # --------------------------------------------------------
    # SECURITY CHECK
    # Patient can only chat with a doctor
    # with whom the patient has an appointment.
    # --------------------------------------------------------

    appointment = (
        Appointment.query
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id == doctor.id
        )
        .first()
    )

    if not appointment:

        flash(
            "You can only chat with doctors you have an appointment with.",
            "danger"
        )

        return redirect(
            url_for("patient_chat.chat_home")
        )

    # --------------------------------------------------------
    # FIND EXISTING CONVERSATION
    # --------------------------------------------------------

    conversation = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        .first()
    )

    # --------------------------------------------------------
    # CREATE CONVERSATION IF NOT EXISTS
    # --------------------------------------------------------

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor.id,
            patient_id=patient.id
        )

        db.session.add(conversation)
        db.session.commit()

    # --------------------------------------------------------
    # GET MESSAGES
    # --------------------------------------------------------

    messages = (
        ChatMessage.query
        .filter_by(
            conversation_id=conversation.id
        )
        .order_by(
            ChatMessage.created_at.asc()
        )
        .all()
    )

    # --------------------------------------------------------
    # MARK DOCTOR MESSAGES AS READ
    # --------------------------------------------------------

    changed = False

    for message in messages:

        if (
            message.sender_type == "doctor"
            and not message.is_read
        ):
            message.is_read = True
            changed = True

    if changed:
        db.session.commit()

    # --------------------------------------------------------
    # GET ALL PATIENT DOCTORS
    # --------------------------------------------------------

    doctors = get_patient_doctors(patient.id)

    conversations = (
        ChatConversation.query
        .filter(
            ChatConversation.patient_id == patient.id
        )
        .order_by(
            ChatConversation.updated_at.desc()
        )
        .all()
    )

    return render_template(
        "chat/patient_chat.html",
        patient=patient,
        doctors=doctors,
        conversations=conversations,
        conversation=conversation,
        doctor=doctor,
        messages=messages
    )


# ============================================================
# SEND MESSAGE TO DOCTOR
# ============================================================

@patient_chat_bp.route(
    "/doctor/<int:doctor_id>/send",
    methods=["POST"]
)
@login_required
def send_message(doctor_id):

    patient = get_logged_in_patient()

    if not patient:

        flash(
            "Patient account is not properly linked.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    doctor = Doctor.query.get_or_404(doctor_id)

    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    appointment = (
        Appointment.query
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id == doctor.id
        )
        .first()
    )

    if not appointment:

        flash(
            "You can only message your own doctors.",
            "danger"
        )

        return redirect(
            url_for("patient_chat.chat_home")
        )

    # --------------------------------------------------------
    # GET MESSAGE
    # --------------------------------------------------------

    message_text = request.form.get(
        "message",
        ""
    ).strip()

    if not message_text:

        flash(
            "Message cannot be empty.",
            "warning"
        )

        return redirect(
            url_for(
                "patient_chat.doctor_chat",
                doctor_id=doctor.id
            )
        )

    # --------------------------------------------------------
    # FIND / CREATE CONVERSATION
    # --------------------------------------------------------

    conversation = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        .first()
    )

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor.id,
            patient_id=patient.id
        )

        db.session.add(conversation)
        db.session.flush()

    # --------------------------------------------------------
    # CREATE MESSAGE
    # --------------------------------------------------------

    message = ChatMessage(
        conversation_id=conversation.id,
        sender_type="patient",
        sender_id=patient.id,
        message=message_text,
        is_read=False
    )

    db.session.add(message)

    # Update conversation timestamp
    conversation.updated_at = db.func.now()

    db.session.commit()

    return redirect(
        url_for(
            "patient_chat.doctor_chat",
            doctor_id=doctor.id
        )
    )