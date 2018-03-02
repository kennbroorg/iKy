# -*- encoding: utf-8 -*-
from flask import Flask
from .configuration import get_config
from api import home


def create_application():
    config = get_config()
    app = Flask(__name__)
    app.config.from_object(config)
    app.register_blueprint(home)
    return app
