from datetime import datetime, timedelta
import secrets

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required
)

from models.user import User
from extensions import db


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)
# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------------------------
        # FIND USER BY USERNAME OR EMAIL
        # -------------------------------------------------

        user = User.query.filter(
            db.or_(
                db.func.lower(User.username) == username.lower(),
                db.func.lower(User.email) == username.lower()
            )
        ).first()

        # -------------------------------------------------
        # INVALID LOGIN
        # -------------------------------------------------

        if not user or not user.check_password(password):

            flash(
                "Invalid username/email or password.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        # -------------------------------------------------
        # CHECK ACTIVE ACCOUNT
        # -------------------------------------------------

        if not user.is_active:

            flash(
                "Your account is inactive.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        login_user(user)

        # -------------------------------------------------
        # PATIENT DASHBOARD
        # -------------------------------------------------

        if user.is_patient():

            return redirect(
                url_for("patient_dashboard.dashboard")
            )

        # -------------------------------------------------
        # STAFF / DOCTOR DASHBOARD
        # -------------------------------------------------

        return redirect(
            url_for("dashboard.dashboard")
        )

    return render_template(
        "auth/login.html"
    )
# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "If this email exists, a password reset link has been generated.",
                "info"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        # Generate secure token

        token = secrets.token_urlsafe(32)

        user.reset_token = token

        user.reset_token_expiry = (
            datetime.utcnow()
            + timedelta(minutes=30)
        )

        db.session.commit()

        # Development/testing URL
        reset_url = url_for(
            "auth.reset_password",
            token=token,
            _external=True
        )

        flash(
            "Password reset link generated. "
            "For development, open the reset link shown below.",
            "success"
        )

        return render_template(
            "auth/forgot_password.html",
            reset_url=reset_url
        )

    return render_template(
        "auth/forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    user = User.query.filter_by(
        reset_token=token
    ).first()

    if not user:

        flash(
            "Invalid or expired password reset link.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # Check expiry

    if (
        not user.reset_token_expiry
        or user.reset_token_expiry < datetime.utcnow()
    ):

        user.reset_token = None
        user.reset_token_expiry = None

        db.session.commit()

        flash(
            "This password reset link has expired.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        # Update password

        user.set_password(password)

        # Token can only be used once

        user.reset_token = None
        user.reset_token_expiry = None

        db.session.commit()

        flash(
            "Password reset successfully. You can now login.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        token=token
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )