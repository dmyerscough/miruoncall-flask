
from oncall.api.models import Teams

from http import HTTPStatus

from datetime import datetime


def test_querying_teams(app, db):
    """
    Test querying teams endpoint
    """
    client = app.test_client()

    db.session.add(
        Teams(name='test-team', team_id='ABC123', summary='', last_checked=datetime.now())
    )
    db.session.commit()

    resp = client.get('/api/v1/teams')

    assert resp.status_code == HTTPStatus.OK
    assert resp.json == {'teams': [{'alias': None, 'id': 1, 'name': 'test-team'}]}


def test_querying_teams_none_exist(app, db):
    """
    Test querying teams endpoint with no teams
    """
    client = app.test_client()

    resp = client.get('/api/v1/teams')

    assert resp.status_code == HTTPStatus.OK
    assert resp.json == {'teams': []}