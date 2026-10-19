
from flask import (
    Flask,
    redirect,
    url_for,
    request
)

from flask_login import (
    AnonymousUserMixin,
    current_user
)

from flask_socketio import SocketIO

from datetime import date

from config import Config
from extensions import (
    db,
    migrate,
    login_manager,
    socketio
)

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.doctors import doctors_bp
from routes.appointments import appointments_bp
from routes.consultations import consultations_bp
from routes.prescriptions import prescriptions_bp
from routes.billing import billing_bp
from routes.roles import roles_bp
from routes.home import home_bp
from routes.doctor_availability import doctor_availability_bp
from routes.notification import notifications_bp
from routes.medicines import medicines_bp
from routes.order import orders_bp
from routes.chat import chat_bp
from routes.patient_dashboard import patient_dashboard_bp
from routes.patient_chat import patient_chat_bp
from routes.patient_appointments import patient_appointments_bp

import socket_events


# =========================================================
# GUEST USER
# =========================================================

class GuestUser(AnonymousUserMixin):

    def has_role(self, *roles):
        return False

    def is_super_admin(self):
        return False

    def is_receptionist(self):
        return False

    def is_doctor(self):
        return False

    def is_staff(self):
        return False


# =========================================================
# CREATE APP
# =========================================================

def create_app():

    # =====================================================
    # CREATE FLASK APP
    # =====================================================

    app = Flask(__name__)

    app.config.from_object(Config)

    # =====================================================
    # JINJA GLOBALS
    # =====================================================

    # Makes "today" available in all Jinja templates
    app.jinja_env.globals["today"] = date.today()

    # =====================================================
    # EXTENSIONS
    # =====================================================

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )

    login_manager.init_app(
        app
    )

    login_manager.login_view = "auth.login"

    # =====================================================
    # SOCKET.IO
    # =====================================================

    socketio.init_app(
        app,
        cors_allowed_origins="*"
    )

    # =====================================================
    # ANONYMOUS USER
    # =====================================================

    login_manager.anonymous_user = GuestUser

    # =====================================================
    # USER LOADER
    # =====================================================

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):

        try:

            return User.query.get(
                int(user_id)
            )

        except (
            ValueError,
            TypeError
        ):

            return None

    # =====================================================
    # BLUEPRINTS
    # =====================================================

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        dashboard_bp
    )

    app.register_blueprint(
        patients_bp
    )

    app.register_blueprint(
        doctors_bp
    )

    app.register_blueprint(
        appointments_bp
    )

    app.register_blueprint(
        consultations_bp
    )

    app.register_blueprint(
        orders_bp
    )

    app.register_blueprint(
        chat_bp
    )

    app.register_blueprint(
        patient_appointments_bp
    )

    app.register_blueprint(
        prescriptions_bp
    )

    app.register_blueprint(
        patient_dashboard_bp
    )

    app.register_blueprint(
        billing_bp
    )

    app.register_blueprint(
        roles_bp
    )

    app.register_blueprint(
        notifications_bp
    )

    app.register_blueprint(
        home_bp
    )

    app.register_blueprint(
        doctor_availability_bp
    )

    app.register_blueprint(
        medicines_bp
    )

    app.register_blueprint(
        patient_chat_bp
    )

    # =====================================================
    # PUBLIC ONLINE APPOINTMENT SECURITY
    # =====================================================

    @app.before_request
    def restrict_public_access():

        # -------------------------------------------------
        # Logged-in clinic user
        # -------------------------------------------------

        if current_user.is_authenticated:

            return None

        # -------------------------------------------------
        # Static files
        # -------------------------------------------------

        if request.endpoint == "static":

            return None

        # -------------------------------------------------
        # Login / authentication pages
        # -------------------------------------------------

        if request.endpoint is not None:

            endpoint = request.endpoint

            if endpoint.startswith(
                "auth."
            ):

                return None

        # -------------------------------------------------
        # PUBLIC ONLINE APPOINTMENT
        # -------------------------------------------------

        allowed_public_endpoints = {

            "appointments.online_appointment",

            "appointments.online_appointment_success",

            "appointments.doctor_schedule",

            "appointments.available_slots"

        }

        # -------------------------------------------------
        # Allow online appointment pages
        # -------------------------------------------------

        if request.endpoint in allowed_public_endpoints:

            return None

        # -------------------------------------------------
        # EVERYTHING ELSE
        # -------------------------------------------------

        return redirect(
            url_for(
                "appointments.online_appointment"
            )
        )

    # =====================================================
    # RETURN APP
    # =====================================================

    return app


# =========================================================
# APPLICATION INSTANCE
# =========================================================

app = create_app()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    socketio.run(
        app,
        debug=True
    )

