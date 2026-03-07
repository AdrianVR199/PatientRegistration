from flask import Flask
from .database import db
from .routes import patients_bp, vapi_bp, appointments_bp
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config:
        # Testing: use in-memory DB, skip seed
        app.config.update(test_config)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///patients.db"

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)

    app.register_blueprint(patients_bp)
    app.register_blueprint(vapi_bp)
    app.register_blueprint(appointments_bp)

    with app.app_context():
        db.create_all()
        if not test_config:
            from .seed import seed_data
            seed_data()

    return app