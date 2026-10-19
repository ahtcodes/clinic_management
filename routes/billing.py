from decimal import Decimal, InvalidOperation
from datetime import datetime

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

from models.bill import Bill
from models.patient import Patient
from models.appointment import Appointment
from models.consultation import Consultation
from models.doctor import Doctor
from models.medicine_provision import MedicineProvision

from utils.permissions import role_required


billing_bp = Blueprint(
    "billing",
    __name__,
    url_prefix="/billing"
)


# =========================================================
# HELPER
# =========================================================

def get_decimal(value, default=Decimal("0.00")):

    try:

        if value is None or str(value).strip() == "":
            return default

        number = Decimal(
            str(value).strip()
        )

        if number < 0:
            return default

        return number

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return default


# =========================================================
# GET PENDING MEDICINE PROVISIONS
# =========================================================

def get_pending_medicine_provisions(patient_id):

    provisions = []

    total = Decimal("0.00")

    try:

        provisions = (
            MedicineProvision.query
            .filter_by(
                patient_id=patient_id,
                payment_status="pending"
            )
            .all()
        )

    except Exception as e:

        print(
            "MEDICINE PROVISION ERROR:",
            e
        )

        return [], Decimal("0.00")


    result = []


    for provision in provisions:

        # =================================================
        # QUANTITY
        # =================================================

        quantity = get_decimal(
            getattr(
                provision,
                "quantity",
                0
            )
        )


        # =================================================
        # UNIT PRICE
        # =================================================

        unit_price = get_decimal(
            getattr(
                provision,
                "unit_price",
                0
            )
        )


        # =================================================
        # TOTAL
        # =================================================

        provision_total = (
            quantity * unit_price
        )

        total += provision_total


        # =================================================
        # MEDICINE NAME
        # =================================================

        medicine_name = "Medicine"

        medicine = getattr(
            provision,
            "medicine",
            None
        )


        if medicine:

            medicine_name = (
                getattr(
                    medicine,
                    "medicine_name",
                    None
                )
                or "Medicine"
            )


        # =================================================
        # RESULT
        # =================================================

        result.append({

            "id": provision.id,

            "medicine_name": medicine_name,

            "quantity": float(
                quantity
            ),

            "price": float(
                unit_price
            ),

            "total": float(
                provision_total
            )

        })


    return result, total


# =========================================================
# GET CONSULTATION BILLING DATA
#
# IMPORTANT:
# Doctor services are ONLY returned as available options.
# They are NOT automatically added to service_fee_total.
# =========================================================

def get_consultation_billing_data(appointment):

    consultation = None

    consultation_fee = Decimal("0.00")

    services = []

    service_fee_total = Decimal("0.00")


    # =====================================================
    # GET DOCTOR
    # =====================================================

    doctor = None


    if appointment and appointment.doctor_id:

        doctor = Doctor.query.get(
            appointment.doctor_id
        )


    # =====================================================
    # DOCTOR CONSULTATION FEE
    # =====================================================

    if doctor:

        consultation_fee = get_decimal(
            doctor.consultation_fee
        )


    # =====================================================
    # GET CONSULTATION
    # =====================================================

    if appointment:

        consultation = Consultation.query.filter_by(
            appointment_id=appointment.id
        ).first()


    # =====================================================
    # DOCTOR ADDITIONAL SERVICES
    #
    # IMPORTANT:
    # Do NOT add their fees here.
    #
    # These are only available services.
    # The receptionist must select the services
    # actually provided to the patient.
    # =====================================================

    if doctor:

        doctor_services = (
            doctor.services
            if doctor.services
            else []
        )


        for doctor_service in doctor_services:

            if not doctor_service.is_active:

                continue


            service_fee = get_decimal(
                doctor_service.fee
            )


            service_name = (
                doctor_service.service_name
                or "Service"
            )


            services.append({

                "id": doctor_service.id,

                "service_name": service_name,

                "service_fee": float(
                    service_fee
                )

            })


        # =================================================
        # DO NOT TOTAL ALL SERVICES HERE
        # =================================================

        service_fee_total = Decimal("0.00")


    return (
        consultation,
        consultation_fee,
        services,
        service_fee_total
    )


# =========================================================
# CALCULATE SELECTED SERVICES
#
# Only services selected by the receptionist are charged.
# =========================================================

def calculate_selected_services(appointment, selected_service_ids):

    total = Decimal("0.00")

    selected_services = []

    if not appointment or not appointment.doctor_id:

        return selected_services, total


    doctor = Doctor.query.get(
        appointment.doctor_id
    )


    if not doctor:

        return selected_services, total


    # =====================================================
    # VALID ACTIVE SERVICES OF THIS DOCTOR
    # =====================================================

    doctor_services = [

        service

        for service in (
            doctor.services
            if doctor.services
            else []
        )

        if service.is_active

    ]


    # =====================================================
    # NORMALIZE SELECTED IDS
    # =====================================================

    selected_ids = set()


    for service_id in selected_service_ids:

        try:

            selected_ids.add(
                int(service_id)
            )

        except (
            ValueError,
            TypeError
        ):

            continue


    # =====================================================
    # CALCULATE ONLY SELECTED SERVICES
    # =====================================================

    for service in doctor_services:

        if service.id not in selected_ids:

            continue


        service_fee = get_decimal(
            service.fee
        )


        total += service_fee


        selected_services.append({

            "id": service.id,

            "service_name": (
                service.service_name
                or "Service"
            ),

            "service_fee": float(
                service_fee
            )

        })


    return selected_services, total


# =========================================================
# BILL LIST
# =========================================================

@billing_bp.route("/")
@role_required(
    "super_admin",
    "receptionist",
    "staff",
    "doctor"
)
def list_bills():

    bills = Bill.query.order_by(
        Bill.created_at.desc()
    ).all()


    return render_template(
        "billing/list.html",
        bills=bills
    )


# =========================================================
# GET APPOINTMENT BILLING DATA
# =========================================================

@billing_bp.route(
    "/appointment-billing-data",
    methods=["GET"]
)
@role_required(
    "super_admin",
    "receptionist"
)
def get_appointment_billing_data():

    appointment_id = request.args.get(
        "appointment_id"
    )


    if not appointment_id:

        return jsonify({

            "success": False,

            "message": (
                "Appointment ID is required."
            )

        }), 400


    try:

        appointment_id = int(
            appointment_id
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({

            "success": False,

            "message": (
                "Invalid appointment ID."
            )

        }), 400


    appointment = Appointment.query.get(
        appointment_id
    )


    if not appointment:

        return jsonify({

            "success": False,

            "message": (
                "Appointment not found."
            )

        }), 404


    # =====================================================
    # DOCTOR
    # =====================================================

    doctor = None


    if appointment.doctor_id:

        doctor = Doctor.query.get(
            appointment.doctor_id
        )


    # =====================================================
    # CONSULTATION + SERVICES
    #
    # Services are returned as options.
    # Their total is ZERO until selected.
    # =====================================================

    (
        consultation,
        consultation_fee,
        services,
        service_fee_total
    ) = get_consultation_billing_data(
        appointment
    )


    # =====================================================
    # PENDING MEDICINES
    # =====================================================

    pending_medicines = []

    medicine_fee_total = Decimal("0.00")


    if appointment.patient_id:

        (
            pending_medicines,
            medicine_fee_total
        ) = get_pending_medicine_provisions(
            appointment.patient_id
        )


    # =====================================================
    # APPOINTMENT DATE
    # =====================================================

    appointment_date = ""


    if appointment.appointment_date:

        appointment_date = (
            appointment.appointment_date
            .strftime("%d %b %Y")
        )


    # =====================================================
    # DOCTOR NAME
    # =====================================================

    doctor_name = "Not Assigned"


    if doctor:

        doctor_name = doctor.full_name


    # =====================================================
    # RESPONSE
    # =====================================================

    return jsonify({

        "success": True,

        "appointment_code": (
            appointment.appointment_code
            or ""
        ),

        "patient_id": (
            appointment.patient_id
            or ""
        ),

        "doctor_id": (
            appointment.doctor_id
            or ""
        ),

        "doctor_name": doctor_name,

        "appointment_date": appointment_date,

        "consultation_id": (
            consultation.id
            if consultation
            else None
        ),

        "consultation_fee": float(
            consultation_fee
        ),

        "services": services,

        # IMPORTANT:
        # Nothing selected yet.
        "service_fee_total": 0.0,

        # =================================================
        # MEDICINES
        # =================================================

        "pending_medicines": pending_medicines,

        "medicine_fee_total": float(
            medicine_fee_total
        )

    })


# =========================================================
# ADD BILL
# =========================================================

@billing_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "receptionist"
)
def add_bill():

    # =====================================================
    # PATIENTS
    # =====================================================

    patients = Patient.query.order_by(
        Patient.full_name.asc()
    ).all()


    # =====================================================
    # APPOINTMENTS
    # =====================================================

    appointments = Appointment.query.order_by(
        Appointment.appointment_date.desc()
    ).all()


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # PATIENT
        # =================================================

        patient_id = request.form.get(
            "patient_id"
        )


        if not patient_id:

            flash(
                "Patient is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "billing.add_bill"
                )
            )


        patient = Patient.query.get(
            patient_id
        )


        if not patient:

            flash(
                "Selected patient was not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "billing.add_bill"
                )
            )


        # =================================================
        # APPOINTMENT
        # =================================================

        appointment_id = request.form.get(
            "appointment_id"
        )


        appointment = None


        if appointment_id:

            appointment = Appointment.query.get(
                appointment_id
            )


            if not appointment:

                flash(
                    "Selected appointment was not found.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "billing.add_bill"
                    )
                )


            if (
                appointment.patient_id
                and
                int(appointment.patient_id)
                != int(patient_id)
            ):

                flash(
                    "Selected appointment does not belong to this patient.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "billing.add_bill"
                    )
                )


        # =================================================
        # CONSULTATION FEE
        # =================================================

        if appointment:

            (
                consultation,
                consultation_fee,
                available_services,
                ignored_service_total
            ) = get_consultation_billing_data(
                appointment
            )

        else:

            consultation_fee = get_decimal(
                request.form.get(
                    "consultation_fee"
                )
            )


        # =================================================
        # SELECTED ADDITIONAL SERVICES
        # =================================================

        selected_service_ids = request.form.getlist(
            "service_ids"
        )


        service_fee = Decimal("0.00")


        if appointment:

            (
                selected_services,
                service_fee
            ) = calculate_selected_services(
                appointment,
                selected_service_ids
            )

        else:

            # No appointment means there is no doctor
            # service selection available.
            service_fee = Decimal("0.00")


        # =================================================
        # MEDICINE FEE
        # =================================================

        medicine_fee = Decimal("0.00")


        if appointment and patient:

            (
                pending_medicines,
                medicine_fee
            ) = get_pending_medicine_provisions(
                patient.id
            )

        else:

            medicine_fee = get_decimal(
                request.form.get(
                    "medicine_fee"
                )
            )


        # =================================================
        # LABORATORY FEE
        # =================================================

        laboratory_fee = get_decimal(
            request.form.get(
                "laboratory_fee"
            )
        )


        # =================================================
        # OTHER CHARGES
        # =================================================

        other_charges = get_decimal(
            request.form.get(
                "other_charges"
            )
        )


        # =================================================
        # DISCOUNT
        # =================================================

        discount = get_decimal(
            request.form.get(
                "discount"
            )
        )


        # =================================================
        # PAID AMOUNT
        # =================================================

        paid_amount = get_decimal(
            request.form.get(
                "paid_amount"
            )
        )


        # =================================================
        # PAYMENT METHOD
        # =================================================

        payment_method = (
            request.form.get(
                "payment_method",
                "Cash"
            )
            or "Cash"
        ).strip()


        # =================================================
        # NOTES
        # =================================================

        notes = (
            request.form.get(
                "notes",
                ""
            )
            .strip()
        )


        # =================================================
        # SUBTOTAL
        #
        # Consultation
        # + Selected Services
        # + Medicine
        # + Laboratory
        # + Other
        # =================================================

        subtotal = (

            consultation_fee

            + service_fee

            + medicine_fee

            + laboratory_fee

            + other_charges

        )


        # =================================================
        # TOTAL
        # =================================================

        total_amount = max(

            subtotal
            - discount,

            Decimal("0.00")

        )


        # =================================================
        # PAID VALIDATION
        # =================================================

        if paid_amount > total_amount:

            flash(
                "Paid amount cannot be greater than total bill amount.",
                "danger"
            )

            return redirect(
                url_for(
                    "billing.add_bill"
                )
            )


        # =================================================
        # GENERATE BILL CODE
        # =================================================

        last_bill = Bill.query.order_by(
            Bill.id.desc()
        ).first()


        if last_bill:

            bill_number = (
                last_bill.id + 1
            )

        else:

            bill_number = 1


        bill_code = (
            f"BILL-{bill_number:05d}"
        )


        # =================================================
        # CREATE BILL
        # =================================================

        bill = Bill(

            bill_code=bill_code,

            patient_id=patient.id,

            appointment_id=(
                appointment.id
                if appointment
                else None
            ),

            consultation_fee=float(
                consultation_fee
            ),

            # ONLY SELECTED SERVICES
            service_fee=float(
                service_fee
            ),

            medicine_fee=float(
                medicine_fee
            ),

            laboratory_fee=float(
                laboratory_fee
            ),

            other_charges=float(
                other_charges
            ),

            discount=float(
                discount
            ),

            paid_amount=float(
                paid_amount
            ),

            payment_method=payment_method,

            notes=notes

        )


        # =================================================
        # TEMPERATURE FEE REMOVED
        # =================================================

        if hasattr(
            bill,
            "temperature_fee"
        ):

            bill.temperature_fee = 0


        # =================================================
        # CALCULATE TOTAL
        # =================================================

        bill.calculate_total()


        # =================================================
        # SAVE BILL
        # =================================================

        try:

            db.session.add(
                bill
            )

            db.session.commit()


        except Exception as e:

            db.session.rollback()

            print(
                "BILL CREATE ERROR:",
                e
            )

            flash(
                "Unable to create bill. Please try again.",
                "danger"
            )

            return redirect(
                url_for(
                    "billing.add_bill"
                )
            )


        # =================================================
        # MARK MEDICINE PROVISIONS AS PAID
        # =================================================

        try:

            if appointment and patient:

                pending_provisions = (
                    MedicineProvision.query
                    .filter_by(
                        patient_id=patient.id,
                        payment_status="pending"
                    )
                    .all()
                )


                for provision in pending_provisions:

                    provision.bill_id = bill.id

                    provision.payment_status = "paid"

                    provision.paid_at = datetime.utcnow()


                db.session.commit()


        except Exception as e:

            db.session.rollback()

            print(
                "MEDICINE PROVISION UPDATE ERROR:",
                e
            )


        # =================================================
        # SUCCESS
        # =================================================

        flash(
            "Bill created successfully.",
            "success"
        )


        return redirect(
            url_for(
                "billing.view_bill",
                id=bill.id
            )
        )


    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "billing/add.html",
        patients=patients,
        appointments=appointments
    )


# =========================================================
# VIEW BILL
# =========================================================

@billing_bp.route(
    "/view/<int:id>"
)
@role_required(
    "super_admin",
    "receptionist",
    "staff",
    "doctor"
)
def view_bill(id):

    bill = Bill.query.get_or_404(
        id
    )


    return render_template(
        "billing/view.html",
        bill=bill
    )


# =========================================================
# EDIT BILL
# =========================================================

@billing_bp.route(
    "/edit/<int:id>",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "receptionist"
)
def edit_bill(id):

    bill = Bill.query.get_or_404(
        id
    )


    # =====================================================
    # PATIENTS
    # =====================================================

    patients = Patient.query.order_by(
        Patient.full_name.asc()
    ).all()


    # =====================================================
    # APPOINTMENTS
    # =====================================================

    appointments = Appointment.query.order_by(
        Appointment.appointment_date.desc()
    ).all()


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # PATIENT
        # =================================================

        patient_id = request.form.get(
            "patient_id"
        )


        if not patient_id:

            flash(
                "Patient is required.",
                "danger"
            )

            return redirect(
                request.url
            )


        patient = Patient.query.get(
            patient_id
        )


        if not patient:

            flash(
                "Selected patient was not found.",
                "danger"
            )

            return redirect(
                request.url
            )


        # =================================================
        # APPOINTMENT
        # =================================================

        appointment_id = request.form.get(
            "appointment_id"
        )


        appointment = None


        if appointment_id:

            appointment = Appointment.query.get(
                appointment_id
            )


            if not appointment:

                flash(
                    "Selected appointment was not found.",
                    "danger"
                )

                return redirect(
                    request.url
                )


            if (
                appointment.patient_id
                and
                int(appointment.patient_id)
                != int(patient.id)
            ):

                flash(
                    "Selected appointment does not belong to this patient.",
                    "danger"
                )

                return redirect(
                    request.url
                )


        # =================================================
        # PATIENT / APPOINTMENT
        # =================================================

        bill.patient_id = patient.id

        bill.appointment_id = (
            appointment.id
            if appointment
            else None
        )


        # =================================================
        # CONSULTATION FEE
        # =================================================

        if appointment:

            (
                consultation,
                consultation_fee,
                available_services,
                ignored_service_total
            ) = get_consultation_billing_data(
                appointment
            )

        else:

            consultation_fee = get_decimal(
                request.form.get(
                    "consultation_fee"
                )
            )


        bill.consultation_fee = float(
            consultation_fee
        )


        # =================================================
        # SELECTED ADDITIONAL SERVICES
        # =================================================

        selected_service_ids = request.form.getlist(
            "service_ids"
        )


        if appointment:

            (
                selected_services,
                service_fee
            ) = calculate_selected_services(
                appointment,
                selected_service_ids
            )

        else:

            service_fee = Decimal("0.00")


        # IMPORTANT:
        # Only selected services are saved.

        bill.service_fee = float(
            service_fee
        )


        # =================================================
        # TEMPERATURE FEE REMOVED
        # =================================================

        if hasattr(
            bill,
            "temperature_fee"
        ):

            bill.temperature_fee = 0


        # =================================================
        # MEDICINE
        # =================================================

        if appointment and patient:

            (
                pending_medicines,
                medicine_fee
            ) = get_pending_medicine_provisions(
                patient.id
            )

            bill.medicine_fee = float(
                medicine_fee
            )

        else:

            bill.medicine_fee = float(
                get_decimal(
                    request.form.get(
                        "medicine_fee"
                    )
                )
            )


        # =================================================
        # LABORATORY
        # =================================================

        bill.laboratory_fee = float(
            get_decimal(
                request.form.get(
                    "laboratory_fee"
                )
            )
        )


        # =================================================
        # OTHER
        # =================================================

        bill.other_charges = float(
            get_decimal(
                request.form.get(
                    "other_charges"
                )
            )
        )


        # =================================================
        # DISCOUNT
        # =================================================

        bill.discount = float(
            get_decimal(
                request.form.get(
                    "discount"
                )
            )
        )


        # =================================================
        # PAID
        # =================================================

        bill.paid_amount = float(
            get_decimal(
                request.form.get(
                    "paid_amount"
                )
            )
        )


        # =================================================
        # PAYMENT METHOD
        # =================================================

        bill.payment_method = (
            request.form.get(
                "payment_method",
                "Cash"
            )
            or "Cash"
        ).strip()


        # =================================================
        # NOTES
        # =================================================

        bill.notes = (
            request.form.get(
                "notes",
                ""
            )
            .strip()
        )


        # =================================================
        # SUBTOTAL
        # =================================================

        subtotal = (

            Decimal(
                str(
                    bill.consultation_fee
                    or 0
                )
            )

            + Decimal(
                str(
                    bill.service_fee
                    or 0
                )
            )

            + Decimal(
                str(
                    bill.medicine_fee
                    or 0
                )
            )

            + Decimal(
                str(
                    bill.laboratory_fee
                    or 0
                )
            )

            + Decimal(
                str(
                    bill.other_charges
                    or 0
                )
            )

        )


        # =================================================
        # TOTAL
        # =================================================

        total_amount = max(

            subtotal

            - Decimal(
                str(
                    bill.discount
                    or 0
                )
            ),

            Decimal("0.00")

        )


        # =================================================
        # PAID VALIDATION
        # =================================================

        if (
            Decimal(
                str(
                    bill.paid_amount
                    or 0
                )
            )
            > total_amount
        ):

            flash(
                "Paid amount cannot be greater than total bill amount.",
                "danger"
            )

            return redirect(
                request.url
            )


        # =================================================
        # RECALCULATE
        # =================================================

        bill.calculate_total()


        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "BILL UPDATE ERROR:",
                e
            )

            flash(
                "Unable to update bill. Please try again.",
                "danger"
            )

            return redirect(
                request.url
            )


        flash(
            "Bill updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "billing.view_bill",
                id=bill.id
            )
        )


    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "billing/edit.html",
        bill=bill,
        patients=patients,
        appointments=appointments
    )


# =========================================================
# DELETE BILL
# SUPER ADMIN ONLY
# =========================================================

@billing_bp.route(
    "/delete/<int:id>",
    methods=["POST"]
)
@role_required(
    "super_admin"
)
def delete_bill(id):

    bill = Bill.query.get_or_404(
        id
    )


    try:

        db.session.delete(
            bill
        )

        db.session.commit()


    except Exception as e:

        db.session.rollback()

        print(
            "BILL DELETE ERROR:",
            e
        )

        flash(
            "Unable to delete bill.",
            "danger"
        )

        return redirect(
            url_for(
                "billing.list_bills"
            )
        )


    flash(
        "Bill deleted successfully.",
        "success"
    )


    return redirect(
        url_for(
            "billing.list_bills"
        )
    )