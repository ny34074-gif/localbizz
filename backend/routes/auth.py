import secrets
import smtplib

from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import Blueprint, request, jsonify, session, current_app

from db import fetch, execute
from extensions import bcrypt


bp = Blueprint("auth", __name__)


# =========================================================
# OTP GENERATOR
# =========================================================

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


# =========================================================
# SEND EMAIL
# =========================================================

def send_email(to_email, subject, body):

    smtp_host = current_app.config["SMTP_HOST"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_email = current_app.config["SMTP_EMAIL"]
    smtp_password = current_app.config["SMTP_PASSWORD"]

    if not smtp_email or not smtp_password:
        raise RuntimeError(
            "SMTP settings are missing in .env"
        )

    message = EmailMessage()

    message["From"] = smtp_email
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as smtp:

        smtp.starttls()

        smtp.login(
            smtp_email,
            smtp_password
        )

        smtp.send_message(message)


# =========================================================
# REGISTER
# =========================================================

@bp.post("/register")
def register():

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "user").strip().lower()

    if role == "customer":
        role = "user"

    # Public registration never creates admin
    if role not in ("user", "business_owner"):
        role = "user"

    # -------------------------
    # VALIDATION
    # -------------------------

    if not name:
        return jsonify(
            success=False,
            message="Name is required."
        ), 400

    if not email:
        return jsonify(
            success=False,
            message="Email is required."
        ), 400

    if not password:
        return jsonify(
            success=False,
            message="Password is required."
        ), 400

    if len(password) < 6:
        return jsonify(
            success=False,
            message="Password must be at least 6 characters."
        ), 400

    # -------------------------
    # ALREADY REGISTERED
    # -------------------------

    existing_user = fetch(
        """
        SELECT id
        FROM users
        WHERE email=%s
        """,
        (email,),
        True
    )

    if existing_user:
        return jsonify(
            success=False,
            message="This email is already registered."
        ), 409

    # -------------------------
    # DELETE OLD OTP REQUEST
    # -------------------------

    execute(
        """
        DELETE FROM pending_registrations
        WHERE email=%s
        """,
        (email,)
    )

    # -------------------------
    # HASH PASSWORD
    # -------------------------

    password_hash = (
        bcrypt
        .generate_password_hash(password)
        .decode("utf-8")
    )

    # -------------------------
    # GENERATE OTP
    # -------------------------

    otp = generate_otp()

    otp_hash = (
        bcrypt
        .generate_password_hash(otp)
        .decode("utf-8")
    )

    expires_at = (
        datetime.now()
        + timedelta(
            minutes=current_app.config[
                "OTP_EXPIRY_MINUTES"
            ]
        )
    )

    # -------------------------
    # TEMPORARY REGISTRATION
    # IMPORTANT:
    # NOT inserted into users
    # -------------------------

    execute(
        """
        INSERT INTO pending_registrations
        (
            name,
            email,
            phone,
            password_hash,
            role,
            otp_hash,
            expires_at,
            attempts
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,0
        )
        """,
        (
            name,
            email,
            phone,
            password_hash,
            role,
            otp_hash,
            expires_at
        )
    )

    # -------------------------
    # SEND OTP
    # -------------------------

    try:

        send_email(
            email,
            "LocalBiz - Verify Your Email",
            f"""
Hello {name},

Your LocalBiz verification OTP is:

{otp}

This OTP will expire in
{current_app.config["OTP_EXPIRY_MINUTES"]} minutes.

Do not share this OTP with anyone.

Regards,
LocalBiz Team
"""
        )

    except Exception as error:

        execute(
            """
            DELETE FROM pending_registrations
            WHERE email=%s
            """,
            (email,)
        )

        print("Email error:", error)

        return jsonify(
            success=False,
            message="Unable to send OTP. Check SMTP settings in .env."
        ), 500

    return jsonify(
        success=True,
        message="OTP sent to your email.",
        email=email
    ), 201


# =========================================================
# VERIFY REGISTRATION OTP
# =========================================================

@bp.post("/verify-registration")
def verify_registration():

    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return jsonify(
            success=False,
            message="Email and OTP are required."
        ), 400

    pending = fetch(
        """
        SELECT *
        FROM pending_registrations
        WHERE email=%s
        """,
        (email,),
        True
    )

    if not pending:
        return jsonify(
            success=False,
            message="No pending registration found."
        ), 404

    # -------------------------
    # EXPIRY
    # -------------------------

    if datetime.now() > pending["expires_at"]:

        execute(
            """
            DELETE FROM pending_registrations
            WHERE id=%s
            """,
            (pending["id"],)
        )

        return jsonify(
            success=False,
            message="OTP expired. Please register again."
        ), 400

    # -------------------------
    # ATTEMPT LIMIT
    # -------------------------

    if pending["attempts"] >= 5:

        execute(
            """
            DELETE FROM pending_registrations
            WHERE id=%s
            """,
            (pending["id"],)
        )

        return jsonify(
            success=False,
            message="Too many incorrect attempts."
        ), 429

    # -------------------------
    # OTP CHECK
    # -------------------------

    if not bcrypt.check_password_hash(
        pending["otp_hash"],
        otp
    ):

        execute(
            """
            UPDATE pending_registrations
            SET attempts=attempts+1
            WHERE id=%s
            """,
            (pending["id"],)
        )

        return jsonify(
            success=False,
            message="Incorrect OTP."
        ), 400

    # -------------------------
    # DOUBLE CHECK EMAIL
    # -------------------------

    existing_user = fetch(
        """
        SELECT id
        FROM users
        WHERE email=%s
        """,
        (email,),
        True
    )

    if existing_user:

        execute(
            """
            DELETE FROM pending_registrations
            WHERE id=%s
            """,
            (pending["id"],)
        )

        return jsonify(
            success=False,
            message="This email is already registered."
        ), 409

    # -------------------------
    # ACTUAL USER CREATION
    # ONLY NOW!
    # -------------------------

    user_id = execute(
        """
        INSERT INTO users
        (
            name,
            email,
            password,
            phone,
            role
        )
        VALUES
        (
            %s,%s,%s,%s,%s
        )
        """,
        (
            pending["name"],
            pending["email"],
            pending["password_hash"],
            pending["phone"],
            pending["role"]
        )
    )

    # -------------------------
    # DELETE PENDING RECORD
    # -------------------------

    execute(
        """
        DELETE FROM pending_registrations
        WHERE id=%s
        """,
        (pending["id"],)
    )

    # -------------------------
    # AUTO LOGIN
    # -------------------------

    session["user_id"] = user_id
    session["role"] = pending["role"]
    session["name"] = pending["name"]

    return jsonify(
        success=True,
        message="Email verified and account created successfully.",
        user={
            "id": user_id,
            "name": pending["name"],
            "email": pending["email"],
            "role": pending["role"]
        }
    ), 201


# =========================================================
# LOGIN
# =========================================================

@bp.post("/login")
def login():

    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = fetch(
        """
        SELECT *
        FROM users
        WHERE email=%s
        """,
        (email,),
        True
    )

    # -------------------------
    # USER DOES NOT EXIST
    # -------------------------

    if not user:

        pending = fetch(
            """
            SELECT id
            FROM pending_registrations
            WHERE email=%s
            """,
            (email,),
            True
        )

        if pending:

            return jsonify(
                success=False,
                message="Please verify your email with OTP before logging in."
            ), 403

        return jsonify(
            success=False,
            message="Invalid email or password."
        ), 401

    # -------------------------
    # PASSWORD CHECK
    # -------------------------

    if not bcrypt.check_password_hash(
        user["password"],
        password
    ):

        return jsonify(
            success=False,
            message="Invalid email or password."
        ), 401

    # -------------------------
    # SESSION
    # -------------------------

    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["name"]

    return jsonify(
        success=True,
        message="Login successful.",
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"]
        }
    )


# =========================================================
# FORGOT PASSWORD - SEND OTP
# =========================================================

@bp.post("/forgot-password")
def forgot_password():

    data = request.get_json(silent=True) or {}

    email = (
        data.get("email") or ""
    ).strip().lower()

    if not email:
        return jsonify(
            success=False,
            message="Email is required."
        ), 400

    user = fetch(
        """
        SELECT id,name,email
        FROM users
        WHERE email=%s
        """,
        (email,),
        True
    )

    # Same response for unknown email
    if not user:

        return jsonify(
            success=True,
            message="If the email exists, an OTP has been sent."
        )

    # Remove old OTP
    execute(
        """
        DELETE FROM password_reset_otps
        WHERE email=%s
        """,
        (email,)
    )

    otp = generate_otp()

    otp_hash = (
        bcrypt
        .generate_password_hash(otp)
        .decode("utf-8")
    )

    expires_at = (
        datetime.now()
        + timedelta(
            minutes=current_app.config[
                "OTP_EXPIRY_MINUTES"
            ]
        )
    )

    execute(
        """
        INSERT INTO password_reset_otps
        (
            user_id,
            email,
            otp_hash,
            expires_at,
            attempts,
            used
        )
        VALUES
        (
            %s,%s,%s,%s,0,0
        )
        """,
        (
            user["id"],
            email,
            otp_hash,
            expires_at
        )
    )

    try:

        send_email(
            email,
            "LocalBiz - Password Reset OTP",
            f"""
Hello {user["name"]},

Your LocalBiz password reset OTP is:

{otp}

This OTP will expire in
{current_app.config["OTP_EXPIRY_MINUTES"]} minutes.

If you did not request this reset,
please ignore this email.

Regards,
LocalBiz Team
"""
        )

    except Exception as error:

        execute(
            """
            DELETE FROM password_reset_otps
            WHERE email=%s
            """,
            (email,)
        )

        print("Email error:", error)

        return jsonify(
            success=False,
            message="Unable to send reset OTP. Check SMTP settings."
        ), 500

    return jsonify(
        success=True,
        message="If the email exists, an OTP has been sent."
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@bp.post("/reset-password")
def reset_password():

    data = request.get_json(silent=True) or {}

    email = (
        data.get("email") or ""
    ).strip().lower()

    otp = (
        data.get("otp") or ""
    ).strip()

    new_password = (
        data.get("new_password") or ""
    )

    if not email or not otp or not new_password:

        return jsonify(
            success=False,
            message="Email, OTP and new password are required."
        ), 400

    if len(new_password) < 6:

        return jsonify(
            success=False,
            message="New password must be at least 6 characters."
        ), 400

    reset = fetch(
        """
        SELECT *
        FROM password_reset_otps
        WHERE email=%s
        AND used=0
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,),
        True
    )

    if not reset:

        return jsonify(
            success=False,
            message="No valid password reset request found."
        ), 404

    if datetime.now() > reset["expires_at"]:

        execute(
            """
            DELETE FROM password_reset_otps
            WHERE id=%s
            """,
            (reset["id"],)
        )

        return jsonify(
            success=False,
            message="OTP expired."
        ), 400

    if reset["attempts"] >= 5:

        return jsonify(
            success=False,
            message="Too many incorrect attempts."
        ), 429

    if not bcrypt.check_password_hash(
        reset["otp_hash"],
        otp
    ):

        execute(
            """
            UPDATE password_reset_otps
            SET attempts=attempts+1
            WHERE id=%s
            """,
            (reset["id"],)
        )

        return jsonify(
            success=False,
            message="Incorrect OTP."
        ), 400

    new_hash = (
        bcrypt
        .generate_password_hash(
            new_password
        )
        .decode("utf-8")
    )

    execute(
        """
        UPDATE users
        SET password=%s
        WHERE id=%s
        """,
        (
            new_hash,
            reset["user_id"]
        )
    )

    execute(
        """
        UPDATE password_reset_otps
        SET used=1
        WHERE id=%s
        """,
        (reset["id"],)
    )

    return jsonify(
        success=True,
        message="Password reset successfully."
    )


# =========================================================
# LOGOUT
# =========================================================

@bp.post("/logout")
def logout():

    session.clear()

    return jsonify(
        success=True,
        message="Logged out."
    )


# =========================================================
# CURRENT USER
# =========================================================

@bp.get("/me")
def me():

    if "user_id" not in session:

        return jsonify(
            success=False,
            message="Not logged in."
        ), 401

    user = fetch(
        """
        SELECT
            id,
            name,
            email,
            phone,
            role,
            created_at
        FROM users
        WHERE id=%s
        """,
        (session["user_id"],),
        True
    )

    if not user:

        session.clear()

        return jsonify(
            success=False,
            message="User not found."
        ), 404

    return jsonify(
        success=True,
        user=user
    )