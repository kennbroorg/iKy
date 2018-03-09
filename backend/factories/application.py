# -*- encoding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from .configuration import get_config
from api import home


def create_application():
    config = get_config()
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)
    app.register_blueprint(home)
    return app
