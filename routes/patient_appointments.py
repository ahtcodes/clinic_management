from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from models.patient import Patient
from models.appointment import Appointment


# ============================================================
# PATIENT APPOINTMENTS BLUEPRINT
# ============================================================

patient_appointments_bp = Blueprint(
    "patient_appointments",
    __name__,
    url_prefix="/patient/appointments"
)


# ============================================================
# GET LOGGED-IN PATIENT
# ============================================================

def get_logged_in_patient():
    """
    Return the Patient record linked with the
    currently logged-in patient account.
    """

    if not current_user.is_authenticated:
        return None

    if not current_user.is_patient():
        return None

    if not current_user.patient_id:
        return None

    return Patient.query.get(current_user.patient_id)


# ============================================================
# MY APPOINTMENTS
# ============================================================

@patient_appointments_bp.route("/")
@login_required
def my_appointments():

    # --------------------------------------------------------
    # Get logged-in patient
    # --------------------------------------------------------

    patient = get_logged_in_patient()

    if not patient:
        flash(
            "Patient account is not properly linked.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # IMPORTANT:
    # Only fetch appointments belonging to this patient
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Appointment statistics
    # --------------------------------------------------------

    total_appointments = len(appointments)

    completed_appointments = sum(
        1
        for appointment in appointments
        if appointment.status
        and appointment.status.lower()
        in [
            "completed",
            "complete",
            "done"
        ]
    )

    cancelled_appointments = sum(
        1
        for appointment in appointments
        if appointment.status
        and appointment.status.lower()
        in [
            "cancelled",
            "canceled"
        ]
    )

    scheduled_appointments = sum(
        1
        for appointment in appointments
        if appointment.status
        and appointment.status.lower()
        in [
            "scheduled",
            "confirmed",
            "pending"
        ]
    )

    # --------------------------------------------------------
    # Render page
    # --------------------------------------------------------

    return render_template(
        "patients/my_appointments.html",

        patient=patient,

        appointments=appointments,

        total_appointments=total_appointments,
        scheduled_appointments=scheduled_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments
    )