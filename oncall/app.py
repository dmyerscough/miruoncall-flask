
from oncall import celery as ext_celery
from oncall import create_app

app = create_app()
celery = ext_celery.celery


@app.route("/")
def hello():
    return "Hello, World!"
