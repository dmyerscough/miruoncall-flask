import os

from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from oncall.config import config
from oncall.utils.celery import make_celery

db = SQLAlchemy()
migrate = Migrate()
celery = FlaskCeleryExt(create_celery_app=make_celery)


def create_app(config_name=None):
    """
    Create a Flask application using the app factory pattern.
    """
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    CORS(app, resources={r'/api/*': {'origins': config[config_name].CORS_ORIGINS}})

    app.config.from_object(config[config_name])

    # app.register_blueprint(api)

    db.init_app(app)
    migrate.init_app(app, db)
    celery.init_app(app)

    @app.shell_context_processor
    def ctx():
        return {'app': app, 'db': db}

    return app
