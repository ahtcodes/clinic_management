from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # BASIC USER INFORMATION
    # =====================================================

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # =====================================================
    # USER ROLE
    # =====================================================

    role = db.Column(
        db.String(30),
        nullable=False,
        default="receptionist"
    )

    # =====================================================
    # DOCTOR LINK
    # =====================================================

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "doctors.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    doctor = db.relationship(
        "Doctor",
        backref="user",
        foreign_keys=[doctor_id]
    )

    # =====================================================
    # PATIENT LINK
    # =====================================================

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "patients.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    patient = db.relationship(
        "Patient",
        backref="user",
        foreign_keys=[patient_id]
    )

    # =====================================================
    # ACCOUNT STATUS
    # =====================================================

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # =====================================================
    # CREATED DATE
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # PASSWORD RESET
    # =====================================================

    reset_token = db.Column(
        db.String(255),
        unique=True,
        nullable=True
    )

    reset_token_expiry = db.Column(
        db.DateTime,
        nullable=True
    )

    # =====================================================
    # PASSWORD METHODS
    # =====================================================

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    # =====================================================
    # ROLE CHECK
    # =====================================================

    def has_role(self, *roles):

        return self.role.lower() in [
            role.lower()
            for role in roles
        ]

    # =====================================================
    # ROLE HELPERS
    # =====================================================

    def is_super_admin(self):

        return self.has_role(
            "super_admin"
        )

    def is_receptionist(self):

        return self.has_role(
            "receptionist"
        )

    def is_doctor(self):

        return self.has_role(
            "doctor"
        )

    def is_staff(self):

        return self.has_role(
            "staff"
        )

    def is_patient(self):

        return self.has_role(
            "patient"
        )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return f"<User {self.username}>"