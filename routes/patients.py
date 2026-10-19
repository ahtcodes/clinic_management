from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from datetime import datetime

from extensions import db

from models.patient import Patient
from models.user import User
from models.medicine_provision import MedicineProvision
from models.order import Order
from models.activity_notification import ActivityNotification

from utils.permissions import role_required


patients_bp = Blueprint(
    "patients",
    __name__,
    url_prefix="/patients"
)


# =========================================================
# PATIENT LIST + SEARCH
# =========================================================

@patients_bp.route("/")
@role_required(
    "super_admin",
    "receptionist",
    "doctor",
    "staff"
)
def list_patients():

    search = request.args.get(
        "search",
        ""
    ).strip()

    if search:

        patients = Patient.query.filter(
            db.or_(
                Patient.patient_code.ilike(
                    f"%{search}%"
                ),
                Patient.full_name.ilike(
                    f"%{search}%"
                ),
                Patient.phone.ilike(
                    f"%{search}%"
                )
            )
        ).order_by(
            Patient.id.desc()
        ).all()

    else:

        patients = Patient.query.order_by(
            Patient.id.desc()
        ).all()

    return render_template(
        "patients/list.html",
        patients=patients,
        search=search
    )


# =========================================================
# VIEW PATIENT
# =========================================================

@patients_bp.route(
    "/<int:patient_id>/view"
)
@role_required(
    "super_admin",
    "receptionist",
    "doctor",
    "staff"
)
def view_patient(patient_id):

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # Patient login account
    # -----------------------------------------------------

    patient_user = User.query.filter_by(
        patient_id=patient.id
    ).first()

    # -----------------------------------------------------
    # Medicine history
    # -----------------------------------------------------

    medicine_provisions = MedicineProvision.query.filter_by(
        patient_id=patient.id
    ).order_by(
        MedicineProvision.id.desc()
    ).all()

    # -----------------------------------------------------
    # Orders
    # -----------------------------------------------------

    orders = Order.query.filter_by(
        patient_id=patient.id
    ).order_by(
        Order.id.desc()
    ).all()

    return render_template(
        "patients/view.html",
        patient=patient,
        patient_user=patient_user,
        medicine_provisions=medicine_provisions,
        orders=orders
    )


# =========================================================
# ADD PATIENT
# =========================================================

@patients_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "receptionist"
)
def add_patient():

    # =====================================================
    # GET REQUEST
    # =====================================================

    if request.method == "GET":

        return render_template(
            "patients/add.html"
        )

    # =====================================================
    # PATIENT INFORMATION
    # =====================================================

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    father_name = request.form.get(
        "father_name",
        ""
    ).strip()

    gender = request.form.get(
        "gender",
        ""
    ).strip()

    # =====================================================
    # DATE OF BIRTH
    # =====================================================

    date_of_birth_raw = request.form.get(
        "date_of_birth",
        ""
    ).strip()

    date_of_birth = None

    if date_of_birth_raw:

        try:

            date_of_birth = datetime.strptime(
                date_of_birth_raw,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Please enter a valid date of birth.",
                "danger"
            )

            return render_template(
                "patients/add.html"
            )

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    address = request.form.get(
        "address",
        ""
    ).strip()

    blood_group = request.form.get(
        "blood_group",
        ""
    ).strip()

    emergency_contact = request.form.get(
        "emergency_contact",
        ""
    ).strip()

    medical_history = request.form.get(
        "medical_history",
        ""
    ).strip()

    allergies = request.form.get(
        "allergies",
        ""
    ).strip()

    # =====================================================
    # PATIENT LOGIN INFORMATION
    # =====================================================

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

    # =====================================================
    # BASIC VALIDATION
    # =====================================================

    if not full_name:

        flash(
            "Patient name is required.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    if not username:

        flash(
            "Patient username is required.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    if not password:

        flash(
            "Patient password is required.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    if len(password) < 6:

        flash(
            "Password must be at least 6 characters.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    if password != confirm_password:

        flash(
            "Passwords do not match.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    # =====================================================
    # CHECK USERNAME
    # =====================================================

    existing_username = User.query.filter(
        db.func.lower(
            User.username
        ) == username.lower()
    ).first()

    if existing_username:

        flash(
            "This username is already in use. "
            "Please choose another username.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    # =====================================================
    # CHECK EMAIL
    # =====================================================

    if email:

        existing_email = User.query.filter(
            db.func.lower(
                User.email
            ) == email.lower()
        ).first()

        if existing_email:

            flash(
                "This email is already associated "
                "with another account.",
                "danger"
            )

            return render_template(
                "patients/add.html"
            )

    # =====================================================
    # CREATE PATIENT CODE
    # =====================================================

    last_patient = Patient.query.order_by(
        Patient.id.desc()
    ).first()

    if last_patient:

        next_number = last_patient.id + 1

    else:

        next_number = 1

    patient_code = f"PAT{next_number:04d}"

    # =====================================================
    # CREATE PATIENT
    # =====================================================

    patient = Patient(
        patient_code=patient_code,
        full_name=full_name,
        father_name=father_name,
        gender=gender,
        date_of_birth=date_of_birth,
        phone=phone,
        email=email or None,
        address=address,
        blood_group=blood_group,
        emergency_contact=emergency_contact,
        medical_history=medical_history,
        allergies=allergies
    )

    db.session.add(patient)

    # =====================================================
    # FLUSH
    #
    # Patient ID is generated here.
    # =====================================================

    try:

        db.session.flush()

    except Exception as e:

        db.session.rollback()

        print(
            "PATIENT FLUSH ERROR:",
            repr(e)
        )

        flash(
            "Unable to create patient.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    # =====================================================
    # PATIENT USER EMAIL
    # =====================================================

    if email:

        user_email = email

    else:

        user_email = (
            f"patient{patient.id}"
            f"@patient.local"
        )

    # =====================================================
    # CHECK GENERATED EMAIL
    # =====================================================

    existing_user_email = User.query.filter(
        db.func.lower(
            User.email
        ) == user_email.lower()
    ).first()

    if existing_user_email:

        db.session.rollback()

        flash(
            "This email is already associated "
            "with another account.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    # =====================================================
    # CREATE PATIENT USER ACCOUNT
    # =====================================================

    patient_user = User(
        username=username,
        email=user_email,
        role="patient",
        patient_id=patient.id,
        is_active=True
    )

    # =====================================================
    # SET PASSWORD HASH
    # =====================================================

    patient_user.set_password(
        password
    )

    db.session.add(
        patient_user
    )

    # =====================================================
    # CREATE ADMIN NOTIFICATIONS
    #
    # Patient successfully create hone ke baad
    # sabhi Super Admin users ko notification milegi.
    # =====================================================

    try:

        admin_users = User.query.filter(
            User.role == "super_admin",
            User.is_active.is_(True)
        ).all()

        for admin in admin_users:

            admin_notification = ActivityNotification(
                user_id=admin.id,

                activity_type="general",

                title="New Patient Added",

                message=(
                    f"New patient {patient.full_name} "
                    f"({patient.patient_code}) has been added."
                ),

                reference_id=patient.id,

                reference_type="patient",

                action_url=url_for(
                    "patients.view_patient",
                    patient_id=patient.id
                ),

                is_read=False,

                created_at=datetime.utcnow()
            )

            db.session.add(
                admin_notification
            )

        # =================================================
        # FINAL COMMIT
        # =================================================

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "ADD PATIENT ERROR:",
            repr(e)
        )

        flash(
            "Unable to create patient and "
            "patient login account.",
            "danger"
        )

        return render_template(
            "patients/add.html"
        )

    # =====================================================
    # VERIFY PATIENT USER
    # =====================================================

    print(
        "========================================"
    )

    print(
        "PATIENT CREATED:",
        patient.id
    )

    print(
        "PATIENT CODE:",
        patient.patient_code
    )

    print(
        "PATIENT USER CREATED:",
        patient_user.id
    )

    print(
        "USERNAME:",
        patient_user.username
    )

    print(
        "ROLE:",
        patient_user.role
    )

    print(
        "PATIENT ID:",
        patient_user.patient_id
    )

    print(
        "ACTIVE:",
        patient_user.is_active
    )

    print(
        "ADMIN NOTIFICATIONS CREATED:",
        len(admin_users)
    )

    print(
        "========================================"
    )

    # =====================================================
    # SUCCESS
    # =====================================================

    flash(
        "Patient and patient login account "
        "created successfully.",
        "success"
    )

    return redirect(
        url_for(
            "patients.view_patient",
            patient_id=patient.id
        )
    )


# =========================================================
# EDIT PATIENT
# =========================================================

@patients_bp.route(
    "/<int:patient_id>/edit",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "receptionist"
)
def edit_patient(patient_id):

    patient = Patient.query.get_or_404(
        patient_id
    )

    if request.method == "POST":

        patient.full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        patient.father_name = request.form.get(
            "father_name",
            ""
        ).strip()

        patient.gender = request.form.get(
            "gender",
            ""
        ).strip()

        # =================================================
        # DATE OF BIRTH
        # =================================================

        date_of_birth_raw = request.form.get(
            "date_of_birth",
            ""
        ).strip()

        if date_of_birth_raw:

            try:

                patient.date_of_birth = datetime.strptime(
                    date_of_birth_raw,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Please enter a valid date of birth.",
                    "danger"
                )

                return render_template(
                    "patients/edit.html",
                    patient=patient
                )

        else:

            patient.date_of_birth = None

        patient.phone = request.form.get(
            "phone",
            ""
        ).strip()

        patient.email = request.form.get(
            "email",
            ""
        ).strip().lower() or None

        patient.address = request.form.get(
            "address",
            ""
        ).strip()

        patient.blood_group = request.form.get(
            "blood_group",
            ""
        ).strip()

        patient.emergency_contact = request.form.get(
            "emergency_contact",
            ""
        ).strip()

        patient.medical_history = request.form.get(
            "medical_history",
            ""
        ).strip()

        patient.allergies = request.form.get(
            "allergies",
            ""
        ).strip()

        # =================================================
        # SAVE CHANGES
        # =================================================

        try:

            db.session.commit()

            flash(
                "Patient updated successfully.",
                "success"
            )

        except Exception as e:

            db.session.rollback()

            print(
                "EDIT PATIENT ERROR:",
                repr(e)
            )

            flash(
                "Unable to update patient.",
                "danger"
            )

        return redirect(
            url_for(
                "patients.view_patient",
                patient_id=patient.id
            )
        )

    return render_template(
        "patients/edit.html",
        patient=patient
    )


# =========================================================
# DELETE PATIENT
# =========================================================

@patients_bp.route(
    "/<int:patient_id>/delete",
    methods=["POST"]
)
@role_required(
    "super_admin"
)
def delete_patient(patient_id):

    patient = Patient.query.get_or_404(
        patient_id
    )

    try:

        # =================================================
        # DELETE PATIENT
        #
        # User.patient_id uses ON DELETE SET NULL,
        # therefore the linked patient account will not
        # cause a foreign-key failure.
        # =================================================

        db.session.delete(
            patient
        )

        db.session.commit()

        flash(
            "Patient deleted successfully. "
            "Order and medicine history has been preserved.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print(
            "DELETE PATIENT ERROR:",
            repr(e)
        )

        flash(
            "Unable to delete patient because "
            "some linked records still prevent deletion.",
            "danger"
        )

    return redirect(
        url_for(
            "patients.list_patients"
        )
    )
