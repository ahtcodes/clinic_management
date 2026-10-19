from datetime import datetime, timedelta, date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from extensions import db

from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.doctor_availability import DoctorAvailability
from models.notification import Notification
from models.user import User

from utils.permissions import role_required


appointments_bp = Blueprint(
    "appointments",
    __name__,
    url_prefix="/appointments"
)


# =========================================================
# APPOINTMENT SETTINGS
# =========================================================

ALLOWED_DURATIONS = [15, 20]


# =========================================================
# WEEKDAYS
# =========================================================

WEEKDAYS = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday")
]


# =========================================================
# HELPER - GENERATE APPOINTMENT CODE
# =========================================================

def generate_appointment_code():

    last_appointment = Appointment.query.order_by(
        Appointment.id.desc()
    ).first()

    if last_appointment:
        next_number = last_appointment.id + 1
    else:
        next_number = 1

    return f"APT{next_number:04d}"


# =========================================================
# HELPER - GENERATE PATIENT CODE
# =========================================================

def generate_patient_code():

    last_patient = Patient.query.order_by(
        Patient.id.desc()
    ).first()

    if not last_patient:
        return "PAT0001"

    try:

        last_number = int(
            last_patient.patient_code.replace(
                "PAT",
                ""
            )
        )

        next_number = last_number + 1

    except (ValueError, AttributeError):

        next_number = last_patient.id + 1

    return f"PAT{next_number:04d}"


# =========================================================
# HELPER - CREATE ONLINE APPOINTMENT NOTIFICATIONS
# =========================================================

def create_online_appointment_notifications(
    appointment,
    patient,
    doctor
):

    # -----------------------------------------------------
    # Find Super Admin + Receptionist
    # -----------------------------------------------------

    staff_users = User.query.filter(
        User.role.in_([
            "super_admin",
            "receptionist"
        ]),
        User.is_active.is_(True)
    ).all()

    # -----------------------------------------------------
    # Notification details
    # -----------------------------------------------------

    title = "New Online Appointment"

    message = (
        f"New online appointment request received from "
        f"{patient.full_name} for Dr. {doctor.full_name} "
        f"on {appointment.appointment_date.strftime('%d %b %Y')} "
        f"at {appointment.appointment_time.strftime('%I:%M %p')}."
    )

    # -----------------------------------------------------
    # Create notification for each staff user
    # -----------------------------------------------------

    for user in staff_users:

        notification = Notification(

            user_id=user.id,

            appointment_id=appointment.id,

            title=title,

            message=message,

            notification_type="online_appointment",

            is_read=False

        )

        db.session.add(notification)


# =========================================================
# HELPER - GET DOCTOR AVAILABILITY
# =========================================================

def get_doctor_availability(
    doctor_id,
    appointment_date,
    appointment_time=None
):

    weekday = appointment_date.weekday()

    query = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        weekday=weekday,
        is_active=True
    ).order_by(
        DoctorAvailability.start_time.asc()
    )

    availabilities = query.all()

    if not availabilities:
        return None

    if appointment_time is None:
        return availabilities[0]

    for availability in availabilities:

        duration = availability.appointment_duration

        if duration not in ALLOWED_DURATIONS:
            duration = 20

        start_datetime = datetime.combine(
            appointment_date,
            availability.start_time
        )

        end_datetime = datetime.combine(
            appointment_date,
            availability.end_time
        )

        selected_datetime = datetime.combine(
            appointment_date,
            appointment_time
        )

        selected_end_datetime = (
            selected_datetime
            + timedelta(minutes=duration)
        )

        if (
            selected_datetime >= start_datetime
            and selected_end_datetime <= end_datetime
        ):
            return availability

    return None


# =========================================================
# HELPER - GET ALL DOCTOR AVAILABILITIES FOR A DAY
# =========================================================

def get_doctor_day_availabilities(
    doctor_id,
    appointment_date
):

    weekday = appointment_date.weekday()

    return DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        weekday=weekday,
        is_active=True
    ).order_by(
        DoctorAvailability.start_time.asc()
    ).all()


# =========================================================
# HELPER - GET AVAILABLE SLOTS
# =========================================================

def get_available_slots(
    doctor_id,
    appointment_date
):

    if appointment_date < date.today():
        return []

    availabilities = get_doctor_day_availabilities(
        doctor_id,
        appointment_date
    )

    if not availabilities:
        return []

    booked_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.status != "Cancelled"
    ).all()

    booked_times = {
        appointment.appointment_time
        for appointment in booked_appointments
    }

    slots = []

    for availability in availabilities:

        start_time = availability.start_time
        end_time = availability.end_time

        duration = availability.appointment_duration

        if duration not in ALLOWED_DURATIONS:
            duration = 20

        current_datetime = datetime.combine(
            appointment_date,
            start_time
        )

        ending_datetime = datetime.combine(
            appointment_date,
            end_time
        )

        while (
            current_datetime
            + timedelta(minutes=duration)
            <= ending_datetime
        ):

            current_time = current_datetime.time()

            if appointment_date == date.today():

                now = datetime.now()

                if current_datetime <= now:

                    current_datetime += timedelta(
                        minutes=duration
                    )

                    continue

            if current_time not in booked_times:

                slots.append({

                    "value": current_time.strftime(
                        "%H:%M"
                    ),

                    "display": current_time.strftime(
                        "%I:%M %p"
                    ),

                    "start_time": current_time.strftime(
                        "%I:%M %p"
                    ),

                    "end_time": (
                        current_datetime
                        + timedelta(minutes=duration)
                    ).time().strftime(
                        "%I:%M %p"
                    ),

                    "duration": duration

                })

            current_datetime += timedelta(
                minutes=duration
            )

    return slots


# =========================================================
# APPOINTMENT LIST
# =========================================================

@appointments_bp.route("/")
@role_required(
    "super_admin",
    "receptionist",
    "doctor",
    "staff"
)
def list_appointments():

    appointments = Appointment.query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()

    return render_template(
        "appointments/list.html",
        appointments=appointments
    )


# =========================================================
# ADD APPOINTMENT
# NORMAL + EMERGENCY
# SUPER ADMIN + RECEPTIONIST
# =========================================================

@appointments_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "receptionist"
)
def add_appointment():

    patients = Patient.query.order_by(
        Patient.full_name.asc()
    ).all()

    doctors = Doctor.query.filter_by(
        is_active=True
    ).order_by(
        Doctor.full_name.asc()
    ).all()

    if request.method == "POST":

        patient_id = request.form.get(
            "patient_id",
            ""
        ).strip()

        doctor_id = request.form.get(
            "doctor_id",
            ""
        ).strip()

        appointment_date = request.form.get(
            "appointment_date",
            ""
        ).strip()

        appointment_time = request.form.get(
            "appointment_time",
            ""
        ).strip()

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        appointment_type = request.form.get(
            "appointment_type",
            "NORMAL"
        ).strip().upper()

        emergency_priority = request.form.get(
            "emergency_priority",
            ""
        ).strip().upper()

        is_emergency = (
            appointment_type == "EMERGENCY"
        )

        if appointment_type not in [
            "NORMAL",
            "EMERGENCY"
        ]:

            flash(
                "Invalid appointment type.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        if is_emergency:

            if emergency_priority not in [
                "CRITICAL",
                "HIGH",
                "MEDIUM"
            ]:

                flash(
                    "Please select a valid emergency priority.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "appointments.add_appointment"
                    )
                )

        else:

            emergency_priority = None

        # -------------------------------------------------
        # PATIENT
        # -------------------------------------------------

        if not patient_id:

            flash(
                "Patient is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        try:

            patient_id = int(patient_id)

        except (ValueError, TypeError):

            flash(
                "Invalid patient selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        patient = Patient.query.get(patient_id)

        if not patient:

            flash(
                "Selected patient does not exist.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        # -------------------------------------------------
        # DOCTOR
        # -------------------------------------------------

        if not doctor_id:

            flash(
                "Doctor is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        try:

            doctor_id = int(doctor_id)

        except (ValueError, TypeError):

            flash(
                "Invalid doctor selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        doctor = Doctor.query.filter_by(
            id=doctor_id,
            is_active=True
        ).first()

        if not doctor:

            flash(
                "Selected doctor is not active or does not exist.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        if not appointment_date:

            flash(
                "Appointment date is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        try:

            parsed_date = datetime.strptime(
                appointment_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid appointment date.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        if parsed_date < date.today():

            flash(
                "Appointment date cannot be in the past.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        # -------------------------------------------------
        # TIME
        # -------------------------------------------------

        if not appointment_time:

            flash(
                "Appointment time is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        try:

            parsed_time = datetime.strptime(
                appointment_time,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid appointment time.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        # =================================================
        # NORMAL APPOINTMENT
        # =================================================

        if not is_emergency:

            availabilities = get_doctor_day_availabilities(
                doctor.id,
                parsed_date
            )

            if not availabilities:

                flash(
                    f"Dr. {doctor.full_name} is not available on "
                    f"{parsed_date.strftime('%A')}.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "appointments.add_appointment"
                    )
                )

            available_slots = get_available_slots(
                doctor.id,
                parsed_date
            )

            valid_slot_values = {
                slot["value"]
                for slot in available_slots
            }

            if appointment_time not in valid_slot_values:

                flash(
                    "Selected appointment slot is not available.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "appointments.add_appointment"
                    )
                )

        # =================================================
        # EMERGENCY
        # =================================================

        else:

            pass

        # -------------------------------------------------
        # DUPLICATE TIME
        # -------------------------------------------------

        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor.id,
            appointment_date=parsed_date,
            appointment_time=parsed_time
        ).filter(
            Appointment.status != "Cancelled"
        ).first()

        if existing_appointment:

            if existing_appointment.is_emergency:

                flash(
                    "This doctor already has an emergency appointment "
                    "at this time.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "appointments.add_appointment"
                    )
                )

            if is_emergency:

                flash(
                    "There is already an appointment at this time. "
                    "Please select another emergency time.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "appointments.add_appointment"
                    )
                )

            flash(
                "This appointment slot has already been booked.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        if is_emergency:
            appointment_status = "Emergency"
        else:
            appointment_status = "Scheduled"

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        appointment = Appointment(

            appointment_code=generate_appointment_code(),

            patient_id=patient.id,

            doctor_id=doctor.id,

            appointment_date=parsed_date,

            appointment_time=parsed_time,

            reason=reason,

            status=appointment_status,

            appointment_type=appointment_type,

            is_emergency=is_emergency,

            emergency_priority=emergency_priority

        )

        db.session.add(appointment)

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "ADD APPOINTMENT ERROR:",
                e
            )

            flash(
                "Unable to create appointment. Please try again.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.add_appointment"
                )
            )

        if is_emergency:

            flash(
                "Emergency appointment created successfully.",
                "success"
            )

        else:

            flash(
                "Appointment created successfully.",
                "success"
            )

        return redirect(
            url_for(
                "appointments.list_appointments"
            )
        )

    return render_template(
        "appointments/add.html",
        patients=patients,
        doctors=doctors
    )


# =========================================================
# DOCTOR WEEKLY SCHEDULE API
# =========================================================

@appointments_bp.route(
    "/doctor-schedule/<int:doctor_id>",
    methods=["GET"]
)
def doctor_schedule(doctor_id):

    doctor = Doctor.query.filter_by(
        id=doctor_id,
        is_active=True
    ).first()

    if not doctor:

        return jsonify({
            "success": False,
            "message": "Doctor not found."
        }), 404

    availabilities = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id,
        is_active=True
    ).order_by(
        DoctorAvailability.weekday.asc(),
        DoctorAvailability.start_time.asc()
    ).all()

    availability_map = {}

    for availability in availabilities:

        if availability.weekday not in availability_map:

            availability_map[
                availability.weekday
            ] = []

        availability_map[
            availability.weekday
        ].append(availability)

    schedule = []

    for weekday, day_name in WEEKDAYS:

        day_availabilities = availability_map.get(
            weekday,
            []
        )

        if not day_availabilities:

            schedule.append({

                "weekday": weekday,

                "day": day_name,

                "available": False,

                "start_time": None,

                "end_time": None,

                "appointment_duration": None

            })

            continue

        for availability in day_availabilities:

            schedule.append({

                "weekday": weekday,

                "day": day_name,

                "available": True,

                "start_time":
                    availability.start_time.strftime(
                        "%I:%M %p"
                    ),

                "end_time":
                    availability.end_time.strftime(
                        "%I:%M %p"
                    ),

                "appointment_duration":
                    availability.appointment_duration

            })

    return jsonify({

        "success": True,

        "doctor": {

            "id": doctor.id,

            "full_name":
                doctor.full_name,

            "specialization":
                doctor.specialization

        },

        "schedule": schedule

    })


# =========================================================
# AVAILABLE APPOINTMENT SLOTS API
# =========================================================

@appointments_bp.route(
    "/available-slots",
    methods=["GET"]
)
def available_slots():

    doctor_id = request.args.get(
        "doctor_id",
        ""
    ).strip()

    appointment_date = request.args.get(
        "appointment_date",
        ""
    ).strip()

    if not doctor_id:

        return jsonify({

            "success": False,

            "message": "Doctor is required.",

            "slots": []

        }), 400

    if not appointment_date:

        return jsonify({

            "success": False,

            "message": "Date is required.",

            "slots": []

        }), 400

    try:

        doctor_id = int(doctor_id)

        parsed_date = datetime.strptime(
            appointment_date,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return jsonify({

            "success": False,

            "message": "Invalid doctor or date.",

            "slots": []

        }), 400

    if parsed_date < date.today():

        return jsonify({

            "success": False,

            "message":
                "Appointment date cannot be in the past.",

            "slots": []

        }), 400

    doctor = Doctor.query.filter_by(
        id=doctor_id,
        is_active=True
    ).first()

    if not doctor:

        return jsonify({

            "success": False,

            "message": "Doctor not found.",

            "slots": []

        }), 404

    availabilities = get_doctor_day_availabilities(
        doctor.id,
        parsed_date
    )

    if not availabilities:

        day_name = parsed_date.strftime("%A")

        return jsonify({

            "success": False,

            "message":
                f"Dr. {doctor.full_name} is OFF on {day_name}.",

            "doctor_available": False,

            "day": day_name,

            "slots": []

        })

    slots = get_available_slots(
        doctor.id,
        parsed_date
    )

    schedule = []

    for availability in availabilities:

        schedule.append({

            "start_time":
                availability.start_time.strftime(
                    "%I:%M %p"
                ),

            "end_time":
                availability.end_time.strftime(
                    "%I:%M %p"
                ),

            "appointment_duration":
                availability.appointment_duration

        })

    if not slots:

        return jsonify({

            "success": False,

            "message":
                "Doctor is available, but all appointment slots are booked.",

            "doctor_available": True,

            "schedule": schedule,

            "slots": []

        })

    return jsonify({

        "success": True,

        "doctor_available": True,

        "doctor":
            doctor.full_name,

        "date":
            parsed_date.strftime(
                "%Y-%m-%d"
            ),

        "day":
            parsed_date.strftime(
                "%A"
            ),

        "schedule":
            schedule,

        "slots":
            slots

    })


# =========================================================
# PUBLIC ONLINE APPOINTMENT
# NORMAL ONLY
# =========================================================

@appointments_bp.route(
    "/online",
    methods=["GET", "POST"]
)
def online_appointment():

    doctors = Doctor.query.filter_by(
        is_active=True
    ).order_by(
        Doctor.full_name.asc()
    ).all()

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        doctor_id = request.form.get(
            "doctor_id",
            ""
        ).strip()

        appointment_date = request.form.get(
            "appointment_date",
            ""
        ).strip()

        appointment_time = request.form.get(
            "appointment_time",
            ""
        ).strip()

        patient_name = request.form.get(
            "patient_name",
            ""
        ).strip()

        patient_phone = request.form.get(
            "patient_phone",
            ""
        ).strip()

        patient_email = request.form.get(
            "patient_email",
            ""
        ).strip().lower()

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        # =================================================
        # LOGIN ACCOUNT DATA
        # =================================================

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # =================================================
        # PATIENT INFORMATION
        # =================================================

        if not patient_name:

            flash(
                "Patient name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if not patient_phone:

            flash(
                "Patient phone is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if not patient_email:

            flash(
                "Patient email is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # ACCOUNT VALIDATION
        # =================================================

        if not username:

            flash(
                "Username is required for patient login.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if len(username) < 3:

            flash(
                "Username must be at least 3 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if not password:

            flash(
                "Password is required for patient login.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # CHECK USERNAME
        # =================================================

        existing_user = User.query.filter(
            db.func.lower(User.username) ==
            username.lower()
        ).first()

        if existing_user:

            flash(
                "This username is already taken. "
                "Please choose another username.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # CHECK EMAIL
        # =================================================

        existing_email_user = User.query.filter(
            db.func.lower(User.email) ==
            patient_email.lower()
        ).first()

        if existing_email_user:

            flash(
                "This email is already registered. "
                "Please use your existing account.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # DOCTOR
        # =================================================

        if not doctor_id:

            flash(
                "Please select a doctor.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        try:

            doctor_id = int(doctor_id)

        except (ValueError, TypeError):

            flash(
                "Invalid doctor selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        doctor = Doctor.query.filter_by(
            id=doctor_id,
            is_active=True
        ).first()

        if not doctor:

            flash(
                "Selected doctor is not active or does not exist.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # DATE
        # =================================================

        if not appointment_date:

            flash(
                "Appointment date is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        try:

            parsed_date = datetime.strptime(
                appointment_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid appointment date.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        if parsed_date < date.today():

            flash(
                "Appointment date cannot be in the past.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # TIME
        # =================================================

        if not appointment_time:

            flash(
                "Please select an appointment time.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        try:

            parsed_time = datetime.strptime(
                appointment_time,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid appointment time.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # CHECK DOCTOR AVAILABILITY
        # =================================================

        availability = get_doctor_availability(
            doctor.id,
            parsed_date,
            parsed_time
        )

        if not availability:

            flash(
                f"Dr. {doctor.full_name} is not available on "
                f"{parsed_date.strftime('%A')} at the selected time.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # GET AVAILABLE SLOTS
        # =================================================

        available_slots = get_available_slots(
            doctor.id,
            parsed_date
        )

        valid_slot_values = {
            slot["value"]
            for slot in available_slots
        }

        if appointment_time not in valid_slot_values:

            flash(
                "Selected appointment slot is no longer available.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # DUPLICATE BOOKING CHECK
        # =================================================

        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor.id,
            appointment_date=parsed_date,
            appointment_time=parsed_time
        ).filter(
            Appointment.status != "Cancelled"
        ).first()

        if existing_appointment:

            flash(
                "This doctor already has an appointment at "
                "the selected date and time. Please choose another time.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # FIND EXISTING PATIENT
        # =================================================

        patient = Patient.query.filter_by(
            phone=patient_phone
        ).first()

        if not patient:

            patient = Patient.query.filter_by(
                email=patient_email
            ).first()

        # =================================================
        # CREATE NEW PATIENT
        # =================================================

        if not patient:

            patient = Patient(

                patient_code=generate_patient_code(),

                full_name=patient_name,

                phone=patient_phone,

                email=patient_email

            )

            db.session.add(patient)

            db.session.flush()

        else:

            if not patient.phone:

                patient.phone = patient_phone

            if not patient.email:

                patient.email = patient_email

            if not patient.full_name:

                patient.full_name = patient_name

        # =================================================
        # CREATE PATIENT USER ACCOUNT
        # =================================================

        patient_user = User.query.filter(
            db.or_(
                db.func.lower(User.username) ==
                username.lower(),

                db.func.lower(User.email) ==
                patient_email.lower()
            )
        ).first()

        if patient_user:

            # Existing user must belong to this patient
            if patient_user.patient_id not in (
                None,
                patient.id
            ):

                db.session.rollback()

                flash(
                    "This username or email belongs to another account.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "appointments.online_appointment"
                    )
                )

            patient_user.patient_id = patient.id
            patient_user.role = "patient"
            patient_user.is_active = True

        else:

            patient_user = User(

                username=username,

                email=patient_email,

                role="patient",

                patient_id=patient.id,

                is_active=True

            )

            patient_user.set_password(password)

            db.session.add(patient_user)

        # =================================================
        # APPOINTMENT CODE
        # =================================================

        appointment_code = generate_appointment_code()

        # =================================================
        # CREATE ONLINE APPOINTMENT
        # =================================================

        appointment = Appointment(

            appointment_code=appointment_code,

            patient_id=patient.id,

            doctor_id=doctor.id,

            appointment_date=parsed_date,

            appointment_time=parsed_time,

            appointment_type="NORMAL",

            is_emergency=False,

            emergency_priority="Normal",

            reason=reason,

            status="Pending",

            is_online=True,

            patient_name=patient_name,

            patient_phone=patient_phone,

            patient_email=patient_email

        )

        db.session.add(appointment)

        # =================================================
        # FLUSH
        # =================================================

        try:

            db.session.flush()

            # =================================================
            # CREATE NOTIFICATIONS
            # =================================================

            create_online_appointment_notifications(
                appointment=appointment,
                patient=patient,
                doctor=doctor
            )

            # =================================================
            # FINAL COMMIT
            # =================================================

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "ONLINE APPOINTMENT ERROR:",
                e
            )

            flash(
                "Unable to submit online appointment. "
                "Please try again.",
                "danger"
            )

            return redirect(
                url_for(
                    "appointments.online_appointment"
                )
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            "Online appointment request submitted successfully. "
            "You can now login using your username and password.",
            "success"
        )

        return redirect(
            url_for(
                "appointments.online_appointment_success",
                appointment_code=appointment_code
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "appointments/online.html",
        doctors=doctors
    )
# =========================================================
# ONLINE APPOINTMENT SUCCESS
# =========================================================

@appointments_bp.route(
    "/online/success/<appointment_code>"
)
def online_appointment_success(
    appointment_code
):

    appointment = Appointment.query.filter_by(
        appointment_code=appointment_code
    ).first_or_404()

    return render_template(
        "appointments/online_success.html",
        appointment=appointment
    )