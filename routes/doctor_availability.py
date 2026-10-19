from datetime import datetime
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import current_user

from extensions import db

from models.doctor import Doctor
from models.doctor_availability import DoctorAvailability
from models.user import User
from models.activity_notification import ActivityNotification

from utils.permissions import role_required


# =========================================================
# BLUEPRINT
# =========================================================

doctor_availability_bp = Blueprint(
    "doctor_availability",
    __name__,
    url_prefix="/doctor-availability"
)


# =========================================================
# DAY NAMES
# =========================================================

DAYS = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday")
]


# =========================================================
# TIMEZONE
# =========================================================

PAKISTAN_TIMEZONE = ZoneInfo("Asia/Karachi")


# =========================================================
# HELPER
# GET LOGGED-IN DOCTOR
# =========================================================

def get_current_doctor():
    """
    Return the Doctor record linked with the
    currently logged-in doctor account.
    """

    if not current_user.is_authenticated:
        return None

    if current_user.role != "doctor":
        return None

    if not current_user.doctor_id:
        return None

    doctor = Doctor.query.filter_by(
        id=current_user.doctor_id,
        is_active=True
    ).first()

    return doctor


# =========================================================
# HELPER
# DELETE SCHEDULE NOTIFICATIONS
# =========================================================

def delete_schedule_notifications(doctor_id):
    """
    Delete existing schedule notifications for a doctor.

    IMPORTANT:
    Only notifications having reference_type =
    'doctor_schedule' are deleted.

    Other notification types such as:
        message
        order
        appointment
        prescription
        consultation
        billing
        medicine

    are NOT affected.
    """

    if not doctor_id:
        return

    doctor_user = User.query.filter_by(
        doctor_id=doctor_id,
        role="doctor"
    ).first()

    if not doctor_user:
        return

    ActivityNotification.query.filter(
        ActivityNotification.user_id == doctor_user.id,
        ActivityNotification.reference_type == "doctor_schedule"
    ).delete(
        synchronize_session=False
    )


# =========================================================
# HELPER
# CREATE / REPLACE SCHEDULE NOTIFICATION
# =========================================================

def create_schedule_notification(
    doctor,
    availability
):
    """
    Delete all previous schedule notifications for this doctor
    and create one fresh notification for the latest schedule.

    Notification always goes to the doctor account linked
    with the Doctor profile.

    Super Admin does NOT receive this notification.
    """

    # =====================================================
    # FIND DOCTOR USER
    # =====================================================

    doctor_user = User.query.filter_by(
        doctor_id=doctor.id,
        role="doctor"
    ).first()

    if not doctor_user:
        return

    # =====================================================
    # DELETE OLD SCHEDULE NOTIFICATIONS
    # =====================================================

    delete_schedule_notifications(
        doctor.id
    )

    # =====================================================
    # GET DAY NAME
    # =====================================================

    day_name = dict(DAYS).get(
        availability.weekday,
        "Unknown Day"
    )

    # =====================================================
    # FORMAT TIME
    # =====================================================

    start_time = availability.start_time.strftime(
        "%I:%M %p"
    )

    end_time = availability.end_time.strftime(
        "%I:%M %p"
    )

    # =====================================================
    # ACTIVE / INACTIVE STATUS
    # =====================================================

    schedule_status = (
        "Active"
        if availability.is_active
        else "Inactive"
    )

    # =====================================================
    # CREATE NEW NOTIFICATION
    # =====================================================

    notification = ActivityNotification(
        user_id=doctor_user.id,

        activity_type="general",

        title="Schedule Updated",

        message=(
            f"Your schedule has been set for "
            f"{day_name}, "
            f"{start_time} - "
            f"{end_time}. "
            f"Status: {schedule_status}."
        ),

        reference_id=doctor.id,

        reference_type="doctor_schedule",

        action_url=url_for(
            "doctor_availability.list_availability"
        ),

        is_read=False
    )

    db.session.add(
        notification
    )


# =========================================================
# HELPER
# GET LIVE AVAILABILITY STATUS
# =========================================================

def get_current_status(availability):
    """
    Return True only when the availability is:

    1. Enabled in database
    2. For today's weekday
    3. Current Pakistan time is within
       start_time <= current_time < end_time
    """

    # -----------------------------------------------------
    # DATABASE ENABLE/DISABLE CHECK
    # -----------------------------------------------------

    if not availability.is_active:
        return False

    # -----------------------------------------------------
    # CURRENT PAKISTAN DATE/TIME
    # -----------------------------------------------------

    now = datetime.now(
        PAKISTAN_TIMEZONE
    )

    current_weekday = now.weekday()
    current_time = now.time()

    # -----------------------------------------------------
    # CHECK CURRENT DAY
    # -----------------------------------------------------

    if availability.weekday != current_weekday:
        return False

    # -----------------------------------------------------
    # CHECK CURRENT TIME
    # -----------------------------------------------------

    if (
        availability.start_time
        <= current_time
        < availability.end_time
    ):
        return True

    return False


# =========================================================
# GET AVAILABILITY STATUS DICTIONARY
# =========================================================

def get_availability_statuses(availabilities):
    """
    Create a dictionary:

        {
            availability_id: True/False
        }
    """

    return {
        availability.id: get_current_status(
            availability
        )
        for availability in availabilities
    }


# =========================================================
# DOCTOR AVAILABILITY LIST
#
# SUPER ADMIN:
#   See all doctors
#
# DOCTOR:
#   See only own schedule
# =========================================================

@doctor_availability_bp.route("/")
@role_required(
    "super_admin",
    "doctor"
)
def list_availability():

    # =====================================================
    # SUPER ADMIN
    # =====================================================

    if current_user.has_role("super_admin"):

        doctors = Doctor.query.order_by(
            Doctor.full_name.asc()
        ).all()

        availabilities = DoctorAvailability.query.order_by(
            DoctorAvailability.doctor_id.asc(),
            DoctorAvailability.weekday.asc(),
            DoctorAvailability.start_time.asc()
        ).all()

        # -------------------------------------------------
        # CALCULATE LIVE STATUS
        # -------------------------------------------------

        availability_status = get_availability_statuses(
            availabilities
        )

        return render_template(
            "doctor_availability/list.html",
            doctors=doctors,
            availabilities=availabilities,
            days=DAYS,
            current_doctor=None,
            availability_status=availability_status
        )

    # =====================================================
    # DOCTOR
    # =====================================================

    doctor = get_current_doctor()

    if not doctor:

        flash(
            "Your doctor account is not linked to an active doctor profile.",
            "danger"
        )

        abort(403)

    # -----------------------------------------------------
    # ONLY THIS DOCTOR'S SCHEDULE
    # -----------------------------------------------------

    availabilities = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        DoctorAvailability.weekday.asc(),
        DoctorAvailability.start_time.asc()
    ).all()

    # -----------------------------------------------------
    # CALCULATE LIVE STATUS
    # -----------------------------------------------------

    availability_status = get_availability_statuses(
        availabilities
    )

    return render_template(
        "doctor_availability/list.html",
        doctors=[doctor],
        availabilities=availabilities,
        days=DAYS,
        current_doctor=doctor,
        availability_status=availability_status
    )


# =========================================================
# ADD AVAILABILITY
#
# SUPER ADMIN:
#   Can select any doctor
#
# DOCTOR:
#   Automatically uses own doctor profile
# =========================================================

@doctor_availability_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def add_availability():

    # =====================================================
    # SUPER ADMIN
    # =====================================================

    if current_user.has_role("super_admin"):

        doctors = Doctor.query.filter_by(
            is_active=True
        ).order_by(
            Doctor.full_name.asc()
        ).all()

        selected_doctor = None

    # =====================================================
    # DOCTOR
    # =====================================================

    else:

        selected_doctor = get_current_doctor()

        if not selected_doctor:

            flash(
                "Your doctor account is not linked to an active doctor profile.",
                "danger"
            )

            abort(403)

        doctors = [
            selected_doctor
        ]

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # DOCTOR ID
        # =================================================

        if current_user.has_role("doctor"):

            doctor_id = selected_doctor.id

        else:

            doctor_id = request.form.get(
                "doctor_id",
                ""
            ).strip()

        # =================================================
        # FORM VALUES
        # =================================================

        weekday = request.form.get(
            "weekday",
            ""
        ).strip()

        start_time = request.form.get(
            "start_time",
            ""
        ).strip()

        end_time = request.form.get(
            "end_time",
            ""
        ).strip()

        appointment_duration = request.form.get(
            "appointment_duration",
            "20"
        ).strip()

        is_active = request.form.get(
            "is_active"
        )

        # =================================================
        # REQUIRED VALIDATION
        # =================================================

        if not doctor_id:

            flash(
                "Please select a doctor.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        if weekday == "":

            flash(
                "Please select a day.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        if not start_time or not end_time:

            flash(
                "Start time and end time are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # CONVERT VALUES
        # =================================================

        try:

            doctor_id = int(
                doctor_id
            )

            weekday = int(
                weekday
            )

            appointment_duration = int(
                appointment_duration
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Invalid form data.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # SECURITY
        # DOCTOR CAN ONLY ADD OWN SCHEDULE
        # =================================================

        if current_user.has_role("doctor"):

            if doctor_id != current_user.doctor_id:

                abort(403)

        # =================================================
        # VALIDATE DAY
        # =================================================

        if weekday not in range(7):

            flash(
                "Invalid day selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # VALIDATE DURATION
        # =================================================

        if appointment_duration not in (
            15,
            20
        ):

            flash(
                "Appointment duration must be 15 or 20 minutes.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # VALIDATE DOCTOR
        # =================================================

        doctor = Doctor.query.filter_by(
            id=doctor_id,
            is_active=True
        ).first()

        if not doctor:

            flash(
                "Selected doctor does not exist or is inactive.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # PARSE TIME
        # =================================================

        try:

            parsed_start = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            parsed_end = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid start or end time.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # START < END
        # =================================================

        if parsed_start >= parsed_end:

            flash(
                "End time must be later than start time.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # CHECK DUPLICATE DAY
        # =================================================

        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            weekday=weekday
        ).first()

        if existing:

            flash(
                "Availability for this doctor on this day already exists.",
                "warning"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        # =================================================
        # CREATE AVAILABILITY
        # =================================================

        availability = DoctorAvailability(

            doctor_id=doctor.id,

            weekday=weekday,

            start_time=parsed_start,

            end_time=parsed_end,

            appointment_duration=appointment_duration,

            is_active=(
                True
                if is_active
                else False
            )
        )

        db.session.add(
            availability
        )

        # =================================================
        # CREATE NOTIFICATION
        # =================================================

        create_schedule_notification(
            doctor,
            availability
        )

        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "DOCTOR AVAILABILITY ERROR:",
                e
            )

            flash(
                "Unable to save doctor availability.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.add_availability"
                )
            )

        flash(
            "Doctor availability added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctor_availability.list_availability"
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "doctor_availability/add.html",
        doctors=doctors,
        days=DAYS,
        current_doctor=selected_doctor
    )


# =========================================================
# EDIT AVAILABILITY
#
# SUPER ADMIN:
#   Can edit any schedule
#
# DOCTOR:
#   Can edit ONLY own schedule
# =========================================================

@doctor_availability_bp.route(
    "/edit/<int:availability_id>",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def edit_availability(
    availability_id
):

    availability = DoctorAvailability.query.get_or_404(
        availability_id
    )

    # =====================================================
    # SECURITY CHECK FOR DOCTOR
    # =====================================================

    if current_user.has_role("doctor"):

        if availability.doctor_id != current_user.doctor_id:

            abort(403)

    # =====================================================
    # DOCTORS
    # =====================================================

    if current_user.has_role("super_admin"):

        doctors = Doctor.query.filter_by(
            is_active=True
        ).order_by(
            Doctor.full_name.asc()
        ).all()

    else:

        doctor = get_current_doctor()

        if not doctor:

            abort(403)

        doctors = [
            doctor
        ]

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # SAVE OLD DOCTOR ID
        #
        # Important when Super Admin changes the doctor
        # assigned to this availability.
        # =================================================

        old_doctor_id = availability.doctor_id

        # =================================================
        # DOCTOR ID
        # =================================================

        if current_user.has_role("doctor"):

            doctor_id = current_user.doctor_id

        else:

            doctor_id = request.form.get(
                "doctor_id",
                ""
            ).strip()

        # =================================================
        # FORM VALUES
        # =================================================

        weekday = request.form.get(
            "weekday",
            ""
        ).strip()

        start_time = request.form.get(
            "start_time",
            ""
        ).strip()

        end_time = request.form.get(
            "end_time",
            ""
        ).strip()

        appointment_duration = request.form.get(
            "appointment_duration",
            "20"
        ).strip()

        is_active = request.form.get(
            "is_active"
        )

        # =================================================
        # CONVERT
        # =================================================

        try:

            doctor_id = int(
                doctor_id
            )

            weekday = int(
                weekday
            )

            appointment_duration = int(
                appointment_duration
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Invalid form data.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # SECURITY
        # =================================================

        if current_user.has_role("doctor"):

            if doctor_id != current_user.doctor_id:

                abort(403)

        # =================================================
        # VALIDATE DAY
        # =================================================

        if weekday not in range(7):

            flash(
                "Invalid day selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # DURATION
        # =================================================

        if appointment_duration not in (
            15,
            20
        ):

            flash(
                "Appointment duration must be 15 or 20 minutes.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # PARSE TIME
        # =================================================

        try:

            parsed_start = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            parsed_end = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid start or end time.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # TIME VALIDATION
        # =================================================

        if parsed_start >= parsed_end:

            flash(
                "End time must be later than start time.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # VALIDATE DOCTOR
        # =================================================

        doctor = Doctor.query.filter_by(
            id=doctor_id,
            is_active=True
        ).first()

        if not doctor:

            flash(
                "Selected doctor does not exist or is inactive.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # DUPLICATE CHECK
        # =================================================

        duplicate = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.weekday == weekday,
            DoctorAvailability.id != availability.id
        ).first()

        if duplicate:

            flash(
                "This doctor already has availability for this day.",
                "warning"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        # =================================================
        # UPDATE
        # =================================================

        availability.doctor_id = doctor_id

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

        # =================================================
        # REMOVE OLD SCHEDULE NOTIFICATIONS
        #
        # This handles both:
        #
        # 1. Same doctor edited
        # 2. Super Admin changes schedule to another doctor
        # =================================================

        delete_schedule_notifications(
            old_doctor_id
        )

        # -------------------------------------------------
        # If doctor changed, also clean the new doctor's
        # previous schedule notification before creating
        # the latest one.
        # -------------------------------------------------

        if doctor_id != old_doctor_id:

            delete_schedule_notifications(
                doctor_id
            )

        # =================================================
        # CREATE LATEST NOTIFICATION
        # =================================================

        create_schedule_notification(
            doctor,
            availability
        )

        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "EDIT AVAILABILITY ERROR:",
                e
            )

            flash(
                "Unable to update availability.",
                "danger"
            )

            return redirect(
                url_for(
                    "doctor_availability.edit_availability",
                    availability_id=availability.id
                )
            )

        flash(
            "Doctor availability updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctor_availability.list_availability"
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "doctor_availability/edit.html",
        availability=availability,
        doctors=doctors,
        days=DAYS,
        current_doctor=(
            get_current_doctor()
            if current_user.has_role("doctor")
            else None
        )
    )


# =========================================================
# DELETE AVAILABILITY
#
# SUPER ADMIN:
#   Can delete any
#
# DOCTOR:
#   Can delete only own
# =========================================================

@doctor_availability_bp.route(
    "/delete/<int:availability_id>",
    methods=["POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def delete_availability(
    availability_id
):

    availability = DoctorAvailability.query.get_or_404(
        availability_id
    )

    # =====================================================
    # SECURITY
    # =====================================================

    if current_user.has_role("doctor"):

        if availability.doctor_id != current_user.doctor_id:

            abort(403)

    # =====================================================
    # SAVE DOCTOR ID BEFORE DELETE
    # =====================================================

    doctor_id = availability.doctor_id

    # =====================================================
    # DELETE AVAILABILITY
    # =====================================================

    db.session.delete(
        availability
    )

    # =====================================================
    # DELETE SCHEDULE NOTIFICATIONS
    #
    # IMPORTANT:
    # We only delete notifications where
    # reference_type = 'doctor_schedule'.
    #
    # Other notifications remain untouched.
    # =====================================================

    delete_schedule_notifications(
        doctor_id
    )

    # =====================================================
    # SAVE
    # =====================================================

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "DELETE AVAILABILITY ERROR:",
            e
        )

        flash(
            "Unable to delete availability.",
            "danger"
        )

        return redirect(
            url_for(
                "doctor_availability.list_availability"
            )
        )

    flash(
        "Doctor availability deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "doctor_availability.list_availability"
        )
    )