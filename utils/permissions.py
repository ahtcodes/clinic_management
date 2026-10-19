from functools import wraps

from flask import abort
from flask_login import current_user, login_required

# =========================================================

# ROLE PERMISSIONS

# =========================================================

ROLE_PERMISSIONS = {


# -----------------------------------------------------
# SUPER ADMIN
# -----------------------------------------------------

"super_admin": {

    "dashboard.view",

    "patients.view",
    "patients.create",
    "patients.edit",
    "patients.delete",

    "doctors.view",
    "doctors.create",
    "doctors.edit",
    "doctors.delete",

    "appointments.view",
    "appointments.create",
    "appointments.edit",
    "appointments.delete",

    "consultations.view",
    "consultations.create",
    "consultations.edit",
    "consultations.delete",

    "prescriptions.view",
    "prescriptions.create",
    "prescriptions.edit",
    "prescriptions.delete",

    "billing.view",
    "billing.create",
    "billing.edit",
    "billing.delete",

    "users.view",
    "users.create",
    "users.edit",
    "users.delete",

    "roles.view",
    "roles.manage",
},


# -----------------------------------------------------
# RECEPTIONIST
# -----------------------------------------------------

"receptionist": {

    "dashboard.view",

    "patients.view",
    "patients.create",
    "patients.edit",
    "patients.delete",

    "doctors.view",

    "appointments.view",
    "appointments.create",
    "appointments.edit",
    "appointments.delete",

    "billing.view",
    "billing.create",
    "billing.edit",
},


# -----------------------------------------------------
# DOCTOR
# -----------------------------------------------------

"doctor": {

    "dashboard.view",

    "patients.view",

    "doctors.view",

    "appointments.view",

    "consultations.view",
    "consultations.create",
    "consultations.edit",

    "prescriptions.view",
    "prescriptions.create",
    "prescriptions.edit",

    "billing.view",
},


# -----------------------------------------------------
# STAFF
# -----------------------------------------------------

"staff": {

    "dashboard.view",

    "patients.view",

    "doctors.view",

    "appointments.view",

    "consultations.view",

    "prescriptions.view",

    "billing.view",
},


# -----------------------------------------------------
# PATIENT
# -----------------------------------------------------

"patient": {

    "dashboard.view",

    "appointments.view",
    "appointments.create",

    "consultations.view",

    "prescriptions.view",

    "billing.view",
}


}

# =========================================================
# CHECK SINGLE PERMISSION
# =========================================================

def has_permission(permission):

    if not current_user.is_authenticated:
        return False

    if not current_user.is_active:
        return False

    user_role = current_user.role

    return permission in ROLE_PERMISSIONS.get(
        user_role,
        set()
    )


# =========================================================
# PERMISSION REQUIRED DECORATOR
# =========================================================

def permission_required(permission):

    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):

            if not current_user.is_active:
                abort(403)

            if not has_permission(permission):
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


# =========================================================
# ROLE REQUIRED DECORATOR
# =========================================================

def role_required(*roles):

    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):

            if not current_user.is_active:
                abort(403)

            if not current_user.has_role(*roles):
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator