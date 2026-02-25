from api import home
from flask import Flask
from flask_cors import CORS

from .configuration import get_config


def create_application():
    config = get_config()
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)
    app.register_blueprint(home)
    return app
