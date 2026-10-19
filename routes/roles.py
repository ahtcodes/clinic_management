from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import current_user

from models.user import User
from extensions import db
from utils.permissions import role_required


roles_bp = Blueprint(
    "roles",
    __name__,
    url_prefix="/roles"
)


# =========================================================
# ROLE PERMISSIONS
# =========================================================

ROLE_PERMISSIONS = {

    "super_admin": [
        "View Dashboard",
        "Manage Patients",
        "Manage Doctors",
        "Manage Appointments",
        "Manage Consultations",
        "Manage Prescriptions",
        "Manage Billing",
        "Manage Users",
        "Manage Roles & Permissions"
    ],

    "receptionist": [
        "View Dashboard",
        "Manage Patients",
        "Manage Appointments",
        "Create Bills",
        "Edit Bills",
        "View Doctors"
    ],

    "doctor": [
        "View Dashboard",
        "View Patients",
        "View Doctors",
        "Manage Consultations",
        "Manage Prescriptions",
        "View Bills"
    ],

    "staff": [
        "View Dashboard",
        "View Patients",
        "View Doctors",
        "View Appointments",
        "View Consultations",
        "View Prescriptions",
        "View Bills"
    ],

    "patient": [
        "View Dashboard",
        "View My Appointments",
        "View My Consultations",
        "View My Prescriptions",
        "View My Bills",
        "Use Doctor Chat"
    ]
}


# =========================================================
# ROLE MANAGEMENT / PERMISSIONS PAGE
# ONLY SUPER ADMIN
# =========================================================

@roles_bp.route("/")
@role_required("super_admin")
def role_management():

    # -----------------------------------------------------
    # All available roles
    # -----------------------------------------------------

    roles = [
        "super_admin",
        "receptionist",
        "doctor",
        "staff",
        "patient"
    ]

    # -----------------------------------------------------
    # All role permissions
    # -----------------------------------------------------

    permissions = ROLE_PERMISSIONS

    # -----------------------------------------------------
    # Super Admin can see all users
    # -----------------------------------------------------

    users = User.query.order_by(
        User.username.asc()
    ).all()

    return render_template(
        "roles/index.html",
        users=users,
        roles=roles,
        permissions=permissions,
        current_role=current_user.role
    )


# =========================================================
# CHANGE USER ROLE
# ONLY SUPER ADMIN
# =========================================================

@roles_bp.route(
    "/change-role/<int:user_id>",
    methods=["POST"]
)
@role_required("super_admin")
def change_role(user_id):

    user = User.query.get_or_404(user_id)

    new_role = request.form.get("role")

    # -----------------------------------------------------
    # Allowed roles
    # -----------------------------------------------------

    allowed_roles = [
        "super_admin",
        "receptionist",
        "doctor",
        "staff",
        "patient"
    ]

    # -----------------------------------------------------
    # Validate role
    # -----------------------------------------------------

    if new_role not in allowed_roles:

        flash(
            "Invalid role selected.",
            "danger"
        )

        return redirect(
            url_for("roles.role_management")
        )

    # -----------------------------------------------------
    # Super Admin cannot remove own role
    # -----------------------------------------------------

    if (
        user.id == current_user.id
        and new_role != "super_admin"
    ):

        flash(
            "You cannot remove your own Super Admin role.",
            "danger"
        )

        return redirect(
            url_for("roles.role_management")
        )

    # -----------------------------------------------------
    # Update role
    # -----------------------------------------------------

    user.role = new_role

    db.session.commit()

    flash(
        f"Role updated successfully for {user.username}.",
        "success"
    )

    return redirect(
        url_for("roles.role_management")
    )