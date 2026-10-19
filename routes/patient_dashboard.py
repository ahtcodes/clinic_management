from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash
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


patient_dashboard_bp = Blueprint(
    "patient_dashboard",
    __name__,
    url_prefix="/patient"
)


# =========================================================
# GET LOGGED-IN PATIENT
# =========================================================

def get_logged_in_patient():

    if not current_user.is_authenticated:
        return None

    if not current_user.is_patient():
        return None

    if not current_user.patient_id:
        return None

    patient = Patient.query.get(
        current_user.patient_id
    )

    return patient


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@patient_dashboard_bp.route("/")
@login_required
def dashboard():

    # =====================================================
    # CHECK PATIENT
    # =====================================================

    patient = get_logged_in_patient()

    if not patient:

        flash(
            "Patient account is not properly linked.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # =====================================================
    # CURRENT DATE / TIME
    # =====================================================

    now = datetime.now()

    today = now.date()

    current_time = now.time()

    # =====================================================
    # ALL PATIENT APPOINTMENTS
    #
    # IMPORTANT:
    # Only appointments belonging to the logged-in
    # patient are loaded.
    # =====================================================

    appointments = (
        Appointment.query
        .filter(
            Appointment.patient_id == patient.id
        )
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        )
        .all()
    )

    # =====================================================
    # APPOINTMENT COUNTS
    # =====================================================

    total_appointments = len(
        appointments
    )

    completed_appointments = sum(
        1
        for appointment in appointments
        if appointment.status
        and appointment.status.lower()
        in ["completed", "complete", "done"]
    )

    cancelled_appointments = sum(
        1
        for appointment in appointments
        if appointment.status
        and appointment.status.lower()
        in ["cancelled", "canceled"]
    )

    scheduled_appointments = sum(
        1
        for appointment in appointments
        if appointment.status
        and appointment.status.lower()
        in ["scheduled", "confirmed", "pending"]
    )

    # =====================================================
    # UPCOMING APPOINTMENTS
    # =====================================================

    upcoming_appointments = []

    for appointment in appointments:

        if not appointment.appointment_date:
            continue

        status = (
            appointment.status.lower()
            if appointment.status
            else ""
        )

        if status in [
            "cancelled",
            "canceled",
            "completed",
            "complete",
            "done"
        ]:
            continue

        appointment_date = (
            appointment.appointment_date
        )

        appointment_time = (
            appointment.appointment_time
        )

        # Future date
        if appointment_date > today:

            upcoming_appointments.append(
                appointment
            )

        # Today
        elif appointment_date == today:

            if (
                appointment_time
                and appointment_time >= current_time
            ):

                upcoming_appointments.append(
                    appointment
                )

            elif not appointment_time:

                upcoming_appointments.append(
                    appointment
                )

    # =====================================================
    # SORT UPCOMING APPOINTMENTS
    # =====================================================

    upcoming_appointments.sort(
        key=lambda appointment: (
            appointment.appointment_date,
            appointment.appointment_time
            if appointment.appointment_time
            else datetime.min.time()
        )
    )

    # Only show next 5
    upcoming_appointments = (
        upcoming_appointments[:5]
    )

    # =====================================================
    # RECENT APPOINTMENTS
    # =====================================================

    recent_appointments = (
        appointments[:5]
    )

    # =====================================================
    # UNREAD DOCTOR MESSAGES
    # =====================================================

    unread_messages = (
        ChatMessage.query
        .join(
            ChatConversation,
            ChatMessage.conversation_id
            == ChatConversation.id
        )
        .filter(
            ChatConversation.patient_id == patient.id,
            ChatMessage.sender_type == "doctor",
            ChatMessage.is_read.is_(False)
        )
        .count()
    )

    # =====================================================
    # TOTAL CHAT CONVERSATIONS
    # =====================================================

    total_conversations = (
        ChatConversation.query
        .filter(
            ChatConversation.patient_id == patient.id
        )
        .count()
    )

    # =====================================================
    # DOCTORS
    #
    # Get unique doctors from patient's appointments.
    # =====================================================

    doctors = []

    doctor_ids = set()

    for appointment in appointments:

        if not appointment.doctor:
            continue

        doctor = appointment.doctor

        if doctor.id in doctor_ids:
            continue

        doctor_ids.add(
            doctor.id
        )

        doctors.append(
            doctor
        )

    # =====================================================
    # DOCTOR COUNT
    # =====================================================

    total_doctors = len(
        doctors
    )

    # =====================================================
    # RENDER DASHBOARD
    # =====================================================

    return render_template(
        "patients/dashboard.html",

        patient=patient,

        appointments=appointments,

        upcoming_appointments=upcoming_appointments,

        recent_appointments=recent_appointments,

        doctors=doctors,

        total_appointments=total_appointments,

        scheduled_appointments=scheduled_appointments,

        completed_appointments=completed_appointments,

        cancelled_appointments=cancelled_appointments,

        unread_messages=unread_messages,

        total_conversations=total_conversations,

        total_doctors=total_doctors
    )