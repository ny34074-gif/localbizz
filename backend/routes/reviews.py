from flask import Blueprint, request, jsonify, session
from db import fetch, execute
from utils.auth import login_required, role_required

bp = Blueprint("reviews", __name__)

@bp.post("/<int:bid>")
@login_required
def add_review(bid):
    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get("rating"))
    except (ValueError, TypeError):
        return jsonify(success=False, message="Rating must be 1 to 5."), 400
    if not 1 <= rating <= 5:
        return jsonify(success=False, message="Rating must be 1 to 5."), 400
    if not fetch("SELECT id FROM businesses WHERE id=%s AND status='approved'", (bid,), True):
        return jsonify(success=False, message="Business not found."), 404
    if fetch("SELECT id FROM reviews WHERE business_id=%s AND user_id=%s", (bid, session["user_id"]), True):
        return jsonify(success=False, message="You already reviewed this business."), 409
    rid = execute(
        "INSERT INTO reviews(business_id,user_id,rating,review_text) VALUES(%s,%s,%s,%s)",
        (bid, session["user_id"], rating, (data.get("review_text") or "").strip())
    )
    return jsonify(success=True, message="Review submitted.", review_id=rid), 201

@bp.get("/business/<int:bid>")
def business_reviews(bid):
    return jsonify(success=True, reviews=fetch("""
        SELECT r.id,r.rating,r.review_text,r.created_at,u.name AS user_name
        FROM reviews r JOIN users u ON u.id=r.user_id
        WHERE r.business_id=%s ORDER BY r.created_at DESC
    """, (bid,)))

@bp.get("/owner")
@role_required("business_owner", "admin")
def owner_reviews():
    return jsonify(success=True, reviews=fetch("""
        SELECT r.id,r.rating,r.review_text,r.created_at,
               b.business_name,u.name AS user_name
        FROM reviews r
        JOIN businesses b ON b.id=r.business_id
        JOIN users u ON u.id=r.user_id
        WHERE b.owner_id=%s ORDER BY r.created_at DESC
    """, (session["user_id"],)))

@bp.delete("/<int:rid>")
@role_required("admin")
def delete_review(rid):
    execute("DELETE FROM reviews WHERE id=%s", (rid,))
    return jsonify(success=True, message="Review deleted.")
