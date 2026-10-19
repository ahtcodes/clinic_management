
from datetime import datetime
from decimal import Decimal
from models.medicine_provision import MedicineProvision
from models.medicine_batch import MedicineBatch
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from extensions import db

from models.order import Order, OrderItem
from models.medicine import Medicine
from models.patient import Patient
from models.prescription import Prescription

from utils.permissions import role_required


orders_bp = Blueprint(
    "orders",
    __name__,
    url_prefix="/orders"
)


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
# ALL ORDERS
# =========================================================

@orders_bp.route("/")
@login_required
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def all_orders():

    orders = (
        Order.query
        .order_by(
            Order.id.desc()
        )
        .all()
    )

    return render_template(
        "orders/list.html",
        orders=orders
    )


# =========================================================
# CREATE ORDER
# =========================================================

@orders_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "super_admin",
    "doctor"
)
def add_order():

    # =====================================================
    # DOCTOR
    # =====================================================

    doctor_id = current_user.doctor_id

    if not doctor_id:

        flash(
            "Your account is not linked with a doctor.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    # =====================================================
    # PATIENTS
    # =====================================================

    patients = (
        Patient.query
        .order_by(
            Patient.full_name.asc()
        )
        .all()
    )

    # =====================================================
    # DOCTOR MEDICINES
    # =====================================================

    medicines = (
        Medicine.query
        .filter(
            Medicine.doctor_id == doctor_id,
            Medicine.is_active.is_(True)
        )
        .order_by(
            Medicine.medicine_name.asc()
        )
        .all()
    )

    # =====================================================
    # PRESCRIPTIONS
    # =====================================================

    prescriptions = (
        Prescription.query
        .filter(
            Prescription.doctor_id == doctor_id
        )
        .order_by(
            Prescription.id.desc()
        )
        .all()
    )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        patient_id = request.form.get(
            "patient_id",
            type=int
        )

        prescription_id = request.form.get(
            "prescription_id",
            type=int
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        # =================================================
        # PATIENT VALIDATION
        # =================================================

        if not patient_id:

            flash(
                "Please select a patient.",
                "danger"
            )

            return render_template(
                "orders/add.html",
                patients=patients,
                medicines=medicines,
                prescriptions=prescriptions
            )

        patient = Patient.query.get(
            patient_id
        )

        if not patient:

            flash(
                "Selected patient was not found.",
                "danger"
            )

            return render_template(
                "orders/add.html",
                patients=patients,
                medicines=medicines,
                prescriptions=prescriptions
            )

        # =================================================
        # PRESCRIPTION VALIDATION
        # =================================================

        prescription = None

        if prescription_id:

            prescription = (
                Prescription.query
                .filter(
                    Prescription.id == prescription_id,
                    Prescription.doctor_id == doctor_id
                )
                .first()
            )

            if not prescription:

                flash(
                    "Selected prescription is not valid.",
                    "danger"
                )

                return render_template(
                    "orders/add.html",
                    patients=patients,
                    medicines=medicines,
                    prescriptions=prescriptions
                )

            # Prescription patient must match order patient

            if prescription.patient_id != patient.id:

                flash(
                    "Selected prescription does not belong to this patient.",
                    "danger"
                )

                return render_template(
                    "orders/add.html",
                    patients=patients,
                    medicines=medicines,
                    prescriptions=prescriptions
                )

        # =================================================
        # GET SELECTED MEDICINES
        # =================================================

        medicine_ids = request.form.getlist(
            "medicine_id"
        )

        quantities = request.form.getlist(
            "quantity"
        )

        # =================================================
        # VALIDATE MEDICINES
        # =================================================

        if not medicine_ids:

            flash(
                "Please select at least one medicine.",
                "danger"
            )

            return render_template(
                "orders/add.html",
                patients=patients,
                medicines=medicines,
                prescriptions=prescriptions
            )

        if len(medicine_ids) != len(quantities):

            flash(
                "Invalid medicine quantities.",
                "danger"
            )

            return render_template(
                "orders/add.html",
                patients=patients,
                medicines=medicines,
                prescriptions=prescriptions
            )

        selected_items = []

        try:

            for medicine_id_value, quantity_value in zip(
                medicine_ids,
                quantities
            ):

                medicine_id = int(
                    medicine_id_value
                )

                quantity = int(
                    quantity_value
                )

                if quantity <= 0:

                    raise ValueError

                medicine = (
                    Medicine.query
                    .filter(
                        Medicine.id == medicine_id,
                        Medicine.doctor_id == doctor_id,
                        Medicine.is_active.is_(True)
                    )
                    .first()
                )

                if not medicine:

                    flash(
                        "One of the selected medicines is invalid.",
                        "danger"
                    )

                    return render_template(
                        "orders/add.html",
                        patients=patients,
                        medicines=medicines,
                        prescriptions=prescriptions
                    )

                # -----------------------------------------
                # STOCK CHECK
                # -----------------------------------------

                if medicine.quantity <= 0:

                    flash(
                        f"{medicine.medicine_name} is out of stock.",
                        "danger"
                    )

                    return render_template(
                        "orders/add.html",
                        patients=patients,
                        medicines=medicines,
                        prescriptions=prescriptions
                    )

                if quantity > medicine.quantity:

                    flash(
                        f"Only {medicine.quantity} "
                        f"{medicine.unit} of "
                        f"{medicine.medicine_name} are available.",
                        "danger"
                    )

                    return render_template(
                        "orders/add.html",
                        patients=patients,
                        medicines=medicines,
                        prescriptions=prescriptions
                    )

                unit_price = Decimal(
                    str(medicine.price or 0)
                )

                total_price = (
                    unit_price
                    *
                    Decimal(quantity)
                )

                selected_items.append({
                    "medicine": medicine,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price
                })

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Medicine quantity must be a valid number greater than 0.",
                "danger"
            )

            return render_template(
                "orders/add.html",
                patients=patients,
                medicines=medicines,
                prescriptions=prescriptions
            )

        # =================================================
        # CALCULATE TOTAL
        # =================================================

        total_amount = sum(
            (
                item["total_price"]
                for item in selected_items
            ),
            Decimal("0.00")
        )

        # =================================================
        # CREATE ORDER
        # =================================================

        order = Order(
            order_code=order_code,
            patient_id=patient.id,

            patient_name=patient.full_name,
            patient_code=patient.patient_code,

            doctor_id=doctor.id,
            consultation_id=consultation_id,
            prescription_id=prescription_id,

            status="pending",
            total_amount=total_amount,
            notes=notes
        ),

        prescription_id=(
            prescription.id
             if prescription
             else None
        ),

        status="pending",

        total_amount=total_amount,

        notes=notes or None,

        created_at=datetime.utcnow()
        

        db.session.add(order)

        # =================================================
        # CREATE ORDER ITEMS
        # =================================================

        for item in selected_items:

            medicine = item["medicine"]

            medicine_name = medicine.medicine_name

            if medicine.strength:

                medicine_name = (
                    f"{medicine.medicine_name}"
                    f" - {medicine.strength}"
                )

            order_item = OrderItem(

                order=order,

                medicine_id=medicine.id,

                medicine_name=medicine_name,

                unit=medicine.unit,

                quantity=item["quantity"],

                unit_price=item["unit_price"],

                total_price=item["total_price"]
            )

            db.session.add(
                order_item
            )

        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "ORDER CREATE ERROR:",
                e
            )

            flash(
                "Unable to create order. Please try again.",
                "danger"
            )

            return render_template(
                "orders/add.html",
                patients=patients,
                medicines=medicines,
                prescriptions=prescriptions
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"Order {order.order_code} created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "orders.view_order",
                order_id=order.id
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "orders/add.html",
        patients=patients,
        medicines=medicines,
        prescriptions=prescriptions
    )


# =========================================================
# VIEW ORDER
# =========================================================

@orders_bp.route(
    "/view/<int:order_id>"
)
@login_required
@role_required(
    "super_admin",
    "doctor",
    "receptionist",
    "staff"
)
def view_order(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    return render_template(
        "orders/view.html",
        order=order
    )


# =========================================================
# CONFIRM ORDER
#
# STOCK IS REDUCED FROM BATCHES
# MEDICINE PROVISION HISTORY IS CREATED
# =========================================================

@orders_bp.route(
    "/confirm/<int:order_id>",
    methods=["POST"]
)
@login_required
@role_required(
    "super_admin",
    "doctor"
)
def confirm_order(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    # =====================================================
    # DOCTOR OWNERSHIP CHECK
    # =====================================================

    if current_user.role == "doctor":

        if order.doctor_id != current_user.doctor_id:

            flash(
                "You are not authorized to confirm this order.",
                "danger"
            )

            return redirect(
                url_for(
                    "orders.all_orders"
                )
            )

    # =====================================================
    # STATUS CHECK
    # =====================================================

    if order.status != "pending":

        flash(
            "This order has already been processed.",
            "warning"
        )

        return redirect(
            url_for(
                "orders.view_order",
                order_id=order.id
            )
        )

    # =====================================================
    # PATIENT CHECK
    # =====================================================

    patient = Patient.query.get(
        order.patient_id
    )

    if not patient:

        flash(
            "Order patient was not found.",
            "danger"
        )

        return redirect(
            url_for(
                "orders.view_order",
                order_id=order.id
            )
        )

    # =====================================================
    # PROCESS ORDER
    # =====================================================

    try:

        for item in order.items:

            # -------------------------------------------------
            # GET MEDICINE
            # -------------------------------------------------

            medicine = (
                Medicine.query
                .filter(
                    Medicine.id == item.medicine_id,
                    Medicine.doctor_id == order.doctor_id,
                    Medicine.is_active.is_(True)
                )
                .with_for_update()
                .first()
            )

            if not medicine:

                raise ValueError(
                    f"Medicine '{item.medicine_name}' "
                    f"is no longer available."
                )

            required_quantity = int(
                item.quantity
            )

            # -------------------------------------------------
            # GET ACTIVE BATCHES
            #
            # FEFO = First Expiry First Out
            # -------------------------------------------------

            batches = (
                MedicineBatch.query
                .filter(
                    MedicineBatch.medicine_id == medicine.id,
                    MedicineBatch.is_active.is_(True),
                    MedicineBatch.quantity > 0
                )
                .order_by(
                    MedicineBatch.expiry_date.asc().nullslast(),
                    MedicineBatch.id.asc()
                )
                .with_for_update()
                .all()
            )

            # -------------------------------------------------
            # TOTAL BATCH STOCK
            # -------------------------------------------------

            total_batch_stock = sum(
                int(batch.quantity or 0)
                for batch in batches
            )

            if total_batch_stock < required_quantity:

                raise ValueError(
                    f"Insufficient batch stock for "
                    f"{medicine.medicine_name}. "
                    f"Available: {total_batch_stock}, "
                    f"Required: {required_quantity}."
                )

            # -------------------------------------------------
            # DISPENSE FROM BATCHES
            # -------------------------------------------------

            remaining_quantity = required_quantity

            for batch in batches:

                if remaining_quantity <= 0:
                    break

                available = int(
                    batch.quantity or 0
                )

                if available <= 0:
                    continue

                dispense_quantity = min(
                    available,
                    remaining_quantity
                )

                # ---------------------------------------------
                # BATCH UNIT PRICE
                # ---------------------------------------------

                unit_price = Decimal(
                    str(
                        batch.selling_price or 0
                    )
                )

                total_amount = (
                    unit_price
                    *
                    Decimal(dispense_quantity)
                )

                # ---------------------------------------------
                # CREATE MEDICINE PROVISION HISTORY
                # ---------------------------------------------
                provision = MedicineProvision(
                    order_item_id=item.id,

                    batch_id=batch.id,

                    medicine_id=medicine.id,

                    patient_id=order.patient_id,

                    patient_name=order.patient_name,
                    patient_code=order.patient_code,

                    doctor_id=order.doctor_id,

                    bill_id=None,

                    quantity=dispense_quantity,

                    unit_price=unit_price,

                    total_amount=total_amount,

                    provision_status="provided",

                    payment_status="pending",

                    notes=f"Provided through Order {order.order_code}",

                    provided_at=datetime.utcnow()
                )

                db.session.add(
                provision
                )

                # ---------------------------------------------
                # REDUCE BATCH STOCK
                # ---------------------------------------------

                batch.quantity -= dispense_quantity

                if batch.quantity <= 0:

                    batch.quantity = 0

                    batch.is_active = False

                remaining_quantity -= dispense_quantity

            # -------------------------------------------------
            # SAFETY CHECK
            # -------------------------------------------------

            if remaining_quantity > 0:

                raise ValueError(
                    f"Unable to fulfill "
                    f"{medicine.medicine_name}."
                )

            # -------------------------------------------------
            # UPDATE MEDICINE TOTAL STOCK
            # -------------------------------------------------

            medicine.quantity = sum(
                int(batch.quantity or 0)
                for batch in medicine.batches
                if batch.is_active
            )

        # =====================================================
        # UPDATE ORDER
        # =====================================================

        order.status = "confirmed"

        order.confirmed_at = datetime.utcnow()

        # =====================================================
        # SAVE EVERYTHING
        # =====================================================

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "ORDER CONFIRM ERROR:",
            repr(e)
        )

        flash(
            f"Unable to confirm order: {str(e)}",
            "danger"
        )

        return redirect(
            url_for(
                "orders.view_order",
                order_id=order.id
            )
        )

    # =====================================================
    # SUCCESS
    # =====================================================

    flash(
        f"Order {order.order_code} confirmed successfully. "
        f"Medicine stock has been reduced and "
        f"medicine history has been created.",
        "success"
    )

    return redirect(
        url_for(
            "orders.view_order",
            order_id=order.id
        )
    )
# =========================================================
# CANCEL ORDER
# =========================================================

@orders_bp.route(
    "/cancel/<int:order_id>",
    methods=["POST"]
)
@login_required
@role_required(
    "super_admin",
    "doctor"
)
def cancel_order(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    # =====================================================
    # DOCTOR OWNERSHIP CHECK
    # =====================================================

    if current_user.role == "doctor":

        if order.doctor_id != current_user.doctor_id:

            flash(
                "You are not authorized to cancel this order.",
                "danger"
            )

            return redirect(
                url_for(
                    "orders.all_orders"
                )
            )

    # =====================================================
    # STATUS CHECK
    # =====================================================

    if order.status != "pending":

        flash(
            "Only pending orders can be cancelled.",
            "warning"
        )

        return redirect(
            url_for(
                "orders.view_order",
                order_id=order.id
            )
        )

    # =====================================================
    # CANCEL
    # =====================================================

    try:

        order.status = "cancelled"

        order.cancelled_at = datetime.utcnow()

        db.session.commit()

        flash(
            f"Order {order.order_code} cancelled successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print(
            "ORDER CANCEL ERROR:",
            e
        )

        flash(
            "Unable to cancel order.",
            "danger"
        )

    return redirect(
        url_for(
            "orders.view_order",
            order_id=order.id
        )
    )

