from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
import logging

db = SQLAlchemy()


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes

    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO, style='{', datefmt='%Y-%m-%d %H:%M:%S', format='{levelname}:{name}:{asctime} {message}')
    app.config.from_object(config_by_name[env or "test"])    
    api = Api(app, title="UdaConnect API", version="0.1.0")

    CORS(app)  # Set CORS for development

    register_routes(api, app)
    db.init_app(app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app
