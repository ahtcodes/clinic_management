
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from datetime import datetime

from flask_login import current_user

from extensions import db

from models.doctor import Doctor
from models.doctor_availability import DoctorAvailability
from models.user import User
from models.doctor_service import DoctorService

from utils.permissions import role_required


doctors_bp = Blueprint(
    "doctors",
    __name__,
    url_prefix="/doctors"
)


# =========================================================
# DOCTOR LIST
# =========================================================

@doctors_bp.route("/")
@role_required(
    "super_admin",
    "receptionist",
    "doctor",
    "staff"
)
def list_doctors():

    doctors = Doctor.query.order_by(
        Doctor.id.desc()
    ).all()

    return render_template(
        "doctors/list.html",
        doctors=doctors
    )


# =========================================================
# ADD DOCTOR
# SUPER ADMIN ONLY
# =========================================================

@doctors_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@role_required("super_admin")
def add_doctor():

    if request.method == "POST":

        # =================================================
        # DOCTOR INFORMATION
        # =================================================

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        specialization = request.form.get(
            "specialization",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        qualification = request.form.get(
            "qualification",
            ""
        ).strip()

        consultation_fee = request.form.get(
            "consultation_fee",
            "0"
        ).strip()

        room_number = request.form.get(
            "room_number",
            ""
        ).strip()

        is_active = request.form.get(
            "is_active"
        )

        # =================================================
        # LOGIN INFORMATION
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
        # REQUIRED VALIDATION
        # =================================================

        if not full_name:

            flash(
                "Doctor name is required.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        if not email:

            flash(
                "Doctor email is required.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        if not confirm_password:

            flash(
                "Please confirm the password.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # PASSWORD MATCH
        # =================================================

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # USERNAME DUPLICATE CHECK
        # =================================================

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash(
                "This username is already in use.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # USER EMAIL DUPLICATE CHECK
        # =================================================

        existing_user_email = User.query.filter_by(
            email=email
        ).first()

        if existing_user_email:

            flash(
                "This email is already registered.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # DOCTOR EMAIL DUPLICATE CHECK
        # =================================================

        existing_doctor_email = Doctor.query.filter_by(
            email=email
        ).first()

        if existing_doctor_email:

            flash(
                "This email is already assigned to another doctor.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # CONSULTATION FEE
        # =================================================

        try:

            consultation_fee = float(
                consultation_fee or 0
            )

        except (ValueError, TypeError):

            flash(
                "Invalid consultation fee.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        if consultation_fee < 0:

            flash(
                "Consultation fee cannot be negative.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # GENERATE DOCTOR CODE
        # =================================================

        last_doctor = (
            Doctor.query
            .order_by(
                Doctor.id.desc()
            )
            .first()
        )

        if last_doctor:

            next_number = last_doctor.id + 1

        else:

            next_number = 1

        doctor_code = (
            f"DOC{next_number:04d}"
        )

        # =================================================
        # CREATE DOCTOR
        # =================================================

        doctor = Doctor(

            doctor_code=doctor_code,

            full_name=full_name,

            specialization=(
                specialization or None
            ),

            phone=(
                phone or None
            ),

            email=(
                email or None
            ),

            qualification=(
                qualification or None
            ),

            consultation_fee=consultation_fee,

            room_number=(
                room_number or None
            ),

            is_active=True
            if is_active
            else False
        )

        db.session.add(
            doctor
        )

        # =================================================
        # FLUSH
        # =================================================

        db.session.flush()

        # =================================================
        # CREATE DOCTOR USER ACCOUNT
        # =================================================

        doctor_user = User(

            username=username,

            email=email,

            role="doctor",

            doctor_id=doctor.id,

            is_active=True
        )

        doctor_user.set_password(
            password
        )

        db.session.add(
            doctor_user
        )

        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to create doctor account. "
                "Please check username/email and try again.",
                "danger"
            )

            return redirect(
                url_for("doctors.add_doctor")
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"Doctor {full_name} and login account created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctors.list_doctors"
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "doctors/add.html"
    )


# =========================================================
# VIEW DOCTOR
# =========================================================

@doctors_bp.route(
    "/view/<int:doctor_id>"
)
@role_required(
    "super_admin",
    "receptionist",
    "doctor",
    "staff"
)
def view_doctor(doctor_id):

    doctor = Doctor.query.get_or_404(
        doctor_id
    )

    doctor_users = User.query.filter_by(
        role="doctor",
        is_active=True
    ).order_by(
        User.username.asc()
    ).all()

    return render_template(
        "doctors/view.html",
        doctor=doctor
    )


# =========================================================
# EDIT DOCTOR
# SUPER ADMIN ONLY
# =========================================================

@doctors_bp.route(
    "/edit/<int:doctor_id>",
    methods=["GET", "POST"]
)
@role_required("super_admin")
def edit_doctor(doctor_id):

    doctor = Doctor.query.get_or_404(
        doctor_id
    )

    doctor_users = User.query.filter_by(
        role="doctor",
        is_active=True
    ).order_by(
        User.username.asc()
    ).all()

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        specialization = request.form.get(
            "specialization",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        qualification = request.form.get(
            "qualification",
            ""
        ).strip()

        consultation_fee = request.form.get(
            "consultation_fee",
            "0"
        )

        room_number = request.form.get(
            "room_number",
            ""
        ).strip()

        is_active = request.form.get(
            "is_active"
        )

        doctor_user_id = request.form.get(
            "doctor_user_id"
        )

        # =================================================
        # REQUIRED VALIDATION
        # =================================================

        if not full_name:

            flash(
                "Doctor name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_doctor",
                    doctor_id=doctor.id
                )
            )

        # =================================================
        # CONSULTATION FEE
        # =================================================

        try:

            consultation_fee = float(
                consultation_fee or 0
            )

        except (ValueError, TypeError):

            flash(
                "Invalid consultation fee.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_doctor",
                    doctor_id=doctor.id
                )
            )

        if consultation_fee < 0:

            flash(
                "Consultation fee cannot be negative.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_doctor",
                    doctor_id=doctor.id
                )
            )

        # =================================================
        # DOCTOR ACCOUNT
        # =================================================

        selected_user = None

        if doctor_user_id:

            try:

                doctor_user_id = int(
                    doctor_user_id
                )

            except (ValueError, TypeError):

                flash(
                    "Invalid doctor account selected.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "doctors.edit_doctor",
                        doctor_id=doctor.id
                    )
                )

            selected_user = User.query.filter_by(
                id=doctor_user_id,
                role="doctor",
                is_active=True
            ).first()

            if not selected_user:

                flash(
                    "Invalid or inactive doctor account selected.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "doctors.edit_doctor",
                        doctor_id=doctor.id
                    )
                )

            if (
                selected_user.doctor_id is not None
                and selected_user.doctor_id != doctor.id
            ):

                flash(
                    "This doctor account is already linked to another doctor.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "doctors.edit_doctor",
                        doctor_id=doctor.id
                    )
                )

        # =================================================
        # UPDATE DOCTOR
        # =================================================

        doctor.full_name = full_name

        doctor.specialization = (
            specialization or None
        )

        doctor.phone = (
            phone or None
        )

        doctor.email = (
            email or None
        )

        doctor.qualification = (
            qualification or None
        )

        doctor.consultation_fee = (
            consultation_fee
        )

        doctor.room_number = (
            room_number or None
        )

        doctor.is_active = (
            True
            if is_active
            else False
        )

        # =================================================
        # REMOVE OLD LINK
        # =================================================

        old_user = User.query.filter_by(
            doctor_id=doctor.id
        ).first()

        if old_user:

            old_user.doctor_id = None

        # =================================================
        # NEW LINK
        # =================================================

        if selected_user:

            selected_user.doctor_id = doctor.id

        # =================================================
        # SAVE
        # =================================================

        db.session.commit()

        flash(
            "Doctor updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctors.view_doctor",
                doctor_id=doctor.id
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "doctors/edit.html",
        doctor=doctor,
        doctor_users=doctor_users
    )


# =========================================================
# DELETE DOCTOR
# SUPER ADMIN ONLY
# =========================================================

@doctors_bp.route(
    "/delete/<int:doctor_id>",
    methods=["POST"]
)
@role_required("super_admin")
def delete_doctor(doctor_id):

    doctor = Doctor.query.get_or_404(
        doctor_id
    )

    db.session.delete(
        doctor
    )

    db.session.commit()

    flash(
        "Doctor deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "doctors.list_doctors"
        )
    )


# =========================================================
# DOCTOR AVAILABILITY
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
# VIEW DOCTOR AVAILABILITY
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/<int:doctor_id>/availability"
)
@role_required(
    "super_admin",
    "doctor"
)
def doctor_availability(doctor_id):

    doctor = Doctor.query.get_or_404(
        doctor_id
    )

    # -----------------------------------------------------
    # Doctor can only access own schedule
    # -----------------------------------------------------

    if current_user.has_role("doctor"):

        if current_user.doctor_id != doctor.id:

            flash(
                "You can only access your own schedule.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_schedule")
            )

    availabilities = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        DoctorAvailability.weekday.asc(),
        DoctorAvailability.start_time.asc()
    ).all()

    return render_template(
        "doctors/availability.html",
        doctor=doctor,
        availabilities=availabilities,
        weekdays=WEEKDAYS
    )


# =========================================================
# ADD DOCTOR AVAILABILITY
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/<int:doctor_id>/availability/add",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def add_availability(doctor_id):

    doctor = Doctor.query.get_or_404(
        doctor_id
    )

    # -----------------------------------------------------
    # Doctor can only manage own schedule
    # -----------------------------------------------------

    if current_user.has_role("doctor"):

        if current_user.doctor_id != doctor.id:

            flash(
                "You can only manage your own schedule.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_schedule")
            )

    if request.method == "POST":

        weekday = request.form.get(
            "weekday"
        )

        start_time = request.form.get(
            "start_time"
        )

        end_time = request.form.get(
            "end_time"
        )

        appointment_duration = request.form.get(
            "appointment_duration"
        )

        # -------------------------------------------------
        # REQUIRED
        # -------------------------------------------------

        if (
            weekday is None
            or not start_time
            or not end_time
            or not appointment_duration
        ):

            flash(
                "All availability fields are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.add_availability",
                    doctor_id=doctor.id
                )
            )

        # -------------------------------------------------
        # CONVERT
        # -------------------------------------------------

        try:

            weekday = int(
                weekday
            )

            appointment_duration = int(
                appointment_duration
            )

            parsed_start = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            parsed_end = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

        except (ValueError, TypeError):

            flash(
                "Invalid availability data.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.add_availability",
                    doctor_id=doctor.id
                )
            )

        # -------------------------------------------------
        # WEEKDAY
        # -------------------------------------------------

        if weekday < 0 or weekday > 6:

            flash(
                "Invalid weekday selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.add_availability",
                    doctor_id=doctor.id
                )
            )

        # -------------------------------------------------
        # DURATION
        # -------------------------------------------------

        if appointment_duration not in [15, 20]:

            flash(
                "Appointment duration must be 15 or 20 minutes.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.add_availability",
                    doctor_id=doctor.id
                )
            )

        # -------------------------------------------------
        # TIME
        # -------------------------------------------------

        if parsed_start >= parsed_end:

            flash(
                "End time must be after start time.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.add_availability",
                    doctor_id=doctor.id
                )
            )

        # -------------------------------------------------
        # OVERLAP
        # -------------------------------------------------

        existing_slots = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            weekday=weekday,
            is_active=True
        ).all()

        for existing in existing_slots:

            if (
                parsed_start < existing.end_time
                and
                parsed_end > existing.start_time
            ):

                flash(
                    "This availability overlaps with an existing schedule.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "doctors.add_availability",
                        doctor_id=doctor.id
                    )
                )

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        availability = DoctorAvailability(

            doctor_id=doctor.id,

            weekday=weekday,

            start_time=parsed_start,

            end_time=parsed_end,

            appointment_duration=appointment_duration,

            is_active=True
        )

        db.session.add(
            availability
        )

        db.session.commit()

        flash(
            "Doctor availability added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctors.doctor_availability",
                doctor_id=doctor.id
            )
        )

    return render_template(
        "doctors/availability_add.html",
        doctor=doctor,
        weekdays=WEEKDAYS
    )


# =========================================================
# EDIT AVAILABILITY
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/availability/edit/<int:availability_id>",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def edit_availability(availability_id):

    availability = DoctorAvailability.query.get_or_404(
        availability_id
    )

    doctor = Doctor.query.get_or_404(
        availability.doctor_id
    )

    # -----------------------------------------------------
    # Doctor can only edit own schedule
    # -----------------------------------------------------

    if current_user.has_role("doctor"):

        if current_user.doctor_id != doctor.id:

            flash(
                "You can only manage your own schedule.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_schedule")
            )

    if request.method == "POST":

        weekday = request.form.get(
            "weekday"
        )

        start_time = request.form.get(
            "start_time"
        )

        end_time = request.form.get(
            "end_time"
        )

        appointment_duration = request.form.get(
            "appointment_duration"
        )

        is_active = request.form.get(
            "is_active"
        )

        # -------------------------------------------------
        # REQUIRED
        # -------------------------------------------------

        if (
            weekday is None
            or not start_time
            or not end_time
            or not appointment_duration
        ):

            flash(
                "All availability fields are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_availability",
                    availability_id=availability.id
                )
            )

        try:

            weekday = int(
                weekday
            )

            appointment_duration = int(
                appointment_duration
            )

            parsed_start = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            parsed_end = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

        except (ValueError, TypeError):

            flash(
                "Invalid availability data.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_availability",
                    availability_id=availability.id
                )
            )

        if weekday < 0 or weekday > 6:

            flash(
                "Invalid weekday selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_availability",
                    availability_id=availability.id
                )
            )

        if appointment_duration not in [15, 20]:

            flash(
                "Appointment duration must be 15 or 20 minutes.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_availability",
                    availability_id=availability.id
                )
            )

        if parsed_start >= parsed_end:

            flash(
                "End time must be after start time.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctors.edit_availability",
                    availability_id=availability.id
                )
            )

        # -------------------------------------------------
        # OVERLAP
        # -------------------------------------------------

        existing_slots = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.weekday == weekday,
            DoctorAvailability.is_active == True,
            DoctorAvailability.id != availability.id
        ).all()

        for existing in existing_slots:

            if (
                parsed_start < existing.end_time
                and
                parsed_end > existing.start_time
            ):

                flash(
                    "This availability overlaps with an existing schedule.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "doctors.edit_availability",
                        availability_id=availability.id
                    )
                )

        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        availability.weekday = weekday

        availability.start_time = parsed_start

        availability.end_time = parsed_end

        availability.appointment_duration = (
            appointment_duration
        )

        availability.is_active = (
            True
            if is_active
            else False
        )

        db.session.commit()

        flash(
            "Doctor availability updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctors.doctor_availability",
                doctor_id=doctor.id
            )
        )

    return render_template(
        "doctors/availability_edit.html",
        doctor=doctor,
        availability=availability,
        weekdays=WEEKDAYS
    )


# =========================================================
# DELETE AVAILABILITY
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/availability/delete/<int:availability_id>",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def delete_availability(availability_id):

    availability = DoctorAvailability.query.get_or_404(
        availability_id
    )

    if current_user.has_role("doctor"):

        if current_user.doctor_id != availability.doctor_id:

            flash(
                "You can only manage your own schedule.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_schedule")
            )

    doctor_id = availability.doctor_id

    db.session.delete(
        availability
    )

    db.session.commit()

    flash(
        "Doctor availability deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "doctors.doctor_availability",
            doctor_id=doctor_id
        )
    )


# =========================================================
# TOGGLE AVAILABILITY
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/availability/toggle/<int:availability_id>",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def toggle_availability(availability_id):

    availability = DoctorAvailability.query.get_or_404(
        availability_id
    )

    if current_user.has_role("doctor"):

        if current_user.doctor_id != availability.doctor_id:

            flash(
                "You can only manage your own schedule.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_schedule")
            )

    availability.is_active = (
        not availability.is_active
    )

    db.session.commit()

    if availability.is_active:

        flash(
            "Doctor availability activated.",
            "success"
        )

    else:

        flash(
            "Doctor availability deactivated.",
            "warning"
        )

    return redirect(
        url_for(
            "doctors.doctor_availability",
            doctor_id=availability.doctor_id
        )
    )


# =========================================================
# MY SCHEDULE
# DOCTOR ONLY
# =========================================================

@doctors_bp.route(
    "/my-schedule",
    methods=["GET"]
)
@role_required("doctor")
def my_schedule():

    if not current_user.doctor_id:

        flash(
            "Your account is not linked to a doctor profile.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    doctor = Doctor.query.get(
        current_user.doctor_id
    )

    if not doctor:

        flash(
            "Doctor profile not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    availabilities = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        DoctorAvailability.weekday.asc(),
        DoctorAvailability.start_time.asc()
    ).all()

    return render_template(
        "doctors/my_schedule.html",
        doctor=doctor,
        availabilities=availabilities
    )


# =========================================================
# FEES & SERVICES
#
# SUPER ADMIN:
#   Can manage any doctor.
#
# DOCTOR:
#   Can manage only own fees/services.
# =========================================================

@doctors_bp.route(
    "/my-fees-services"
)
@role_required(
    "super_admin",
    "doctor"
)
def my_fees_services():

    # =====================================================
    # SUPER ADMIN
    # =====================================================

    if current_user.has_role("super_admin"):

        doctors = Doctor.query.order_by(
            Doctor.full_name.asc()
        ).all()

        if not doctors:

            flash(
                "No doctor profiles found.",
                "warning"
            )

            return redirect(
                url_for("doctors.list_doctors")
            )

        doctor_id = request.args.get(
            "doctor_id",
            type=int
        )

        if doctor_id:

            doctor = Doctor.query.get_or_404(
                doctor_id
            )

        else:

            doctor = doctors[0]

        services = DoctorService.query.filter_by(
            doctor_id=doctor.id
        ).order_by(
            DoctorService.id.desc()
        ).all()

        return render_template(
            "doctors/my_fees_services.html",
            doctor=doctor,
            services=services,
            doctors=doctors,
            is_admin=True
        )

    # =====================================================
    # DOCTOR
    # =====================================================

    if not current_user.doctor_id:

        flash(
            "Your account is not linked to a doctor profile.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    doctor = Doctor.query.get(
        current_user.doctor_id
    )

    if not doctor:

        flash(
            "Doctor profile not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    services = DoctorService.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        DoctorService.id.desc()
    ).all()

    return render_template(
        "doctors/my_fees_services.html",
        doctor=doctor,
        services=services,
        doctors=[],
        is_admin=False
    )


# =========================================================
# UPDATE CONSULTATION FEE
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/my-fees-services/consultation-fee",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def update_my_consultation_fee():

    # =====================================================
    # FIND TARGET DOCTOR
    # =====================================================

    if current_user.has_role("super_admin"):

        doctor_id = request.form.get(
            "doctor_id",
            type=int
        )

        if not doctor_id:

            flash(
                "Please select a doctor.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_fees_services")
            )

        doctor = Doctor.query.get_or_404(
            doctor_id
        )

    else:

        if not current_user.doctor_id:

            flash(
                "Your account is not linked to a doctor profile.",
                "danger"
            )

            return redirect(
                url_for("dashboard.dashboard")
            )

        doctor = Doctor.query.get_or_404(
            current_user.doctor_id
        )

    # =====================================================
    # FEE
    # =====================================================

    fee = request.form.get(
        "consultation_fee",
        "0"
    ).strip()

    try:

        fee = float(
            fee
        )

    except (ValueError, TypeError):

        flash(
            "Please enter a valid consultation fee.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor.id
            )
        )

    if fee < 0:

        flash(
            "Consultation fee cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor.id
            )
        )

    # =====================================================
    # UPDATE
    # =====================================================

    doctor.consultation_fee = fee

    db.session.commit()

    flash(
        "Consultation fee updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "doctors.my_fees_services",
            doctor_id=doctor.id
        )
    )


# =========================================================
# ADD SERVICE
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/my-fees-services/add",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def add_my_service():

    # =====================================================
    # FIND TARGET DOCTOR
    # =====================================================

    if current_user.has_role("super_admin"):

        doctor_id = request.form.get(
            "doctor_id",
            type=int
        )

        if not doctor_id:

            flash(
                "Please select a doctor.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_fees_services")
            )

        doctor = Doctor.query.get_or_404(
            doctor_id
        )

    else:

        if not current_user.doctor_id:

            flash(
                "Your account is not linked to a doctor profile.",
                "danger"
            )

            return redirect(
                url_for("dashboard.dashboard")
            )

        doctor = Doctor.query.get_or_404(
            current_user.doctor_id
        )

    # =====================================================
    # FORM DATA
    # =====================================================

    service_name = request.form.get(
        "service_name",
        ""
    ).strip()

    fee = request.form.get(
        "fee",
        "0"
    ).strip()

    # =====================================================
    # SERVICE NAME
    # =====================================================

    if not service_name:

        flash(
            "Service name is required.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor.id
            )
        )

    # =====================================================
    # FEE
    # =====================================================

    try:

        fee = float(
            fee
        )

    except (ValueError, TypeError):

        flash(
            "Please enter a valid service fee.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor.id
            )
        )

    if fee < 0:

        flash(
            "Service fee cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor.id
            )
        )

    # =====================================================
    # DUPLICATE SERVICE
    # =====================================================

    existing = DoctorService.query.filter_by(
        doctor_id=doctor.id,
        service_name=service_name
    ).first()

    if existing:

        flash(
            "This service already exists.",
            "warning"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor.id
            )
        )

    # =====================================================
    # CREATE SERVICE
    # =====================================================

    service = DoctorService(

        doctor_id=doctor.id,

        service_name=service_name,

        fee=fee,

        is_active=True
    )

    db.session.add(
        service
    )

    db.session.commit()

    flash(
        "Service added successfully.",
        "success"
    )

    return redirect(
        url_for(
            "doctors.my_fees_services",
            doctor_id=doctor.id
        )
    )


# =========================================================
# EDIT SERVICE
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/my-fees-services/edit/<int:service_id>",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def edit_my_service(service_id):

    # =====================================================
    # FIND SERVICE
    # =====================================================

    service = DoctorService.query.get_or_404(
        service_id
    )

    # =====================================================
    # DOCTOR SECURITY
    # =====================================================

    if current_user.has_role("doctor"):

        if current_user.doctor_id != service.doctor_id:

            flash(
                "You can only edit your own services.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_fees_services")
            )

    doctor_id = service.doctor_id

    # =====================================================
    # FORM DATA
    # =====================================================

    service_name = request.form.get(
        "service_name",
        ""
    ).strip()

    fee = request.form.get(
        "fee",
        "0"
    ).strip()

    # =====================================================
    # NAME
    # =====================================================

    if not service_name:

        flash(
            "Service name is required.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor_id
            )
        )

    # =====================================================
    # FEE
    # =====================================================

    try:

        fee = float(
            fee
        )

    except (ValueError, TypeError):

        flash(
            "Please enter a valid service fee.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor_id
            )
        )

    if fee < 0:

        flash(
            "Service fee cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor_id
            )
        )

    # =====================================================
    # DUPLICATE
    # =====================================================

    existing = DoctorService.query.filter(
        DoctorService.doctor_id == doctor_id,
        DoctorService.service_name == service_name,
        DoctorService.id != service.id
    ).first()

    if existing:

        flash(
            "Another service with this name already exists.",
            "warning"
        )

        return redirect(
            url_for(
                "doctors.my_fees_services",
                doctor_id=doctor_id
            )
        )

    # =====================================================
    # UPDATE
    # =====================================================

    service.service_name = service_name

    service.fee = fee

    db.session.commit()

    flash(
        "Service updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "doctors.my_fees_services",
            doctor_id=doctor_id
        )
    )


# =========================================================
# ENABLE / DISABLE SERVICE
# SUPER ADMIN / DOCTOR
# =========================================================

@doctors_bp.route(
    "/my-fees-services/toggle/<int:service_id>",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def toggle_my_service(service_id):

    # =====================================================
    # FIND SERVICE
    # =====================================================

    service = DoctorService.query.get_or_404(
        service_id
    )

    # =====================================================
    # DOCTOR SECURITY
    # =====================================================

    if current_user.has_role("doctor"):

        if current_user.doctor_id != service.doctor_id:

            flash(
                "You can only manage your own services.",
                "danger"
            )

            return redirect(
                url_for("doctors.my_fees_services")
            )

    doctor_id = service.doctor_id

    # =====================================================
    # TOGGLE
    # =====================================================

    service.is_active = not service.is_active

    db.session.commit()

    if service.is_active:

        flash(
            f"{service.service_name} enabled successfully.",
            "success"
        )

    else:

        flash(
            f"{service.service_name} disabled successfully.",
            "warning"
        )

    return redirect(
        url_for(
            "doctors.my_fees_services",
            doctor_id=doctor_id
        )
    )

