from datetime import date, datetime
from decimal import Decimal
import re
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

from models.medicine import Medicine
from models.patient import Patient
from models.medicine_provision import MedicineProvision
from models.medicine_batch import MedicineBatch
from models.order import OrderItem


# =====================================================
# BLUEPRINT
# =====================================================

medicines_bp = Blueprint(
    "medicines",
    __name__,
    url_prefix="/medicines"
)


# =====================================================
# DOCTOR ACCESS CHECK
# =====================================================

def doctor_required():

    if not current_user.is_authenticated:
        return False

    return current_user.role == "doctor"


# =====================================================
# GENERATE MEDICINE-SPECIFIC BATCH NUMBER
# =====================================================

def generate_batch_number(medicine):
    """
    Generate medicine-specific batch number.

    Examples:

        Pandol      -> PAND01
        Pandol      -> PAND02
        Pandol      -> PAND03

        Brufen      -> BRUF01
        Brufen      -> BRUF02

        Amoxicillin -> AMOX01
        Amoxicillin -> AMOX02
    """

    # -------------------------------------------------
    # GET MEDICINE NAME
    # -------------------------------------------------

    name = (
        medicine.medicine_name or ""
    ).strip().upper()

    # -------------------------------------------------
    # KEEP ONLY ENGLISH LETTERS
    # -------------------------------------------------

    prefix = re.sub(
        r"[^A-Z]",
        "",
        name
    )

    # -------------------------------------------------
    # MINIMUM 4 CHARACTERS
    # -------------------------------------------------

    if len(prefix) < 4:

        prefix = prefix.ljust(
            4,
            "X"
        )

    # -------------------------------------------------
    # ONLY FIRST 4 LETTERS
    # -------------------------------------------------

    prefix = prefix[:4]

    # -------------------------------------------------
    # GET EXISTING BATCHES
    # FOR THIS MEDICINE ONLY
    # -------------------------------------------------

    existing_batches = (
        MedicineBatch.query
        .filter_by(
            medicine_id=medicine.id
        )
        .all()
    )

    max_number = 0

    # -------------------------------------------------
    # FIND HIGHEST EXISTING NUMBER
    # -------------------------------------------------

    for batch in existing_batches:

        existing_batch_number = (
            batch.batch_number or ""
        ).strip().upper()

        if existing_batch_number.startswith(prefix):

            number_part = (
                existing_batch_number[
                    len(prefix):
                ]
            )

            if number_part.isdigit():

                max_number = max(
                    max_number,
                    int(number_part)
                )

    # -------------------------------------------------
    # NEXT NUMBER
    # -------------------------------------------------

    next_number = max_number + 1

    # -------------------------------------------------
    # FINAL BATCH NUMBER
    # -------------------------------------------------

    return f"{prefix}{next_number:02d}"


# =====================================================
# MY MEDICINES
# =====================================================

@medicines_bp.route("/")
@login_required
def my_medicines():

    if not doctor_required():

        flash(
            "You are not authorized to access medicines.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    doctor_id = current_user.doctor_id

    medicines = (
        Medicine.query
        .filter_by(
            doctor_id=doctor_id
        )
        .order_by(
            Medicine.medicine_name.asc()
        )
        .all()
    )

    # -------------------------------------------------
    # SYNC TOTAL STOCK FROM ACTIVE BATCHES
    # -------------------------------------------------

    for medicine in medicines:

        medicine.quantity = sum(
            int(batch.quantity or 0)
            for batch in medicine.batches
            if batch.is_active
        )

    return render_template(
        "medicines/my_medicines.html",
        medicines=medicines
    )


# =====================================================
# ADD MEDICINE
# =====================================================

@medicines_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
def add_medicine():

    # =================================================
    # DOCTOR ACCESS CHECK
    # =================================================

    if not doctor_required():

        flash(
            "You are not authorized to add medicines.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    # =================================================
    # POST
    # =================================================

    if request.method == "POST":

        # -------------------------------------------------
        # MEDICINE INFORMATION
        # -------------------------------------------------

        medicine_name = request.form.get(
            "medicine_name",
            ""
        ).strip()

        generic_name = request.form.get(
            "generic_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        strength = request.form.get(
            "strength",
            ""
        ).strip()

        unit = request.form.get(
            "unit",
            ""
        ).strip()

        # -------------------------------------------------
        # BATCH INFORMATION
        # -------------------------------------------------

        supplier_name = request.form.get(
            "supplier_name",
            ""
        ).strip()

        quantity_value = request.form.get(
            "quantity",
            ""
        ).strip()

        purchase_price_value = request.form.get(
            "purchase_price",
            ""
        ).strip()

        selling_price_value = request.form.get(
            "selling_price",
            ""
        ).strip()

        expiry_date_value = request.form.get(
            "expiry_date",
            ""
        ).strip()

        # =================================================
        # MEDICINE NAME VALIDATION
        # =================================================

        if not medicine_name:

            flash(
                "Medicine name is required.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # UNIT VALIDATION
        # =================================================

        if not unit:

            flash(
                "Please select a medicine unit.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # QUANTITY VALIDATION
        # =================================================

        try:

            quantity = int(
                quantity_value
            )

            if quantity <= 0:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Quantity must be greater than 0.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # PURCHASE PRICE VALIDATION
        # =================================================

        try:

            purchase_price = Decimal(
                purchase_price_value
            )

            if purchase_price < 0:
                raise ValueError

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            flash(
                "Purchase price must be a valid number.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # SELLING PRICE VALIDATION
        # =================================================

        try:

            selling_price = Decimal(
                selling_price_value
            )

            if selling_price < 0:
                raise ValueError

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            flash(
                "Selling price must be a valid number.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # PRICE VALIDATION
        # =================================================

        if selling_price < purchase_price:

            flash(
                "Selling price cannot be lower than purchase price.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # EXPIRY DATE VALIDATION
        # =================================================

        if not expiry_date_value:

            flash(
                "Expiry date is required.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        try:

            parsed_expiry_date = date.fromisoformat(
                expiry_date_value
            )

        except ValueError:

            flash(
                "Invalid expiry date.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # EXPIRY DATE MUST BE FUTURE
        # =================================================

        if parsed_expiry_date <= date.today():

            flash(
                "Expiry date must be a future date.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # CHECK DOCTOR ID
        # =================================================

        doctor_id = getattr(
            current_user,
            "doctor_id",
            None
        )

        if not doctor_id:

            flash(
                "Your account is not linked to a doctor.",
                "danger"
            )

            return redirect(
                url_for(
                    "dashboard.dashboard"
                )
            )

        # =================================================
        # CREATE MEDICINE
        # =================================================

        medicine = Medicine(

            doctor_id=doctor_id,

            medicine_name=medicine_name,

            generic_name=(
                generic_name
                or None
            ),

            category=(
                category
                or None
            ),

            strength=(
                strength
                or None
            ),

            unit=unit,

            quantity=quantity,

            price=selling_price,

            expiry_date=parsed_expiry_date,

            is_active=True
        )

        # =================================================
        # SAVE MEDICINE + FIRST BATCH
        # =================================================

        try:

            # -------------------------------------------------
            # ADD MEDICINE
            # -------------------------------------------------

            db.session.add(
                medicine
            )

            # Medicine ID required
            db.session.flush()

            # -------------------------------------------------
            # GENERATE FIRST BATCH NUMBER
            # -------------------------------------------------

            batch_number = generate_batch_number(
                medicine
            )

            # -------------------------------------------------
            # CREATE FIRST BATCH
            # -------------------------------------------------

            batch = MedicineBatch(

                medicine_id=medicine.id,

                batch_number=batch_number,

                supplier_name=(
                    supplier_name
                    or None
                ),

                quantity=quantity,

                purchase_price=purchase_price,

                selling_price=selling_price,

                expiry_date=parsed_expiry_date,

                is_active=True
            )

            # -------------------------------------------------
            # ADD BATCH
            # -------------------------------------------------

            db.session.add(
                batch
            )

            # -------------------------------------------------
            # COMMIT BOTH
            # -------------------------------------------------

            db.session.commit()

        except Exception as e:

            # -------------------------------------------------
            # ROLLBACK
            # -------------------------------------------------

            db.session.rollback()

            print(
                "MEDICINE + BATCH ADD ERROR:",
                repr(e)
            )

            flash(
                "Unable to add medicine and batch. "
                "Please check the information and try again.",
                "danger"
            )

            return render_template(
                "medicines/add_medicine.html"
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"{medicine_name} added successfully. "
            f"Batch {batch_number} created with "
            f"Quantity: {quantity}, "
            f"Purchase Price: Rs. {purchase_price}, "
            f"Selling Price: Rs. {selling_price}.",
            "success"
        )

        # =================================================
        # REDIRECT
        # =================================================

        return redirect(
            url_for(
                "medicines.my_medicines"
            )
        )

    # =================================================
    # GET
    # =================================================

    return render_template(
        "medicines/add_medicine.html"
    )

# =====================================================
# ADD MEDICINE BATCH
# =====================================================

@medicines_bp.route(
    "/add-batch",
    methods=["GET", "POST"]
)
@login_required
def add_batch():

    # =================================================
    # DOCTOR ACCESS CHECK
    # =================================================

    if not doctor_required():

        flash(
            "You are not authorized to add medicine batches.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    # =================================================
    # GET DOCTOR'S MEDICINES
    # =================================================

    medicines = (
        Medicine.query
        .filter_by(
            doctor_id=current_user.doctor_id,
            is_active=True
        )
        .order_by(
            Medicine.medicine_name.asc()
        )
        .all()
    )

    # =================================================
    # POST
    # =================================================

    if request.method == "POST":

        # -------------------------------------------------
        # MEDICINE ID
        # -------------------------------------------------

        medicine_id = request.form.get(
            "medicine_id",
            ""
        ).strip()

        # -------------------------------------------------
        # QUANTITY
        # -------------------------------------------------

        quantity_value = request.form.get(
            "quantity",
            ""
        ).strip()

        # -------------------------------------------------
        # PURCHASE PRICE
        # -------------------------------------------------

        purchase_price_value = request.form.get(
            "purchase_price",
            ""
        ).strip()

        # -------------------------------------------------
        # SELLING PRICE
        # -------------------------------------------------

        selling_price_value = request.form.get(
            "selling_price",
            ""
        ).strip()

        # -------------------------------------------------
        # EXPIRY DATE
        # -------------------------------------------------

        expiry_date_value = request.form.get(
            "expiry_date",
            ""
        ).strip()

             # -------------------------------------------------
             #     supplier_name
             # -------------------------------------------------

        supplier_name = request.form.get(
            "supplier_name",
            ""
        ).strip()

        # =================================================
        # MEDICINE VALIDATION
        # =================================================

        if not medicine_id:

            flash(
                "Please select a medicine.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number="",
                selected_medicine_id=medicine_id
            )

        try:

            medicine_id = int(
                medicine_id
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Invalid medicine selected.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number="",
                selected_medicine_id=medicine_id
            )

        # =================================================
        # GET MEDICINE
        # =================================================

        medicine = (
            Medicine.query
            .filter_by(
                id=medicine_id,
                doctor_id=current_user.doctor_id,
                is_active=True
            )
            .first()
        )

        if not medicine:

            flash(
                "Selected medicine was not found.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number="",
                selected_medicine_id=medicine_id
            )

        # =================================================
        # AUTO GENERATE BATCH NUMBER
        # =================================================

        batch_number = generate_batch_number(
            medicine
        )

        # =================================================
        # QUANTITY VALIDATION
        # =================================================

        try:

            quantity = int(
                quantity_value
            )

            if quantity <= 0:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Quantity must be greater than 0.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number=batch_number,
                selected_medicine_id=medicine_id
            )

        # =================================================
        # PURCHASE PRICE VALIDATION
        # =================================================

        try:

            purchase_price = Decimal(
                purchase_price_value
            )

            if purchase_price < 0:
                raise ValueError

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            flash(
                "Purchase price must be a valid number.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number=batch_number,
                selected_medicine_id=medicine_id
            )

        # =================================================
        # SELLING PRICE VALIDATION
        # =================================================

        try:

            selling_price = Decimal(
                selling_price_value
            )

            if selling_price < 0:
                raise ValueError

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            flash(
                "Selling price must be a valid number.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number=batch_number,
                selected_medicine_id=medicine_id
            )

        # =================================================
        # PRICE VALIDATION
        # =================================================

        if selling_price < purchase_price:

            flash(
                "Selling price cannot be lower than purchase price.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number=batch_number,
                selected_medicine_id=medicine_id
            )

        # =================================================
        # EXPIRY DATE
        # =================================================

        parsed_expiry_date = None

        if expiry_date_value:

            try:

                parsed_expiry_date = date.fromisoformat(
                    expiry_date_value
                )

            except ValueError:

                flash(
                    "Invalid expiry date.",
                    "danger"
                )

                return render_template(
                    "medicines/add_batch.html",
                    medicines=medicines,
                    next_batch_number=batch_number,
                    selected_medicine_id=medicine_id
                )

        # =================================================
        # CREATE BATCH
        # =================================================

        batch = MedicineBatch(

            medicine_id=medicine.id,

            batch_number=batch_number,

            quantity=quantity,

            supplier_name=supplier_name,

            purchase_price=purchase_price,

            selling_price=selling_price,

            expiry_date=parsed_expiry_date,

            is_active=True
        )

        # =================================================
        # SAVE BATCH + UPDATE TOTAL STOCK
        # =================================================

        try:

            db.session.add(
                batch
            )

            # Get batch ID and update relationship
            db.session.flush()

            # -------------------------------------------------
            # IMPORTANT:
            # Medicine.quantity = SUM of active batch stock
            # -------------------------------------------------

            medicine.quantity = sum(
                int(b.quantity or 0)
                for b in medicine.batches
                if b.is_active
            )

            # -------------------------------------------------
            # KEEP LEGACY PRICE UPDATED
            # -------------------------------------------------

            active_batches = [
                b
                for b in medicine.batches
                if b.is_active
            ]

            if active_batches:

                active_batches.sort(
                    key=lambda b: b.id
                )

                first_batch = active_batches[0]

                medicine.price = (
                    first_batch.selling_price or 0
                )

                # -------------------------------------------------
                # EARLIEST EXPIRY
                # -------------------------------------------------

                batches_with_expiry = [
                    b
                    for b in active_batches
                    if b.expiry_date is not None
                ]

                if batches_with_expiry:

                    earliest_batch = min(
                        batches_with_expiry,
                        key=lambda b: b.expiry_date
                    )

                    medicine.expiry_date = (
                        earliest_batch.expiry_date
                    )

                else:

                    medicine.expiry_date = None

            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "MEDICINE BATCH ERROR:",
                repr(e)
            )

            flash(
                "Unable to add medicine batch. Please try again.",
                "danger"
            )

            return render_template(
                "medicines/add_batch.html",
                medicines=medicines,
                next_batch_number=batch_number,
                selected_medicine_id=medicine_id
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"Batch {batch_number} added successfully. "
            f"Quantity: {quantity}, "
            f"Purchase Price: Rs. {purchase_price}, "
            f"Selling Price: Rs. {selling_price}",
            "success"
        )

        return redirect(
            url_for(
                "medicines.my_medicines"
            )
        )

    # =================================================
    # GET
    # =================================================

    selected_medicine_id = request.args.get(
        "medicine_id",
        ""
    )

    next_batch_number = ""

    # -------------------------------------------------
    # IF MEDICINE IS SELECTED
    # -------------------------------------------------

    if selected_medicine_id:

        try:

            selected_id = int(
                selected_medicine_id
            )

            selected_medicine = (
                Medicine.query
                .filter_by(
                    id=selected_id,
                    doctor_id=current_user.doctor_id,
                    is_active=True
                )
                .first()
            )

            if selected_medicine:

                next_batch_number = (
                    generate_batch_number(
                        selected_medicine
                    )
                )

        except (
            ValueError,
            TypeError
        ):

            next_batch_number = ""

    return render_template(
        "medicines/add_batch.html",
        medicines=medicines,
        selected_medicine_id=selected_medicine_id,
        next_batch_number=next_batch_number
    )


# =====================================================
# GET NEXT BATCH NUMBER
# =====================================================

@medicines_bp.route(
    "/next-batch-number/<int:medicine_id>",
    methods=["GET"]
)
@login_required
def next_batch_number(medicine_id):

    # -------------------------------------------------
    # DOCTOR ACCESS CHECK
    # -------------------------------------------------

    if not doctor_required():

        return {
            "success": False,
            "message": "Unauthorized"
        }, 403

    # -------------------------------------------------
    # GET MEDICINE
    # -------------------------------------------------

    medicine = (
        Medicine.query
        .filter_by(
            id=medicine_id,
            doctor_id=current_user.doctor_id,
            is_active=True
        )
        .first()
    )

    if not medicine:

        return {
            "success": False,
            "message": "Medicine not found"
        }, 404

    # -------------------------------------------------
    # GENERATE NEXT BATCH
    # -------------------------------------------------

    batch_number = generate_batch_number(
        medicine
    )

    return {
        "success": True,
        "batch_number": batch_number
    }


# =========================================================
# EDIT MEDICINE BATCH
# =========================================================

@medicines_bp.route(
    "/edit-batch/<int:batch_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_batch(batch_id):

    # -----------------------------------------------------
    # DOCTOR CHECK
    # -----------------------------------------------------

    if not doctor_required():

        flash(
            "You are not authorized to edit medicine batches.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    # -----------------------------------------------------
    # GET BATCH
    # -----------------------------------------------------

    batch = (
        MedicineBatch.query
        .join(Medicine)
        .filter(
            MedicineBatch.id == batch_id,
            Medicine.doctor_id == current_user.doctor_id
        )
        .first_or_404()
    )

    medicine = batch.medicine

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        # -------------------------------------------------
        # QUANTITY
        # -------------------------------------------------

        quantity_raw = request.form.get(
            "quantity",
            ""
        ).strip()

        # -------------------------------------------------
        # SUPPLIER / PURCHASED FROM
        # -------------------------------------------------

        supplier_name = request.form.get(
            "supplier_name",
            ""
        ).strip()

        # -------------------------------------------------
        # PURCHASE PRICE
        # -------------------------------------------------

        purchase_price_raw = request.form.get(
            "purchase_price",
            ""
        ).strip()

        # -------------------------------------------------
        # SELLING PRICE
        # -------------------------------------------------

        selling_price_raw = request.form.get(
            "selling_price",
            ""
        ).strip()

        # -------------------------------------------------
        # EXPIRY DATE
        # -------------------------------------------------

        expiry_date_raw = request.form.get(
            "expiry_date",
            ""
        ).strip()

        # -------------------------------------------------
        # ACTIVE STATUS
        # -------------------------------------------------

        is_active = (
            request.form.get("is_active") == "on"
        )

        # =================================================
        # QUANTITY VALIDATION
        # =================================================

        try:

            quantity = int(
                quantity_raw
            )

            if quantity < 0:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Quantity must be a valid number greater than or equal to 0.",
                "danger"
            )

            return render_template(
                "medicines/edit_batch.html",
                batch=batch,
                medicine=medicine
            )

        # =================================================
        # PURCHASE PRICE VALIDATION
        # =================================================

        try:

            purchase_price = Decimal(
                purchase_price_raw or "0"
            )

            if purchase_price < 0:
                raise ValueError

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            flash(
                "Purchase price must be a valid amount.",
                "danger"
            )

            return render_template(
                "medicines/edit_batch.html",
                batch=batch,
                medicine=medicine
            )

        # =================================================
        # SELLING PRICE VALIDATION
        # =================================================

        try:

            selling_price = Decimal(
                selling_price_raw or "0"
            )

            if selling_price < 0:
                raise ValueError

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            flash(
                "Selling price must be a valid amount.",
                "danger"
            )

            return render_template(
                "medicines/edit_batch.html",
                batch=batch,
                medicine=medicine
            )

        # =================================================
        # PRICE CHECK
        # =================================================

        if selling_price < purchase_price:

            flash(
                "Selling price cannot be lower than purchase price.",
                "danger"
            )

            return render_template(
                "medicines/edit_batch.html",
                batch=batch,
                medicine=medicine
            )

        # =================================================
        # EXPIRY DATE
        # =================================================

        parsed_expiry_date = None

        if expiry_date_raw:

            try:

                parsed_expiry_date = datetime.strptime(
                    expiry_date_raw,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid expiry date.",
                    "danger"
                )

                return render_template(
                    "medicines/edit_batch.html",
                    batch=batch,
                    medicine=medicine
                )

        # =================================================
        # UPDATE BATCH
        # =================================================

        batch.quantity = quantity

        batch.supplier_name = (
            supplier_name or None
        )

        batch.purchase_price = purchase_price

        batch.selling_price = selling_price

        batch.expiry_date = parsed_expiry_date

        batch.is_active = is_active

        # =================================================
        # RECALCULATE MEDICINE TOTAL STOCK
        # =================================================

        medicine.quantity = sum(
            int(b.quantity or 0)
            for b in medicine.batches
            if b.is_active
        )

        # =================================================
        # ACTIVE BATCHES
        # =================================================

        active_batches = [
            b
            for b in medicine.batches
            if b.is_active
        ]

        # =================================================
        # UPDATE LEGACY PRICE / EXPIRY
        # =================================================

        if active_batches:

            active_batches.sort(
                key=lambda b: b.id
            )

            first_batch = active_batches[0]

            medicine.price = (
                first_batch.selling_price or 0
            )

            # ---------------------------------------------
            # EARLIEST EXPIRY
            # ---------------------------------------------

            batches_with_expiry = [
                b
                for b in active_batches
                if b.expiry_date is not None
            ]

            if batches_with_expiry:

                earliest_batch = min(
                    batches_with_expiry,
                    key=lambda b: b.expiry_date
                )

                medicine.expiry_date = (
                    earliest_batch.expiry_date
                )

            else:

                medicine.expiry_date = None

        else:

            medicine.price = 0

            medicine.expiry_date = None

        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

            flash(
                f"Batch {batch.batch_number} updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "medicines.edit_medicine",
                    medicine_id=medicine.id
                )
            )

        except Exception as e:

            db.session.rollback()

            print(
                "BATCH UPDATE ERROR:",
                repr(e)
            )

            flash(
                f"Error updating batch: {str(e)}",
                "danger"
            )

    # =================================================
    # GET
    # =================================================

    return render_template(
        "medicines/edit_batch.html",
        batch=batch,
        medicine=medicine
    )

# =====================================================
# EDIT MEDICINE
# =====================================================

@medicines_bp.route(
    "/edit/<int:medicine_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_medicine(medicine_id):

    # =================================================
    # CORRECT DOCTOR CHECK
    # =================================================

    if not doctor_required():

        flash(
            "You are not authorized to edit medicines.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    # =================================================
    # GET MEDICINE
    # =================================================

    medicine = (
        Medicine.query
        .filter_by(
            id=medicine_id,
            doctor_id=current_user.doctor_id
        )
        .first_or_404()
    )

    # =================================================
    # MEDICINE HISTORY
    # =================================================

    medicine_history = (
        MedicineProvision.query
        .filter(
            MedicineProvision.medicine_id == medicine.id,
            MedicineProvision.doctor_id == current_user.doctor_id
        )
        .order_by(
            MedicineProvision.provided_at.desc()
        )
        .all()
    )

    # =================================================
    # UPDATE MEDICINE
    # =================================================

    if request.method == "POST":

        medicine_name = request.form.get(
            "medicine_name",
            ""
        ).strip()

        generic_name = request.form.get(
            "generic_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        strength = request.form.get(
            "strength",
            ""
        ).strip()

        unit = request.form.get(
            "unit",
            "Tablet"
        ).strip()

        is_active = (
            request.form.get("is_active") == "on"
        )

        # =================================================
        # VALIDATION
        # =================================================

        if not medicine_name:

            flash(
                "Medicine name is required.",
                "danger"
            )

            return render_template(
                "medicines/edit_medicine.html",
                medicine=medicine,
                medicine_history=medicine_history,
                today=date.today()
            )

        if not unit:

            flash(
                "Medicine unit is required.",
                "danger"
            )

            return render_template(
                "medicines/edit_medicine.html",
                medicine=medicine,
                medicine_history=medicine_history
            )

        # =================================================
        # UPDATE BASE MEDICINE INFORMATION
        # =================================================

        medicine.medicine_name = medicine_name

        medicine.generic_name = (
            generic_name
            if generic_name
            else None
        )

        medicine.category = (
            category
            if category
            else None
        )

        medicine.strength = (
            strength
            if strength
            else None
        )

        medicine.unit = unit

        medicine.is_active = is_active

        # =================================================
        # RECALCULATE TOTAL STOCK
        # =================================================

        medicine.quantity = sum(
            int(batch.quantity or 0)
            for batch in medicine.batches
            if batch.is_active
        )

        # =================================================
        # SYNCHRONIZE LEGACY PRICE / EXPIRY
        # =================================================

        active_batches = [
            batch
            for batch in medicine.batches
            if batch.is_active
        ]

        if active_batches:

            # -------------------------------------------------
            # FIRST ACTIVE BATCH
            # -------------------------------------------------

            active_batches.sort(
                key=lambda batch: batch.id
            )

            first_batch = active_batches[0]

            medicine.price = (
                first_batch.selling_price or 0
            )

            # -------------------------------------------------
            # EARLIEST EXPIRY
            # -------------------------------------------------

            batches_with_expiry = [
                batch
                for batch in active_batches
                if batch.expiry_date is not None
            ]

            if batches_with_expiry:

                earliest_batch = min(
                    batches_with_expiry,
                    key=lambda batch: batch.expiry_date
                )

                medicine.expiry_date = (
                    earliest_batch.expiry_date
                )

            else:

                medicine.expiry_date = None

        else:

            medicine.price = 0

            medicine.expiry_date = None

        # =================================================
        # SAVE
        # =================================================

        try:

            db.session.commit()

            flash(
                "Medicine information updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "medicines.edit_medicine",
                    medicine_id=medicine.id
                )
            )

        except Exception as e:

            db.session.rollback()

            print(
                "MEDICINE UPDATE ERROR:",
                repr(e)
            )

            flash(
                f"Error updating medicine: {str(e)}",
                "danger"
            )

    # =================================================
    # GET REQUEST
    # =================================================

    return render_template(
        "medicines/edit_medicine.html",
        medicine=medicine,
        medicine_history=medicine_history
    )

# =========================================================
# PERMANENTLY DELETE MEDICINE
# =========================================================

@medicines_bp.route("/delete/<int:medicine_id>", methods=["POST"])
@login_required
def delete_medicine(medicine_id):

    if not doctor_required():
        flash("You are not authorized to delete medicines.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    medicine = (
        Medicine.query
        .filter(
            Medicine.id == medicine_id,
            Medicine.doctor_id == current_user.doctor_id
        )
        .first_or_404()
    )

    try:
        # -------------------------------------------------
        # 1. Delete medicine provisions/history
        # -------------------------------------------------
        MedicineProvision.query.filter(
            MedicineProvision.medicine_id == medicine.id
        ).delete(synchronize_session=False)

        # -------------------------------------------------
        # 2. Delete order items related to this medicine
        # -------------------------------------------------
        OrderItem.query.filter(
            OrderItem.medicine_id == medicine.id
        ).delete(synchronize_session=False)

        # -------------------------------------------------
        # 3. Delete all batches
        # -------------------------------------------------
        MedicineBatch.query.filter(
            MedicineBatch.medicine_id == medicine.id
        ).delete(synchronize_session=False)

        # -------------------------------------------------
        # 4. Delete medicine itself
        # -------------------------------------------------
        medicine_name = medicine.medicine_name

        db.session.delete(medicine)

        db.session.commit()

        flash(
            f"Medicine '{medicine_name}' has been permanently deleted.",
            "success"
        )

    except Exception as e:
        db.session.rollback()

        print("PERMANENT MEDICINE DELETE ERROR:", repr(e))

        flash(
            f"Unable to delete medicine: {str(e)}",
            "danger"
        )

    return redirect(url_for("medicines.my_medicines"))
# =====================================================
# PROVIDE MEDICINE - BATCH WISE / FEFO
# =====================================================

@medicines_bp.route(
    "/provide/<int:medicine_id>",
    methods=["GET", "POST"]
)
@login_required
def provide_medicine(medicine_id):

    # =================================================
    # DOCTOR ACCESS CHECK
    # =================================================

    if not doctor_required():

        flash(
            "You are not authorized to provide medicines.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    # =================================================
    # GET MEDICINE
    # =================================================

    medicine = (
        Medicine.query
        .filter_by(
            id=medicine_id,
            doctor_id=current_user.doctor_id
        )
        .first_or_404()
    )

    # =================================================
    # GET PATIENTS
    # =================================================

    patients = (
        Patient.query
        .order_by(
            Patient.full_name.asc()
        )
        .all()
    )

    # =================================================
    # POST
    # =================================================

    if request.method == "POST":

        patient_id = request.form.get(
            "patient_id"
        )

        quantity_value = request.form.get(
            "quantity",
            "1"
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
                "medicines/provide_medicine.html",
                medicine=medicine,
                patients=patients
            )

        try:

            patient_id = int(
                patient_id
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Invalid patient selected.",
                "danger"
            )

            return render_template(
                "medicines/provide_medicine.html",
                medicine=medicine,
                patients=patients
            )

        # =================================================
        # GET PATIENT
        # =================================================

        patient = Patient.query.get(
            patient_id
        )

        if not patient:

            flash(
                "Selected patient was not found.",
                "danger"
            )

            return render_template(
                "medicines/provide_medicine.html",
                medicine=medicine,
                patients=patients
            )

        # =================================================
        # QUANTITY VALIDATION
        # =================================================

        try:

            quantity = int(
                quantity_value
            )

            if quantity <= 0:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Quantity must be a valid number greater than 0.",
                "danger"
            )

            return render_template(
                "medicines/provide_medicine.html",
                medicine=medicine,
                patients=patients
            )

        # =================================================
        # GET AVAILABLE ACTIVE BATCHES
        #
        # FEFO:
        # First Expiry, First Out
        # =================================================

        batches = (
            MedicineBatch.query
            .filter(
                MedicineBatch.medicine_id == medicine.id,
                MedicineBatch.quantity > 0,
                MedicineBatch.is_active.is_(True)
            )
            .order_by(
                MedicineBatch.expiry_date.is_(None).asc(),
                MedicineBatch.expiry_date.asc(),
                MedicineBatch.id.asc()
            )
            .with_for_update()
            .all()
        )

        # =================================================
        # TOTAL AVAILABLE STOCK
        # =================================================

        total_available = sum(
            int(batch.quantity or 0)
            for batch in batches
        )

        # =================================================
        # NO STOCK
        # =================================================

        if total_available <= 0:

            flash(
                "This medicine is out of stock.",
                "danger"
            )

            return redirect(
                url_for(
                    "medicines.my_medicines"
                )
            )

        # =================================================
        # INSUFFICIENT STOCK
        # =================================================

        if quantity > total_available:

            flash(
                f"Only {total_available} units are available "
                f"across all batches.",
                "danger"
            )

            return render_template(
                "medicines/provide_medicine.html",
                medicine=medicine,
                patients=patients
            )

        # =================================================
        # REMAINING QUANTITY
        # =================================================

        remaining_quantity = quantity

        # =================================================
        # GRAND TOTAL
        # =================================================

        grand_total = Decimal(
            "0.00"
        )

        # =================================================
        # CREATE PROVISIONS BATCH BY BATCH
        # =================================================

        try:

            for batch in batches:

                # -------------------------------------------------
                # STOP WHEN COMPLETE
                # -------------------------------------------------

                if remaining_quantity <= 0:
                    break

                batch_stock = int(
                    batch.quantity or 0
                )

                if batch_stock <= 0:
                    continue

                # -------------------------------------------------
                # QUANTITY FROM THIS BATCH
                # -------------------------------------------------

                take_quantity = min(
                    remaining_quantity,
                    batch_stock
                )

                # -------------------------------------------------
                # BATCH SELLING PRICE
                # -------------------------------------------------

                unit_price = Decimal(
                    str(
                        batch.selling_price or 0
                    )
                )

                # -------------------------------------------------
                # BATCH TOTAL
                # -------------------------------------------------

                batch_total = (
                    unit_price
                    *
                    Decimal(take_quantity)
                )

                # -------------------------------------------------
                # CREATE PROVISION
                # -------------------------------------------------

                provision = MedicineProvision(

                    medicine_id=medicine.id,

                    batch_id=batch.id,

                    patient_id=patient.id,

                    doctor_id=current_user.doctor_id,

                    bill_id=None,

                    quantity=take_quantity,

                    unit_price=unit_price,

                    total_amount=batch_total,

                    provision_status="provided",

                    payment_status="pending",

                    provided_at=datetime.utcnow(),

                    notes=notes or None
                )

                db.session.add(
                    provision
                )

                # -------------------------------------------------
                # REDUCE BATCH STOCK
                # -------------------------------------------------

                batch.quantity = (
                    batch_stock
                    -
                    take_quantity
                )

                # -------------------------------------------------
                # UPDATE REMAINING
                # -------------------------------------------------

                remaining_quantity -= (
                    take_quantity
                )

                # -------------------------------------------------
                # UPDATE TOTAL
                # -------------------------------------------------

                grand_total += (
                    batch_total
                )

            # =================================================
            # SAFETY CHECK
            # =================================================

            if remaining_quantity > 0:

                raise ValueError(
                    "Unable to allocate the requested quantity "
                    "from available batches."
                )

            # =================================================
            # RECALCULATE MEDICINE TOTAL STOCK
            # =================================================

            medicine.quantity = sum(
                int(batch.quantity or 0)
                for batch in MedicineBatch.query.filter(
                    MedicineBatch.medicine_id == medicine.id,
                    MedicineBatch.is_active.is_(True)
                ).all()
            )

            # =================================================
            # UPDATE LEGACY PRICE
            # =================================================

            active_batches = (
                MedicineBatch.query
                .filter(
                    MedicineBatch.medicine_id == medicine.id,
                    MedicineBatch.is_active.is_(True)
                )
                .order_by(
                    MedicineBatch.id.asc()
                )
                .all()
            )

            if active_batches:

                medicine.price = (
                    active_batches[0].selling_price or 0
                )

                # -------------------------------------------------
                # EARLIEST EXPIRY
                # -------------------------------------------------

                batches_with_expiry = [
                    batch
                    for batch in active_batches
                    if batch.expiry_date is not None
                ]

                if batches_with_expiry:

                    earliest_batch = min(
                        batches_with_expiry,
                        key=lambda batch: batch.expiry_date
                    )

                    medicine.expiry_date = (
                        earliest_batch.expiry_date
                    )

                else:

                    medicine.expiry_date = None

            else:

                medicine.price = 0

                medicine.expiry_date = None

            # =================================================
            # COMMIT
            # =================================================

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "BATCH MEDICINE PROVISION ERROR:",
                repr(e)
            )

            flash(
                "Unable to provide medicine. "
                "Please try again.",
                "danger"
            )

            return render_template(
                "medicines/provide_medicine.html",
                medicine=medicine,
                patients=patients
            )

        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"{medicine.medicine_name} provided successfully "
            f"to {patient.full_name}. "
            f"Quantity: {quantity}. "
            f"Amount: Rs. {grand_total:.2f}",
            "success"
        )

        # =================================================
        # REDIRECT
        # =================================================

        return redirect(
            url_for(
                "medicines.my_medicines"
            )
        )

    # =================================================
    # GET
    # =================================================

    return render_template(
        "medicines/provide_medicine.html",
        medicine=medicine,
        patients=patients
    )