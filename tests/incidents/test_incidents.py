
from oncall.api.models import Teams

from http import HTTPStatus

from datetime import datetime


def test_query_incidents(app, db):
    """
    Test the query incidents endpoint
    """
    client = app.test_client()

    db.session.add(
        Teams(name='test-team', team_id='ABC123', summary='', last_checked=datetime.now())
    )
    db.session.commit()

    resp = client.post('/api/v1/incidents/ABC123', content_type='application/json', json={'since': '2023-01-01', 'until': '2023-01-07'})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json == {
        'incidents': [],
        'summary': {
            '2023-01-01': {'high': 0, 'low': 0},
            '2023-01-02': {'high': 0, 'low': 0},
            '2023-01-03': {'high': 0, 'low': 0},
            '2023-01-04': {'high': 0, 'low': 0},
            '2023-01-05': {'high': 0, 'low': 0},
            '2023-01-06': {'high': 0, 'low': 0},
            '2023-01-07': {'high': 0, 'low': 0}
        }
    }


def test_query_incidents_incorrect_content_type(app, db):
    """
    Test query incidents endpoint with incorrect content type
    """
    client = app.test_client()

    resp = client.post('/api/v1/incidents/123')

    assert resp.status_code == 400
    assert resp.json == {'error': 'requests must of type application/json'}


def test_query_incidents_none_existant_team(app, db):
    """
    Test query incidents endpoint with a none existant team
    """
    client = app.test_client()

    resp = client.post('/api/v1/incidents/123', content_type='application/json')

    assert resp.status_code == 404
