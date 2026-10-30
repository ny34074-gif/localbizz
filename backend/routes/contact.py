from flask import Blueprint, request, jsonify, session
from db import execute, fetch

bp = Blueprint("contact", __name__)

@bp.post("")
def send_message():
    d = request.get_json(silent=True) or {}
    for k in ("name","email","subject","message"):
        if not (d.get(k) or "").strip():
            return jsonify(success=False, message=f"{k} is required"), 400
    mid = execute("""
        INSERT INTO messages(sender_id,business_id,name,email,subject,message,status)
        VALUES(%s,%s,%s,%s,%s,%s,'unread')
    """, (
        session.get("user_id"), d.get("business_id") or None,
        d["name"].strip(), d["email"].strip(),
        d["subject"].strip(), d["message"].strip()
    ))
    return jsonify(success=True, message="Message sent successfully.", message_id=mid), 201

@bp.get("/owner")
def owner_messages():
    if "user_id" not in session:
        return jsonify(success=False, message="Login required."), 401
    return jsonify(success=True, messages=fetch("""
        SELECT m.*,b.business_name
        FROM messages m
        LEFT JOIN businesses b ON b.id=m.business_id
        WHERE b.owner_id=%s
        ORDER BY m.created_at DESC
    """, (session["user_id"],)))

@bp.get("/business/<int:bid>")
def business_messages(bid):
    if "user_id" not in session:
        return jsonify(success=False, message="Login required."), 401
    owner = fetch("SELECT owner_id FROM businesses WHERE id=%s", (bid,), True)
    if not owner or owner["owner_id"] != session["user_id"]:
        return jsonify(success=False, message="Permission denied."), 403
    return jsonify(success=True, messages=fetch(
        "SELECT * FROM messages WHERE business_id=%s ORDER BY created_at DESC", (bid,)
    ))
