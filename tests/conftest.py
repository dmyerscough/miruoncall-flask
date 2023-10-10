import pytest

from oncall import create_app, db as _db

from oncall.api.routes import api
from oncall.api.models import Teams, Incidents

from datetime import datetime


@pytest.fixture
def app():
    app = create_app('testing')
    app.register_blueprint(api)
    return app


@pytest.fixture
def db(app):
    """
    https://github.com/pytest-dev/pytest-flask/issues/70
    """
    with app.app_context():
        _db.create_all()
        _db.session.commit()

        yield _db

        _db.session.remove()
        _db.drop_all()
