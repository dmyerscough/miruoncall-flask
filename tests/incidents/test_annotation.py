from oncall.api.models import Teams, Incidents

from http import HTTPStatus
from datetime import datetime


def create_team_and_incident(db):
    """
    Create a team and incident for testing
    """
    team = Teams(
        name='test-team', team_id='ABC123', summary='', last_checked=datetime.now()
    )

    incident = Incidents(
        incident_id='123',
        team=team.id,
        title='Server on Fire',
        summary='Servers on Fire',
        description='Servers on Fire',
        actionable=True,
        status='resolved',
        created_at=datetime.now(),
        urgency='high',
        annotation=None,
    )

    db.session.add(team)
    db.session.add(incident)
    db.session.commit()


def test_annotation_incident(app, db):
    """
    Test that an annotation can be added to an incident
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()

    resp = client.post('/api/v1/incident/123/annotation', json={'annotation': 'test'})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['annotation']['summary'] == 'test'


def test_annotation_none_existant_incident(app, db):
    """
    Test that an annotation cannot be added to an incident that does not exist
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()

    resp = client.post('/api/v1/incident/2/annotation', json={'annotation': 'test'})

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json['error'] == 'incident does not exist'


def test_annotation_incident_no_json(app, db):
    """
    Test that an annotation cannot be added to an incident without json
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()

    resp = client.post('/api/v1/incident/123/annotation')

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json == {'error': 'requests must of type application/json'}


def test_update_annotation(app, db):
    """
    Test that an annotation can be updated
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()

    resp = client.post('/api/v1/incident/123/annotation', json={'annotation': 'test'})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['annotation']['summary'] == 'test'

    resp = client.put('/api/v1/incident/123/annotation', json={'annotation': 'test 2'})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['annotation']['summary'] == 'test 2'


def test_deleting_annotation(app, db):
    """
    Test that an annotation can be deleted
    """
    assert create_team_and_incident(db) is None

    client = app.test_client()

    resp = client.post('/api/v1/incident/123/annotation', json={'annotation': 'test'})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['annotation']['summary'] == 'test'

    resp = client.delete('/api/v1/incident/123/annotation')

    assert resp.status_code == HTTPStatus.OK
    assert resp.json == {'annotation': None}

    incident = Incidents.query.filter_by(id=1).one_or_none()

    assert incident.annotation_id is None
