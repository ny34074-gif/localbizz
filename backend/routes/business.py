import os
import uuid
import json

from datetime import timedelta, datetime, date, time

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    session
)

from werkzeug.utils import secure_filename

from db import fetch, execute
from utils.auth import role_required


bp = Blueprint("business", __name__)


ALLOWED = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif"
}


# =========================================================
# JSON SAFE
# =========================================================

def json_safe(data):

    return json.loads(
        json.dumps(
            data,
            default=str
        )
    )


# =========================================================
# FILE VALIDATION
# =========================================================

def valid(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower() in ALLOWED
    )


# =========================================================
# LIST APPROVED BUSINESSES
# =========================================================

@bp.get("")
def list_businesses():

    q = (
        request.args
        .get("q", "")
        .strip()
    )

    location = (
        request.args
        .get("location", "")
        .strip()
    )

    category = (
        request.args
        .get("category", "")
        .strip()
    )

    try:

        rating = float(
            request.args
            .get("rating", 0)
            or 0
        )

    except ValueError:

        rating = 0


    sql = """

        SELECT

            b.id,

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

            c.name AS category,

            COALESCE(
                AVG(r.rating),
                0
            ) AS avg_rating,

            COUNT(r.id) AS review_count

        FROM businesses b

        LEFT JOIN categories c
            ON c.id = b.category_id

        LEFT JOIN reviews r
            ON r.business_id = b.id

        WHERE b.status = 'approved'

    """


    params = []


    # Search
    if q:

        sql += """

            AND (
                b.business_name LIKE %s
                OR b.description LIKE %s
            )

        """

        params.extend(
            [
                f"%{q}%",
                f"%{q}%"
            ]
        )


    # Location
    if location:

        sql += """

            AND (
                b.location LIKE %s
                OR b.address LIKE %s
            )

        """

        params.extend(
            [
                f"%{location}%",
                f"%{location}%"
            ]
        )


    # Category
    if category:

        sql += """

            AND c.name = %s

        """

        params.append(
            category
        )


    sql += """

        GROUP BY b.id

        HAVING avg_rating >= %s

        ORDER BY avg_rating DESC

    """


    params.append(
        rating
    )


    businesses = fetch(
        sql,
        tuple(params)
    )


    return jsonify(
        success=True,
        businesses=json_safe(
            businesses
        )
    )


# =========================================================
# CATEGORIES
# =========================================================

@bp.get("/categories")
def categories():

    rows = fetch(
        """
        SELECT *
        FROM categories
        ORDER BY name
        """
    )


    return jsonify(
        success=True,
        categories=json_safe(rows)
    )


# =========================================================
# BUSINESS DETAILS
# =========================================================

@bp.get("/<int:bid>")
def details(bid):

    # -----------------------------------------------------
    # First get approved business
    # -----------------------------------------------------

    business = fetch(
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

            c.name AS category,

            COALESCE(
                AVG(r.rating),
                0
            ) AS avg_rating,

            COUNT(r.id) AS review_count

        FROM businesses b

        LEFT JOIN categories c
            ON c.id = b.category_id

        LEFT JOIN reviews r
            ON r.business_id = b.id

        WHERE
            b.id = %s
            AND b.status = 'approved'

        GROUP BY b.id

        """,
        (bid,),
        True
    )


    if not business:

        return jsonify(
            success=False,
            message="Business not found or not approved."
        ), 404


    # -----------------------------------------------------
    # Images
    # -----------------------------------------------------

    images = fetch(
        """
        SELECT
            id,
            business_id,
            image_path
        FROM business_images
        WHERE business_id=%s
        ORDER BY id ASC
        """,
        (bid,)
    )


    # -----------------------------------------------------
    # Reviews
    # -----------------------------------------------------

    reviews = fetch(
        """
        SELECT

            r.id,
            r.rating,
            r.review_text,
            r.created_at,

            u.name AS user_name

        FROM reviews r

        INNER JOIN users u
            ON u.id = r.user_id

        WHERE r.business_id=%s

        ORDER BY r.created_at DESC

        """,
        (bid,)
    )


    business["images"] = json_safe(
        images
    )

    business["reviews"] = json_safe(
        reviews
    )


    # -----------------------------------------------------
    # Final JSON-safe response
    # -----------------------------------------------------

    business = json_safe(
        business
    )


    return jsonify(
        success=True,
        business=business
    )


# =========================================================
# ADD BUSINESS
# =========================================================

@bp.post("")
@role_required(
    "business_owner",
    "admin"
)
def add():

    data = request.form


    business_name = (
        data.get(
            "business_name"
        ) or ""
    ).strip()


    category_id = (
        data.get(
            "category_id"
        ) or ""
    ).strip()


    if not business_name:

        return jsonify(
            success=False,
            message="Business name is required."
        ), 400


    if not category_id:

        return jsonify(
            success=False,
            message="Category is required."
        ), 400


    # -----------------------------------------------------
    # Check category
    # -----------------------------------------------------

    category = fetch(
        """
        SELECT id
        FROM categories
        WHERE id=%s
        """,
        (category_id,),
        True
    )


    if not category:

        return jsonify(
            success=False,
            message="Invalid category."
        ), 400


    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    if session.get("role") == "admin":

        status = "approved"

    else:

        status = "pending"


    # -----------------------------------------------------
    # Insert business
    # -----------------------------------------------------

    bid = execute(
        """

        INSERT INTO businesses

        (
            owner_id,
            category_id,

            business_name,
            description,
            address,
            location,

            phone,
            email,

            opening_time,
            closing_time,

            services,
            status

        )

        VALUES

        (
            %s,
            %s,

            %s,
            %s,
            %s,
            %s,

            %s,
            %s,

            %s,
            %s,

            %s,
            %s
        )

        """,
        (
            session["user_id"],
            category_id,

            business_name,
            data.get(
                "description",
                ""
            ),

            data.get(
                "address",
                ""
            ),

            data.get(
                "location",
                ""
            ),

            data.get(
                "phone",
                ""
            ),

            data.get(
                "email",
                ""
            ),

            data.get(
                "opening_time"
            ) or None,

            data.get(
                "closing_time"
            ) or None,

            data.get(
                "services",
                ""
            ),

            status
        )
    )


    # -----------------------------------------------------
    # Upload images
    # -----------------------------------------------------

    upload_folder = (
        current_app.config[
            "UPLOAD_FOLDER"
        ]
    )


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    for file in request.files.getlist(
        "images"
    ):

        if not file:
            continue


        if not file.filename:
            continue


        if not valid(
            file.filename
        ):
            continue


        filename = (
            uuid.uuid4().hex
            + "_"
            + secure_filename(
                file.filename
            )
        )


        filepath = os.path.join(
            upload_folder,
            filename
        )


        file.save(
            filepath
        )


        execute(
            """
            INSERT INTO business_images
            (
                business_id,
                image_path
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                bid,
                "/uploads/" + filename
            )
        )


    return jsonify(
        success=True,
        message=(
            "Business submitted "
            "for approval."
        ),
        business_id=bid
    ), 201


# =========================================================
# OWNER BUSINESSES
# =========================================================

@bp.get("/owner/my")
@role_required(
    "business_owner",
    "admin"
)
def mine():

    rows = fetch(
        """

        SELECT

            b.id,
            b.business_name,
            b.status,

            b.address,
            b.location,

            c.name AS category,

            COALESCE(
                AVG(r.rating),
                0
            ) AS avg_rating,

            COUNT(r.id) AS review_count

        FROM businesses b

        LEFT JOIN categories c
            ON c.id = b.category_id

        LEFT JOIN reviews r
            ON r.business_id = b.id

        WHERE b.owner_id=%s

        GROUP BY b.id

        ORDER BY b.created_at DESC

        """,
        (
            session["user_id"],
        )
    )


    return jsonify(
        success=True,
        businesses=json_safe(
            rows
        )
    )