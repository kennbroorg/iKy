import os

from api import home
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from .configuration import get_config
from .extensions import socketio


def create_application() -> tuple[Flask, SocketIO]:
    config = get_config()
    app = Flask(__name__)
    cors_origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:4200,http://localhost:5173",
    ).split(",")
    CORS(app, origins=cors_origins)
    app.config.from_object(config)
    app.register_blueprint(home)
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
    )
    return app, socketio
