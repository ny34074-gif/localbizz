import json

from flask import Blueprint, request, jsonify

from db import fetch, execute
from utils.auth import role_required


bp = Blueprint("admin", __name__)


# =========================================================
# JSON SAFE CONVERSION
# =========================================================

def json_safe(data):
    """
    Converts MySQL/Python values such as:
    timedelta, datetime, date, Decimal, etc.
    into JSON-safe values.
    """

    return json.loads(
        json.dumps(
            data,
            default=str
        )
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@bp.get("/dashboard")
@role_required("admin")
def dashboard():

    users = fetch(
        """
        SELECT COUNT(*) AS count
        FROM users
        """,
        one=True
    )

    businesses = fetch(
        """
        SELECT COUNT(*) AS count
        FROM businesses
        """,
        one=True
    )

    pending = fetch(
        """
        SELECT COUNT(*) AS count
        FROM businesses
        WHERE status='pending'
        """,
        one=True
    )

    reviews = fetch(
        """
        SELECT COUNT(*) AS count
        FROM reviews
        """,
        one=True
    )

    messages = fetch(
        """
        SELECT COUNT(*) AS count
        FROM messages
        """,
        one=True
    )

    return jsonify(
        success=True,
        stats={
            "users": int(users["count"] or 0),
            "businesses": int(businesses["count"] or 0),
            "pending_businesses": int(
                pending["count"] or 0
            ),
            "reviews": int(reviews["count"] or 0),
            "messages": int(messages["count"] or 0)
        }
    )


# =========================================================
# USERS
# =========================================================

@bp.get("/users")
@role_required("admin")
def all_users():

    rows = fetch(
        """
        SELECT
            id,
            name,
            email,
            phone,
            role,
            created_at
        FROM users
        ORDER BY id DESC
        """
    )

    return jsonify(
        success=True,
        users=json_safe(rows)
    )


# =========================================================
# DELETE USER
# =========================================================

@bp.delete("/users/<int:user_id>")
@role_required("admin")
def delete_user(user_id):

    user = fetch(
        """
        SELECT
            id,
            role
        FROM users
        WHERE id=%s
        """,
        (user_id,),
        True
    )

    if not user:

        return jsonify(
            success=False,
            message="User not found."
        ), 404

    if user["role"] == "admin":

        return jsonify(
            success=False,
            message="Admin accounts cannot be deleted from this panel."
        ), 403

    execute(
        """
        DELETE FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    return jsonify(
        success=True,
        message="User deleted successfully."
    )


# =========================================================
# ALL BUSINESSES
# =========================================================

@bp.get("/businesses")
@role_required("admin")
def all_businesses():

    rows = fetch(
        """
        SELECT
            b.id,
            b.owner_id,
            b.category_id,

            b.business_name,
            b.description,
            b.address,
            b.location,
            b.phone,
            b.email,

            b.opening_time,
            b.closing_time,

            b.services,
            b.status,
            b.created_at,

            u.name AS owner_name,

            c.name AS category,

            COALESCE(
                (
                    SELECT AVG(r.rating)
                    FROM reviews r
                    WHERE r.business_id = b.id
                ),
                0
            ) AS avg_rating,

            (
                SELECT COUNT(*)
                FROM reviews r2
                WHERE r2.business_id = b.id
            ) AS review_count

        FROM businesses b

        LEFT JOIN users u
            ON u.id = b.owner_id

        LEFT JOIN categories c
            ON c.id = b.category_id

        ORDER BY b.created_at DESC
        """
    )

    # ================================================
    # IMPORTANT
    # timedelta / datetime / decimal -> JSON safe
    # ================================================

    safe_rows = json_safe(rows)

    return jsonify(
        success=True,
        businesses=safe_rows
    )


# =========================================================
# APPROVE / REJECT BUSINESS
# =========================================================

@bp.patch(
    "/businesses/<int:business_id>/status"
)
@role_required("admin")
def update_business_status(
    business_id
):

    data = request.get_json(
        silent=True
    ) or {}

    status = (
        data.get("status") or ""
    ).strip().lower()

    if status not in (
        "pending",
        "approved",
        "rejected"
    ):

        return jsonify(
            success=False,
            message="Invalid status."
        ), 400

    business = fetch(
        """
        SELECT id
        FROM businesses
        WHERE id=%s
        """,
        (business_id,),
        True
    )

    if not business:

        return jsonify(
            success=False,
            message="Business not found."
        ), 404

    execute(
        """
        UPDATE businesses
        SET status=%s
        WHERE id=%s
        """,
        (
            status,
            business_id
        )
    )

    return jsonify(
        success=True,
        message=(
            "Business "
            + status
            + " successfully."
        )
    )


# =========================================================
# ALL REVIEWS
# =========================================================

@bp.get("/reviews")
@role_required("admin")
def all_reviews():

    rows = fetch(
        """
        SELECT
            r.id,
            r.business_id,
            r.user_id,
            r.rating,
            r.review_text,
            r.created_at,

            u.name AS user_name,

            b.business_name

        FROM reviews r

        LEFT JOIN users u
            ON u.id = r.user_id

        LEFT JOIN businesses b
            ON b.id = r.business_id

        ORDER BY r.created_at DESC
        """
    )

    return jsonify(
        success=True,
        reviews=json_safe(rows)
    )


# =========================================================
# DELETE REVIEW
# =========================================================

@bp.delete(
    "/reviews/<int:review_id>"
)
@role_required("admin")
def delete_review(review_id):

    review = fetch(
        """
        SELECT id
        FROM reviews
        WHERE id=%s
        """,
        (review_id,),
        True
    )

    if not review:

        return jsonify(
            success=False,
            message="Review not found."
        ), 404

    execute(
        """
        DELETE FROM reviews
        WHERE id=%s
        """,
        (review_id,)
    )

    return jsonify(
        success=True,
        message="Review deleted successfully."
    )


# =========================================================
# ALL MESSAGES
# =========================================================

@bp.get("/messages")
@role_required("admin")
def all_messages():

    rows = fetch(
        """
        SELECT
            m.id,
            m.sender_id,
            m.business_id,
            m.name,
            m.email,
            m.subject,
            m.message,
            m.status,
            m.created_at,

            b.business_name

        FROM messages m

        LEFT JOIN businesses b
            ON b.id = m.business_id

        ORDER BY m.created_at DESC
        """
    )

    return jsonify(
        success=True,
        messages=json_safe(rows)
    )