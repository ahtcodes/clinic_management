from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import date

from models.patient import Patient
from models.appointment import Appointment
from models.bill import Bill
from models.doctor import Doctor
from models.consultation import Consultation
from models.prescription import Prescription


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard_bp.route("/")
@login_required
def dashboard():

    today = date.today()
    role = current_user.role

    # =====================================================
    # SUPER ADMIN DASHBOARD
    # =====================================================

    if role == "super_admin":

        total_patients = Patient.query.count()

        today_appointments = Appointment.query.filter(
            Appointment.appointment_date == today
        ).count()

        today_patients = (
            Appointment.query
            .filter(
                Appointment.appointment_date == today,
                Appointment.patient_id.isnot(None)
            )
            .with_entities(
                Appointment.patient_id
            )
            .distinct()
            .count()
        )

        today_bills = Bill.query.filter(
            Bill.created_at >= today
        ).all()

        today_revenue = sum(
            float(bill.total_amount or 0)
            for bill in today_bills
        )

        total_doctors = Doctor.query.count()
        total_users = 0

        try:
            from models.user import User
            total_users = User.query.count()
        except Exception:
            total_users = 0

        return render_template(
            "dashboard/index.html",

            dashboard_role="super_admin",

            total_patients=total_patients,
            today_appointments=today_appointments,
            today_patients=today_patients,
            today_revenue=today_revenue,

            total_doctors=total_doctors,
            total_users=total_users
        )

    # =====================================================
    # RECEPTIONIST DASHBOARD
    # =====================================================

    if role == "receptionist":

        total_patients = Patient.query.count()

        today_appointments = Appointment.query.filter(
            Appointment.appointment_date == today
        ).count()

        today_patients = (
            Appointment.query
            .filter(
                Appointment.appointment_date == today,
                Appointment.patient_id.isnot(None)
            )
            .with_entities(
                Appointment.patient_id
            )
            .distinct()
            .count()
        )

        today_bills = Bill.query.filter(
            Bill.created_at >= today
        ).all()

        today_revenue = sum(
            float(bill.total_amount or 0)
            for bill in today_bills
        )

        total_doctors = Doctor.query.count()

        return render_template(
            "dashboard/index.html",

            dashboard_role="receptionist",

            total_patients=total_patients,
            today_appointments=today_appointments,
            today_patients=today_patients,
            today_revenue=today_revenue,

            total_doctors=total_doctors
        )

    # =====================================================
    # DOCTOR DASHBOARD
    # =====================================================

    if role == "doctor":

        doctor = getattr(current_user, "doctor", None)

        doctor_id = doctor.id if doctor else None

        if doctor_id:

            today_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == today
            ).count()

            total_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id
            ).count()

            today_patients = (
                Appointment.query
                .filter(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_date == today,
                    Appointment.patient_id.isnot(None)
                )
                .with_entities(
                    Appointment.patient_id
                )
                .distinct()
                .count()
            )

            doctor_patients = (
                Appointment.query
                .filter(
                    Appointment.doctor_id == doctor_id,
                    Appointment.patient_id.isnot(None)
                )
                .with_entities(
                    Appointment.patient_id
                )
                .distinct()
                .count()
            )

            doctor_consultations = Consultation.query.filter(
                Consultation.doctor_id == doctor_id
            ).count()

            doctor_prescriptions = Prescription.query.filter(
                Prescription.doctor_id == doctor_id
            ).count()

        else:

            today_appointments = 0
            total_appointments = 0
            today_patients = 0
            doctor_patients = 0
            doctor_consultations = 0
            doctor_prescriptions = 0

        return render_template(
            "dashboard/index.html",

            dashboard_role="doctor",

            today_appointments=today_appointments,
            total_appointments=total_appointments,
            today_patients=today_patients,
            doctor_patients=doctor_patients,
            doctor_consultations=doctor_consultations,
            doctor_prescriptions=doctor_prescriptions,

            doctor=doctor
        )

    # =====================================================
    # STAFF DASHBOARD
    # =====================================================

    if role == "staff":

        total_patients = Patient.query.count()

        today_appointments = Appointment.query.filter(
            Appointment.appointment_date == today
        ).count()

        today_patients = (
            Appointment.query
            .filter(
                Appointment.appointment_date == today,
                Appointment.patient_id.isnot(None)
            )
            .with_entities(
                Appointment.patient_id
            )
            .distinct()
            .count()
        )

        total_doctors = Doctor.query.count()

        total_consultations = Consultation.query.count()
        total_prescriptions = Prescription.query.count()

        return render_template(
            "dashboard/index.html",

            dashboard_role="staff",

            total_patients=total_patients,
            today_appointments=today_appointments,
            today_patients=today_patients,

            total_doctors=total_doctors,
            total_consultations=total_consultations,
            total_prescriptions=total_prescriptions
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    return render_template(
        "dashboard/index.html",
        dashboard_role=role
    )