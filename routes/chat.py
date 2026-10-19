from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import (
    login_required,
    current_user
)

from extensions import db

from models.patient import Patient
from models.appointment import Appointment
from models.chat_conversation import ChatConversation
from models.chat_message import ChatMessage
from models.activity_notification import ActivityNotification
from models.user import User


chat_bp = Blueprint(
    "chat",
    __name__,
    url_prefix="/chat"
)


# =========================================================
# GET LOGGED-IN DOCTOR ID
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
# GET DOCTOR'S PATIENTS
# =========================================================

def get_doctor_patients(doctor_id):

    appointments = (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id.isnot(None)
        )
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        )
        .all()
    )

    patients = []

    patient_ids = set()

    for appointment in appointments:

        if not appointment.patient:
            continue

        patient = appointment.patient

        if patient.id in patient_ids:
            continue

        patient_ids.add(patient.id)

        patients.append(patient)

    return patients


# =========================================================
# DOCTOR CHAT HOME
# =========================================================

@chat_bp.route("/")
@login_required
def chat_home():

    doctor_id = get_logged_in_doctor_id()

    if not doctor_id:

        flash(
            "Only doctors can access the chat system.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    patients = get_doctor_patients(
        doctor_id
    )

    conversations = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor_id
        )
        .order_by(
            ChatConversation.updated_at.desc()
        )
        .all()
    )

    return render_template(
        "chat/doctor_chat.html",
        patients=patients,
        conversations=conversations
    )


# =========================================================
# OPEN DOCTOR CHAT
# =========================================================

@chat_bp.route(
    "/doctor/<int:patient_id>"
)
@login_required
def doctor_chat(patient_id):

    doctor_id = get_logged_in_doctor_id()

    if not doctor_id:

        flash(
            "Only doctors can access the chat system.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    # -----------------------------------------------------
    # GET PATIENT
    # -----------------------------------------------------

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # CHECK DOCTOR-PATIENT RELATIONSHIP
    # -----------------------------------------------------

    appointment = (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient.id
        )
        .first()
    )

    if not appointment:

        flash(
            "This patient is not associated with you.",
            "danger"
        )

        return redirect(
            url_for("chat.chat_home")
        )

    # -----------------------------------------------------
    # FIND CONVERSATION
    # -----------------------------------------------------

    conversation = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor_id,
            patient_id=patient.id
        )
        .first()
    )

    # -----------------------------------------------------
    # CREATE CONVERSATION
    # -----------------------------------------------------

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor_id,
            patient_id=patient.id
        )

        db.session.add(
            conversation
        )

        db.session.commit()

    # -----------------------------------------------------
    # GET MESSAGES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # MARK PATIENT MESSAGES AS READ
    # -----------------------------------------------------

    changed = False

    for msg in messages:

        if (
            msg.sender_type == "patient"
            and not msg.is_read
        ):

            msg.is_read = True

            changed = True

    if changed:

        ActivityNotification.query.filter_by(
            user_id=current_user.id,
            activity_type="chat_message",
            reference_type="patient",
            reference_id=patient.id,
            is_read=False
        ).update(
        {
            "is_read": True
        },
        synchronize_session=False
    )

    db.session.commit()

    # -----------------------------------------------------
    # GET ALL PATIENTS
    # -----------------------------------------------------

    patients = get_doctor_patients(
        doctor_id
    )

    # -----------------------------------------------------
    # GET ALL CONVERSATIONS
    # -----------------------------------------------------

    conversations = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor_id
        )
        .order_by(
            ChatConversation.updated_at.desc()
        )
        .all()
    )

    return render_template(
        "chat/doctor_chat.html",
        patients=patients,
        conversations=conversations,
        conversation=conversation,
        patient=patient,
        messages=messages
    )


# =========================================================
# DOCTOR SEND MESSAGE
# =========================================================

@chat_bp.route(
    "/doctor/<int:patient_id>/send",
    methods=["POST"]
)
@login_required
def send_message(patient_id):

    doctor_id = get_logged_in_doctor_id()

    if not doctor_id:

        flash(
            "Only doctors can send messages.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    # -----------------------------------------------------
    # GET PATIENT
    # -----------------------------------------------------

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # CHECK DOCTOR-PATIENT RELATIONSHIP
    # -----------------------------------------------------

    appointment = (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient.id
        )
        .first()
    )

    if not appointment:

        flash(
            "You can only message your own patients.",
            "danger"
        )

        return redirect(
            url_for("chat.chat_home")
        )

    # -----------------------------------------------------
    # GET MESSAGE
    # -----------------------------------------------------

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
                "chat.doctor_chat",
                patient_id=patient.id
            )
        )

    # -----------------------------------------------------
    # FIND CONVERSATION
    # -----------------------------------------------------

    conversation = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor_id,
            patient_id=patient.id
        )
        .first()
    )

    # -----------------------------------------------------
    # CREATE CONVERSATION IF NEEDED
    # -----------------------------------------------------

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor_id,
            patient_id=patient.id
        )

        db.session.add(
            conversation
        )

        db.session.flush()

    # -----------------------------------------------------
    # CREATE DOCTOR MESSAGE
    # -----------------------------------------------------

    message = ChatMessage(
        conversation_id=conversation.id,
        sender_type="doctor",
        sender_id=doctor_id,
        message=message_text,
        is_read=False
    )

    db.session.add(
        message
    )

    # -----------------------------------------------------
    # UPDATE CONVERSATION
    # -----------------------------------------------------

    conversation.updated_at = db.func.now()

    # -----------------------------------------------------
    # FIND PATIENT USER ACCOUNT
    # -----------------------------------------------------

    patient_user = (
        User.query
        .filter_by(
            patient_id=patient.id
        )
        .first()
    )

    # -----------------------------------------------------
    # CREATE NOTIFICATION FOR PATIENT
    # -----------------------------------------------------

    if patient_user:

        doctor_name = (
            current_user.username
            if getattr(current_user, "username", None)
            else "Doctor"
        )

        notification = ActivityNotification(
            user_id=patient_user.id,
            activity_type="chat_message",
            title="New Doctor Message",
            message=f"{doctor_name} sent you a new message.",
            reference_id=doctor_id,
            reference_type="doctor",
            action_url=url_for(
                "chat.patient_chat",
                doctor_id=doctor_id
            ),
            is_read=False
        )

        db.session.add(
            notification
        )

    # -----------------------------------------------------
    # SAVE MESSAGE + NOTIFICATION
    # -----------------------------------------------------

    db.session.commit()

    # -----------------------------------------------------
    # BACK TO DOCTOR CHAT
    # -----------------------------------------------------

    return redirect(
        url_for(
            "chat.doctor_chat",
            patient_id=patient.id
        )
    )


# =========================================================
# PATIENT CHAT HELPERS
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
# GET PATIENT'S DOCTORS
# =========================================================

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

        if not doctor.is_active:
            continue

        if doctor.id in doctor_ids:
            continue

        doctor_ids.add(
            doctor.id
        )

        doctors.append(
            doctor
        )

    return doctors


# =========================================================
# PATIENT CHAT HOME
# =========================================================

@chat_bp.route(
    "/patient/"
)
@login_required
def patient_chat_home():

    patient_id = get_logged_in_patient_id()

    if not patient_id:

        flash(
            "Only patients can access the patient chat.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # GET PATIENT
    # -----------------------------------------------------

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # GET PATIENT'S DOCTORS
    # -----------------------------------------------------

    doctors = get_patient_doctors(
        patient_id
    )

    # -----------------------------------------------------
    # GET PATIENT CONVERSATIONS
    # -----------------------------------------------------

    conversations = (
        ChatConversation.query
        .filter_by(
            patient_id=patient_id
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
        conversations=conversations
    )


# =========================================================
# PATIENT OPEN DOCTOR CHAT
# =========================================================

@chat_bp.route(
    "/patient/doctor/<int:doctor_id>"
)
@login_required
def patient_chat(doctor_id):

    patient_id = get_logged_in_patient_id()

    if not patient_id:

        flash(
            "Only patients can access the patient chat.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # GET PATIENT
    # -----------------------------------------------------

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # CHECK PATIENT-DOCTOR RELATIONSHIP
    # -----------------------------------------------------

    appointment = (
        Appointment.query
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id
        )
        .first()
    )

    if not appointment:

        flash(
            "You can only chat with your own doctors.",
            "danger"
        )

        return redirect(
            url_for("chat.patient_chat_home")
        )

    # -----------------------------------------------------
    # GET DOCTOR
    # -----------------------------------------------------

    doctor = appointment.doctor

    if not doctor:

        flash(
            "Doctor not found.",
            "danger"
        )

        return redirect(
            url_for("chat.patient_chat_home")
        )

    # -----------------------------------------------------
    # FIND CONVERSATION
    # -----------------------------------------------------

    conversation = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor.id,
            patient_id=patient_id
        )
        .first()
    )

    # -----------------------------------------------------
    # CREATE CONVERSATION
    # -----------------------------------------------------

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor.id,
            patient_id=patient_id
        )

        db.session.add(
            conversation
        )

        db.session.commit()

    # -----------------------------------------------------
    # GET MESSAGES
    # -----------------------------------------------------

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

   

      # =========================================================
    # MARK DOCTOR MESSAGES AS READ
    # =========================================================

    for message in messages:

        if (
            message.sender_type == "doctor"
            and not message.is_read
        ):

            message.is_read = True


    # =========================================================
    # MARK CHAT NOTIFICATIONS AS READ
    # =========================================================

    ActivityNotification.query.filter(
        ActivityNotification.user_id == current_user.id,
        ActivityNotification.activity_type == "chat_message",
        ActivityNotification.reference_type == "doctor",
        ActivityNotification.reference_id == doctor.id,
        ActivityNotification.is_read.is_(False)
    ).update(
        {
            "is_read": True
        },
        synchronize_session=False
    )


    # ----------------------------------------------------
    # SAVE READ STATUS
    # ----------------------------------------------------

    db.session.commit()  
    # -----------------------------------------------------
    # GET ALL PATIENT DOCTORS
    # -----------------------------------------------------

    doctors = get_patient_doctors(
        patient_id
    )

    # -----------------------------------------------------
    # GET ALL PATIENT CONVERSATIONS
    # -----------------------------------------------------

    conversations = (
        ChatConversation.query
        .filter_by(
            patient_id=patient_id
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
        doctor=doctor,
        conversation=conversation,
        messages=messages
    )


# =========================================================
# PATIENT SEND MESSAGE
# =========================================================

@chat_bp.route(
    "/patient/doctor/<int:doctor_id>/send",
    methods=["POST"]
)
@login_required
def patient_send_message(doctor_id):

    patient_id = get_logged_in_patient_id()

    if not patient_id:

        flash(
            "Only patients can send messages.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # CHECK PATIENT-DOCTOR RELATIONSHIP
    # -----------------------------------------------------

    appointment = (
        Appointment.query
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id
        )
        .first()
    )

    if not appointment:

        flash(
            "You can only message your own doctors.",
            "danger"
        )

        return redirect(
            url_for("chat.patient_chat_home")
        )

    # -----------------------------------------------------
    # GET DOCTOR
    # -----------------------------------------------------

    doctor = appointment.doctor

    if not doctor:

        flash(
            "Doctor not found.",
            "danger"
        )

        return redirect(
            url_for("chat.patient_chat_home")
        )

    # -----------------------------------------------------
    # GET PATIENT
    # -----------------------------------------------------

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # GET MESSAGE
    # -----------------------------------------------------

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
                "chat.patient_chat",
                doctor_id=doctor.id
            )
        )

    # -----------------------------------------------------
    # FIND CONVERSATION
    # -----------------------------------------------------

    conversation = (
        ChatConversation.query
        .filter_by(
            doctor_id=doctor.id,
            patient_id=patient_id
        )
        .first()
    )

    # -----------------------------------------------------
    # CREATE CONVERSATION IF NEEDED
    # -----------------------------------------------------

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor.id,
            patient_id=patient_id
        )

        db.session.add(
            conversation
        )

        db.session.flush()

    # -----------------------------------------------------
    # CREATE PATIENT MESSAGE
    # -----------------------------------------------------

    message = ChatMessage(
        conversation_id=conversation.id,
        sender_type="patient",
        sender_id=patient_id,
        message=message_text,
        is_read=False
    )

    db.session.add(
        message
    )

    # -----------------------------------------------------
    # UPDATE CONVERSATION
    # -----------------------------------------------------

    conversation.updated_at = db.func.now()

    # -----------------------------------------------------
    # FIND DOCTOR USER ACCOUNT
    # -----------------------------------------------------

    doctor_user = (
        User.query
        .filter(
            User.doctor_id == doctor.id,
            User.role.ilike("doctor")
        )
        .first()
    )

    # -----------------------------------------------------
    # DEBUG INFORMATION
    # -----------------------------------------------------

    print("========================================")
    print("PATIENT SEND MESSAGE DEBUG")
    print("Patient ID:", patient_id)
    print("Doctor ID:", doctor.id)
    print("Doctor User:", doctor_user)

    if doctor_user:

        print(
            "Doctor User ID:",
            doctor_user.id
        )

        print(
            "Doctor Username:",
            doctor_user.username
        )

        print(
            "Doctor Linked Doctor ID:",
            doctor_user.doctor_id
        )

    else:

        print(
            "DOCTOR USER NOT FOUND"
        )

    print("========================================")

    # -----------------------------------------------------
    # CREATE NOTIFICATION FOR DOCTOR
    # -----------------------------------------------------

    if doctor_user:

        patient_name = (
            patient.full_name
            if getattr(patient, "full_name", None)
            else "Patient"
        )

        notification = ActivityNotification(
            user_id=doctor_user.id,
            activity_type="chat_message",
            title="New Patient Message",
            message=f"{patient_name} sent you a new message.",
            reference_id=patient.id,
            reference_type="patient",
            action_url=url_for(
                "chat.doctor_chat",
                patient_id=patient.id
            ),
            is_read=False
        )

        db.session.add(
            notification
        )

    # -----------------------------------------------------
    # SAVE MESSAGE + NOTIFICATION
    # -----------------------------------------------------

    db.session.commit()

    # -----------------------------------------------------
    # BACK TO PATIENT CHAT
    # -----------------------------------------------------

    return redirect(
        url_for(
            "chat.patient_chat",
            doctor_id=doctor.id
        )
    )