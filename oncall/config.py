import os
from pathlib import Path

from celery.schedules import crontab


class BaseConfig:
    """
    Base configuration
    """

    BASE_DIR = Path(__file__).resolve().parent.parent

    TESTING = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', f'sqlite:///{BASE_DIR}/oncall.db')

    INITIAL_INCIDENT_LOOKBACK = os.getenv('INITIAL_INCIDENT_LOOKBACK', 90)

    # Celery configuration
    BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')

    CELERY_ACCEPT_CONTENT = ['application/json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'

    # Celery beat schedule
    CELERYBEAT_SCHEDULE = {
        'populate_teams': {
            'task': 'oncall.api.tasks.populate_teams',
            # Every 30 minutes
            'schedule': crontab(minute='*/30'),
        },
        'populate_incidents': {
            'task': 'oncall.api.tasks.populate_incidents',
            # Every 5 minutes
            'schedule': crontab(minute='*/5'),
        },
        'update_incidents': {
            'task': 'oncall.api.tasks.update_incidents',
            # Every 5 minutes
            'schedule': crontab(minute='*/10'),
        },
    }

    CORS_ORIGINS = []


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'


class DevelopmentConfig(BaseConfig):
    """
    Development configuration
    """

    DEBUG = True

    CORS_ORIGINS = ['*']


class ProductionConfig(BaseConfig):
    """
    Production configuration
    """

    DEBUG = False

    CORS_ORIGINS = []


config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
