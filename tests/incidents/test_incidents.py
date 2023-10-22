
from oncall.api.models import Teams

from http import HTTPStatus

from datetime import datetime


def test_query_incidents(app, db):
    """
    Test the query incidents endpoint
    """
    client = app.test_client()

    team = Teams(name='test-team', team_id='ABC123', summary='awesome team', last_checked=datetime.now())

    db.session.add(team)
    db.session.commit()

    resp = client.post(f'/api/v1/incidents/{team.id}', content_type='application/json', json={'since': '2023-01-01', 'until': '2023-01-07'})

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
        },
        # 2023-10-22 08:06:01
        'team': {
            'alias': None,
            'created_at': team.created_at.isoformat(),
            'id': team.id,
            'last_checked': team.last_checked.isoformat(),
            'name': team.name,
            'summary': team.summary,
            'team_id': team.team_id
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
    assert resp.json == {'error': 'team does not exist'}


def test_query_incidents_invalid_since_until(app, db):
    """
    Test query incidents endpoint with invalid since and until
    """
    client = app.test_client()

    team = Teams(name='test-team', team_id='ABC123', summary='', last_checked=datetime.now())

    db.session.add(team)
    db.session.commit()

    resp = client.post(f'/api/v1/incidents/{team.id}', content_type='application/json', json={'since': '01-01-2023', 'until': '07-01-2023'})

    assert resp.status_code == 400
    assert resp.json == {'error': 'since and until require the format of YYYY-MM-DD'}

    resp = client.post(f'/api/v1/incidents/{team.id}', content_type='application/json', json={'since': '2023-28-01', 'until': '2023-30-01'})

    assert resp.status_code == 400
    assert resp.json == {'error': 'since and until require the format of YYYY-MM-DD'}


def test_query_incidents_since_greater_than_until(app, db):
    """
    Test query incidents endpoint with since greater than until
    """
    client = app.test_client()

    team = Teams(name='test-team', team_id='ABC123', summary='', last_checked=datetime.now())

    db.session.add(team)
    db.session.commit()

    resp = client.post(f'/api/v1/incidents/{team.id}', content_type='application/json', json={'since': '2023-01-07', 'until': '2023-01-01'})

    assert resp.status_code == 400
    assert resp.json == {'error': 'since cannot be greater than until'}
