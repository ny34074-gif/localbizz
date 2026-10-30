import mysql.connector
from flask import current_app


def get_db():
    return mysql.connector.connect(
        host=current_app.config["MYSQL_HOST"],
        user=current_app.config["MYSQL_USER"],
        password=current_app.config["MYSQL_PASSWORD"],
        database=current_app.config["MYSQL_DB"],
        port=int(current_app.config["MYSQL_PORT"]),
        charset="utf8mb4"
    )


def fetch(sql, params=(), one=False):
    conn = get_db()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)

        if one:
            return cursor.fetchone()

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        conn.close()


def execute(sql, params=()):
    conn = get_db()
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()

        return cursor.lastrowid

    finally:
        if cursor:
            cursor.close()
        conn.close()