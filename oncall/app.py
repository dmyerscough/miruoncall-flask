from oncall import celery as ext_celery
from oncall import create_app
from oncall.api.routes import api

app = create_app()
celery = ext_celery.celery

app.register_blueprint(api)
