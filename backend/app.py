import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from extensions import bcrypt


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )


    # =========================
    # BCRYPT
    # =========================

    bcrypt.init_app(app)


    # =========================
    # CORS
    # =========================

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://127.0.0.1:5500",
                    "http://localhost:5500"
                ]
            }
        },
        supports_credentials=True
    )


    # =========================
    # ROUTES
    # =========================

    from routes.auth import bp as auth_bp
    from routes.business import bp as business_bp
    from routes.reviews import bp as reviews_bp
    from routes.contact import bp as contact_bp
    from routes.admin import bp as admin_bp


    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        business_bp,
        url_prefix="/api/businesses"
    )

    app.register_blueprint(
        reviews_bp,
        url_prefix="/api/reviews"
    )

    app.register_blueprint(
        contact_bp,
        url_prefix="/api/contact"
    )

    app.register_blueprint(
        admin_bp,
        url_prefix="/api/admin"
    )


    # =========================
    # HEALTH CHECK
    # =========================

    @app.get("/api/health")
    def health():

        return jsonify({
            "success": True,
            "message": "LocalBiz backend is running"
        })


    # =========================
    # UPLOADS
    # =========================

    @app.get("/uploads/<path:filename>")
    def uploads(filename):

        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )


    # =========================
    # FILE TOO LARGE
    # =========================

    @app.errorhandler(413)
    def too_large(error):

        return jsonify({
            "success": False,
            "message": "Maximum upload size is 10 MB."
        }), 413


    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )