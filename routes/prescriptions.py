from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from extensions import db

from models.prescription import Prescription
from models.consultation import Consultation
from models.medicine import Medicine
from models.order import Order, OrderItem

from utils.permissions import role_required


prescriptions_bp = Blueprint(
    "prescriptions",
    __name__,
    url_prefix="/prescriptions"
)


# =========================================================
# GENERATE PRESCRIPTION CODE
# =========================================================

def generate_prescription_code():

    last_prescription = (
        Prescription.query
        .order_by(
            Prescription.id.desc()
        )
        .first()
    )

    if last_prescription:

        next_id = last_prescription.id + 1

    else:

        next_id = 1

    return f"RX{next_id:05d}"


# =========================================================
# GENERATE ORDER CODE
# =========================================================

def generate_order_code():

    last_order = (
        Order.query
        .order_by(
            Order.id.desc()
        )
        .first()
    )

    if last_order:

        next_id = last_order.id + 1

    else:

        next_id = 1

    return f"ORD{next_id:05d}"


# =========================================================
# ALL PRESCRIPTIONS
# =========================================================

@prescriptions_bp.route("/")
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def all_prescriptions():

    prescriptions = (
        Prescription.query
        .order_by(
            Prescription.id.desc()
        )
        .all()
    )

    return render_template(
        "prescriptions/list.html",
        prescriptions=prescriptions,
        consultation=None
    )


# =========================================================
# ADD PRESCRIPTION
# =========================================================

@prescriptions_bp.route(
    "/add/<int:consultation_id>",
    methods=["GET", "POST"]
)
@role_required(
    "super_admin",
    "doctor"
)
def add_prescription(consultation_id):

    # =====================================================
    # GET CONSULTATION
    # =====================================================

    consultation = Consultation.query.get_or_404(
        consultation_id
    )

    # =====================================================
    # GET DOCTOR MEDICINES
    # =====================================================

    medicines = (
        Medicine.query
        .filter(
            Medicine.doctor_id == consultation.doctor_id,
            Medicine.is_active.is_(True)
        )
        .order_by(
            Medicine.medicine_name.asc()
        )
        .all()
    )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        # -------------------------------------------------
        # SELECTED MEDICINE
        # -------------------------------------------------

        medicine_id = request.form.get(
            "medicine_id",
            type=int
        )

        # -------------------------------------------------
        # OTHER PRESCRIPTION FIELDS
        # -------------------------------------------------

        dosage = request.form.get(
            "dosage",
            ""
        ).strip()

        frequency = request.form.get(
            "frequency",
            ""
        ).strip()

        duration = request.form.get(
            "duration",
            ""
        ).strip()

        instructions = request.form.get(
            "instructions",
            ""
        ).strip()

        # =================================================
        # VALIDATE MEDICINE ID
        # =================================================

        if not medicine_id:

            flash(
                "Please select a medicine.",
                "danger"
            )

            return redirect(
                url_for(
                    "prescriptions.add_prescription",
                    consultation_id=consultation.id
                )
            )

        # =================================================
        # FIND MEDICINE
        # =================================================

        medicine = (
            Medicine.query
            .filter(
                Medicine.id == medicine_id,
                Medicine.doctor_id == consultation.doctor_id,
                Medicine.is_active.is_(True)
            )
            .first()
        )

        # =================================================
        # MEDICINE NOT FOUND
        # =================================================

        if not medicine:

            flash(
                "Selected medicine is not available for this doctor.",
                "danger"
            )

            return redirect(
                url_for(
                    "prescriptions.add_prescription",
                    consultation_id=consultation.id
                )
            )

        # =================================================
        # CHECK PATIENT
        # =================================================

        if not consultation.patient_id:

            flash(
                "This consultation is not linked with a patient.",
                "danger"
            )

            return redirect(
                url_for(
                    "prescriptions.list_prescriptions",
                    consultation_id=consultation.id
                )
            )

        # =================================================
        # MEDICINE NAME SNAPSHOT
        # =================================================

        medicine_name = medicine.medicine_name

        if medicine.strength:

            medicine_name = (
                f"{medicine.medicine_name}"
                f" - {medicine.strength}"
            )

        # =================================================
        # CREATE PRESCRIPTION
        # =================================================

        prescription = Prescription(

            prescription_code=generate_prescription_code(),

            consultation_id=consultation.id,

            patient_id=consultation.patient_id,

            doctor_id=consultation.doctor_id,

            medicine_name=medicine_name,

            dosage=dosage,

            frequency=frequency,

            duration=duration,

            instructions=instructions
        )

        # =================================================
        # ADD PRESCRIPTION TO SESSION
        # =================================================

        db.session.add(
            prescription
        )

        # =================================================
        # FLUSH
        #
        # This gives prescription.id before commit.
        # =================================================

        db.session.flush()

        # =================================================
        # CREATE AUTOMATIC ORDER
        #
        # Prescription add hote hi Order create hoga.
        #
        # IMPORTANT:
        # Order status = pending
        #
        # Stock abhi reduce nahi hoga.
        # Stock orders/confirm route par reduce hoga.
        # =================================================

        unit_price = medicine.price or 0

        order = Order(

            order_code=generate_order_code(),

            patient_id=consultation.patient_id,

            doctor_id=consultation.doctor_id,

            consultation_id=consultation.id,

            prescription_id=prescription.id,

            status="pending",

            total_amount=unit_price,

            notes=(
                "Automatically created from prescription "
                f"{prescription.prescription_code}."
            )
        )

        db.session.add(
            order
        )

        # =================================================
        # FLUSH ORDER
        #
        # OrderItem ko order relationship se attach karne
        # ke liye order.id ki zaroorat nahi.
        # =================================================

        db.session.flush()

        # =================================================
        # CREATE ORDER ITEM
        #
        # Prescription model mein quantity field nahi hai,
        # is liye default quantity = 1 rakhi ja rahi hai.
        #
        # Agar baad mein prescription mein quantity add
        # karni ho to is value ko dynamically use kar sakte hain.
        # =================================================

        order_item = OrderItem(

            order=order,

            medicine_id=medicine.id,

            medicine_name=medicine_name,

            unit=medicine.unit or "Tablet",

            quantity=1,

            unit_price=unit_price,

            total_price=unit_price
        )

        db.session.add(
            order_item
        )

        # =================================================
        # SAVE EVERYTHING
        #
        # Prescription
        # Order
        # OrderItem
        #
        # teeno ek hi transaction mein save honge.
        # =================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "PRESCRIPTION + ORDER CREATE ERROR:",
                e
            )

            flash(
                "Unable to save prescription and create order. "
                "Please try again.",
                "danger"
            )

            return render_template(
                "prescriptions/add.html",
                consultation=consultation,
                medicines=medicines
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"Prescription {prescription.prescription_code} "
            f"added successfully. "
            f"Order {order.order_code} was created automatically.",
            "success"
        )

        # =================================================
        # REDIRECT TO PRESCRIPTION LIST
        # =================================================

        return redirect(
            url_for(
                "prescriptions.list_prescriptions",
                consultation_id=consultation.id
            )
        )

    # =====================================================
    # GET PAGE
    # =====================================================

    return render_template(
        "prescriptions/add.html",
        consultation=consultation,
        medicines=medicines
    )


# =========================================================
# LIST PRESCRIPTIONS FOR ONE CONSULTATION
# =========================================================

@prescriptions_bp.route(
    "/consultation/<int:consultation_id>"
)
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def list_prescriptions(consultation_id):

    consultation = Consultation.query.get_or_404(
        consultation_id
    )

    prescriptions = (
        Prescription.query
        .filter_by(
            consultation_id=consultation.id
        )
        .order_by(
            Prescription.id.desc()
        )
        .all()
    )

    return render_template(
        "prescriptions/list.html",
        consultation=consultation,
        prescriptions=prescriptions
    )


# =========================================================
# VIEW PRESCRIPTION
# =========================================================

@prescriptions_bp.route(
    "/view/<int:prescription_id>"
)
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def view_prescription(prescription_id):

    prescription = Prescription.query.get_or_404(
        prescription_id
    )

    return render_template(
        "prescriptions/view.html",
        prescription=prescription
    )