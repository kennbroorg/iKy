import os

from api import home
from flask import Flask
from flask_cors import CORS

from .configuration import get_config


def create_application():
    config = get_config()
    app = Flask(__name__)
    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",")
    CORS(app, origins=cors_origins)
    app.config.from_object(config)
    app.register_blueprint(home)
    return app
