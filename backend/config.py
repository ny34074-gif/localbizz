import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "localbiz-secret-change-me"
    )

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_USER = os.getenv(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD",
        ""
    )

    MYSQL_DB = os.getenv(
        "MYSQL_DB",
        "local_business_directory"
    )

    MYSQL_PORT = int(
        os.getenv(
            "MYSQL_PORT",
            "3306"
        )
    )

    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(__file__),
        "uploads"
    )

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # Email / OTP
    SMTP_HOST = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    SMTP_PORT = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    SMTP_EMAIL = os.getenv(
        "SMTP_EMAIL",
        ""
    )

    SMTP_PASSWORD = os.getenv(
        "SMTP_PASSWORD",
        ""
    )

    OTP_EXPIRY_MINUTES = int(
        os.getenv(
            "OTP_EXPIRY_MINUTES",
            "10"
        )
    )