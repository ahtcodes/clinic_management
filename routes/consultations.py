from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from extensions import db

from models.consultation import Consultation
from models.consultation_service import ConsultationService
from models.doctor_service import DoctorService
from models.appointment import Appointment

from utils.permissions import role_required


consultations_bp = Blueprint(
    "consultations",
    __name__,
    url_prefix="/consultations"
)


# =========================================================
# CONSULTATION LIST
# =========================================================

@consultations_bp.route("/")
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def list_consultations():

    consultations = Consultation.query.order_by(
        Consultation.created_at.desc()
    ).all()

    return render_template(
        "consultations/list.html",
        consultations=consultations
    )


# =========================================================
# ADD CONSULTATION
# =========================================================

@consultations_bp.route(
    "/add/<int:appointment_id>",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def add_consultation(appointment_id):

    appointment = Appointment.query.get_or_404(
        appointment_id
    )

    # =====================================================
    # CHECK IF CONSULTATION ALREADY EXISTS
    # =====================================================

    existing = Consultation.query.filter_by(
        appointment_id=appointment.id
    ).first()

    if existing:

        flash(
            "Consultation already exists for this appointment.",
            "warning"
        )

        return redirect(
            url_for(
                "consultations.view_consultation",
                consultation_id=existing.id
            )
        )

    # =====================================================
    # DOCTOR SERVICES
    # =====================================================

    doctor_services = DoctorService.query.filter_by(
        doctor_id=appointment.doctor_id,
        is_active=True
    ).order_by(
        DoctorService.service_name.asc()
    ).all()

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # GENERATE CONSULTATION CODE
        # =================================================

        last_consultation = Consultation.query.order_by(
            Consultation.id.desc()
        ).first()

        if last_consultation:

            last_id = last_consultation.id + 1

        else:

            last_id = 1

        consultation_code = (
            f"CON{last_id:04d}"
        )

        # =================================================
        # FOLLOW-UP DATE
        # =================================================

        follow_up_date = None

        follow_up = request.form.get(
            "follow_up_date",
            ""
        ).strip()

        if follow_up:

            try:

                follow_up_date = datetime.strptime(
                    follow_up,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid follow-up date.",
                    "danger"
                )

                return redirect(
                    request.url
                )

        # =================================================
        # TEMPERATURE CHECK
        # =================================================

        temperature_checked = (
            request.form.get(
                "temperature_checked"
            ) == "on"
        )

        temperature_fee = 0.0

        if temperature_checked:

            try:

                temperature_fee = float(
                    request.form.get(
                        "temperature_fee",
                        "0"
                    ) or 0
                )

            except (
                ValueError,
                TypeError
            ):

                temperature_fee = 0.0

            if temperature_fee < 0:

                temperature_fee = 0.0

        else:

            temperature_fee = 0.0

        # =================================================
        # SELECTED DOCTOR SERVICES
        # =================================================

        selected_service_ids = request.form.getlist(
            "service_ids"
        )

        selected_service_ids = set(
            selected_service_ids
        )

        selected_services = []

        for service in doctor_services:

            if str(service.id) in selected_service_ids:

                selected_services.append(
                    service
                )

        # =================================================
        # CREATE CONSULTATION
        # =================================================

        consultation = Consultation(

            consultation_code=consultation_code,

            appointment_id=appointment.id,

            patient_id=appointment.patient_id,

            doctor_id=appointment.doctor_id,

            # -------------------------------------------------
            # PATIENT COMPLAINTS
            # -------------------------------------------------

            symptoms=request.form.get(
                "symptoms",
                ""
            ).strip(),

            # -------------------------------------------------
            # VITALS
            # -------------------------------------------------

            blood_pressure=request.form.get(
                "blood_pressure",
                ""
            ).strip(),

            temperature=request.form.get(
                "temperature",
                ""
            ).strip(),

            weight=request.form.get(
                "weight",
                ""
            ).strip(),

            # -------------------------------------------------
            # TEMPERATURE CHECK BILLING
            # -------------------------------------------------

            temperature_checked=temperature_checked,

            temperature_fee=temperature_fee,

            # -------------------------------------------------
            # DIAGNOSIS
            # -------------------------------------------------

            diagnosis=request.form.get(
                "diagnosis",
                ""
            ).strip(),

            # -------------------------------------------------
            # CLINICAL NOTES
            # -------------------------------------------------

            clinical_notes=request.form.get(
                "clinical_notes",
                ""
            ).strip(),

            # -------------------------------------------------
            # TREATMENT
            # -------------------------------------------------

            treatment_notes=request.form.get(
                "treatment_notes",
                ""
            ).strip(),

            # -------------------------------------------------
            # FOLLOW UP
            # -------------------------------------------------

            follow_up_date=follow_up_date

        )

        # =================================================
        # SAVE CONSULTATION
        # =================================================

        db.session.add(
            consultation
        )

        # Flush so consultation.id becomes available
        # before creating ConsultationService records.
        db.session.flush()

        # =================================================
        # SAVE SELECTED SERVICES
        # =================================================

        for service in selected_services:

            consultation_service = ConsultationService(

                consultation_id=consultation.id,

                doctor_service_id=service.id,

                # Snapshot
                service_name=service.service_name,

                # Snapshot
                service_fee=service.fee or Decimal("0.00")

            )

            db.session.add(
                consultation_service
            )

        # =================================================
        # MARK APPOINTMENT COMPLETED
        # =================================================

        appointment.status = "Completed"

        # =================================================
        # COMMIT
        # =================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "CONSULTATION ERROR:",
                e
            )

            flash(
                "Unable to save consultation. Please try again.",
                "danger"
            )

            return redirect(
                request.url
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            "Consultation created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "consultations.view_consultation",
                consultation_id=consultation.id
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "consultations/add.html",
        appointment=appointment,
        doctor_services=doctor_services
    )


# =========================================================
# VIEW CONSULTATION
# =========================================================

@consultations_bp.route(
    "/<int:consultation_id>"
)
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def view_consultation(consultation_id):

    consultation = Consultation.query.get_or_404(
        consultation_id
    )

    return render_template(
        "consultations/view.html",
        consultation=consultation
    )