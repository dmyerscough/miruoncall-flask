
from oncall.api.models import Teams, Incidents

from http import HTTPStatus
from datetime import datetime


def create_team_and_incident(db):
    """
    Create a team and incident for testing
    """
    team = Teams(name='test-team', team_id='ABC123', summary='', last_checked=datetime.now())

    incident = Incidents(
        incident_id='123',
        team=team.id,
        title='Server on Fire',
        summary='Servers on Fire',
        description='Servers on Fire',
        actionable=None,
        status='resolved',
        created_at=datetime.now(),
        urgency='high',
        annotation=None
    )

    db.session.add(team)
    db.session.add(incident)
    db.session.commit()


def test_actionable_incident(app, db):
    """
    Test that an incident can be marked as actionable
    """
    assert create_team_and_incident(db) is None

    incident = Incidents.query.filter_by(incident_id='123').one_or_none()

    client = app.test_client()
    resp = client.post('/api/v1/incident/123/actionable', json={'actionable': 'true'})

    assert incident.actionable is True


def test_actionable_incident_no_json(app, db):
    """
    Test that an incident cannot be marked as actionable if the request is not json
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()
    resp = client.post('/api/v1/incident/123/actionable')

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json['error'] == 'requests must of type application/json'


def test_actionable_incident_no_incident(app, db):
    """
    Test that an incident cannot be marked as actionable if it does not exist
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()
    resp = client.post('/api/v1/incident/2/actionable', json={'actionable': 'true'})

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json['error'] == 'incident does not exist'


def test_actionable_incident_no_actionable(app, db):
    """
    Test that an incident cannot be marked as actionable if the request does not contain a value
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()
    resp = client.post('/api/v1/incident/123/actionable', json={'actionable': ''})

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json['error'] == 'actionable must be either true or false'


def test_actionable_incident_invalid_actionable(app, db):
    """
    Test that an incident cannot be marked as actionable if the request contains an invalid value
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()
    resp = client.post('/api/v1/incident/123/actionable', json={'actionable': 'test'})

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json['error'] == 'actionable must be either true or false'
