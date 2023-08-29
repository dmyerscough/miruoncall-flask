# -*- coding: utf-8 -*-

import uuid
import pytest

from datetime import datetime
from mock import MagicMock, patch

from oncall.api.models import Incidents, Teams
from oncall.api.tasks import (_populate_incident, _update_incident, populate_incidents, populate_teams, update_incidents)


@patch('oncall.api.tasks._populate_incident')
@patch('oncall.api.tasks.datetime')
def test_populate_incidents(mock_datetime, mock_populate_incident, db):
    """
    Test checking teams to populate incidents
    """
    current_time = datetime.now()

    mock_datetime.now.return_value = current_time

    db.session.add(Teams(name='example', team_id='example-id', summary='example SRE', last_checked=current_time))
    db.session.commit()

    assert populate_incidents()

    mock_populate_incident.delay.assert_called_once_with(
        since=current_time,
        team_id=1,
        until=current_time,
    )

@patch('oncall.api.tasks.PagerDuty')
@patch('oncall.api.tasks.datetime')
def test_populate_incident(mock_datetime, mock_pagerduty, db):
    """
    Test populating alerts
    """
    mock_incidents = MagicMock()
    mock_incidents.get_incidents.return_value = [
        [
            {
                'id': 'PT4KHLK',
                'summary': '[#1234] The server is on fire.',
                'incident_number': 1234,
                'created_at': '2015-10-06T21:30:42Z',
                'status': 'resolved',
                'title': 'The server is on fire.',
                'incident_key': 'baf7cf21b1da41b4b0221008339ff357',
                'last_status_change_at': '2015-10-06T21:38:23Z',
                'urgency': 'high'
            }
        ]
    ]

    mock_pagerduty.return_value = mock_incidents

    current_time = datetime.now()
    mock_datetime.now.return_value = current_time
    mock_datetime.fromisoformat.return_value = datetime.fromisoformat('2015-10-06T21:30:42Z')

    db.session.add(Teams(name='example', team_id='example-id', summary='example SRE', last_checked=current_time))
    db.session.commit()

    assert _populate_incident(team_id=1, since=current_time.isoformat(), until=current_time.isoformat())

    incident = Incidents.query.filter_by(incident_id='PT4KHLK').one_or_none()

    assert incident is not None

    assert incident.incident_id == 'PT4KHLK'
    assert incident.title == 'The server is on fire.'
    assert incident.summary == '[#1234] The server is on fire.'
    assert incident.description == 'No description'
    assert incident.status == 'resolved'

@patch('oncall.api.tasks.PagerDuty')
def test_populate_teams(mock_teams, db):
    """
    Test populating teams
    """
    mock_team = MagicMock()
    mock_team.get_teams.return_value = [
        [
            {
                "id": "PQ9K7I8",
                "type": "team",
                "summary": "Engineering",
                "self": "https://api.pagerduty.com/teams/PQ9K7I8",
                "html_url": "https://subdomain.pagerduty.com/teams/PQ9K7I8",
                "name": "Engineering",
                "description": "All engineering"
            }
        ]
    ]

    mock_teams.return_value = mock_team

    assert populate_teams()

@patch('oncall.api.tasks.PagerDuty')
def test_update_incident_helper_status_mismatch(mock_incident, db):
    """
    Test incident helper when the status does not match the status stored in the database
    """
    mock_incident_ = MagicMock()
    mock_incident_.get_incident.return_value = {
        'id': 'PT4KHLK',
        'type': 'incident',
        'summary': '[#1234] The server is on fire.',
        'self': 'https://api.pagerduty.com/incidents/PT4KHLK',
        'html_url': 'https://subdomain.pagerduty.com/incidents/PT4KHLK',
        'incident_number': 1234,
        'created_at': '2015-10-06T21:30:42Z',
        'status': 'resolved',
        'title': 'The server is on fire.',
        'urgency': 'high'
    }

    mock_incident.return_value = mock_incident_

    db.session.add(Teams(name='example', team_id='example-id', summary='example SRE', last_checked=datetime.now()))
    db.session.commit()

    db.session.add(
        Incidents(
            title='Down Replica DB',
            description='Down Replica DB',
            summary='Down Replica DB',
            status='triggered',
            created_at=datetime.now(),
            incident_id='PT4KHLK',
            actionable=None,
            annotation=None,
            urgency='high',
            team=1,
        )
    )
    db.session.commit()

    incident = Incidents.query.filter_by(incident_id='PT4KHLK').one_or_none()

    assert _update_incident(incident_id=incident.id)
    db.session.commit() # commit the changes that were applied in the _update_incident function

    assert Incidents.query.filter_by(id=incident.id).one().status == 'resolved'

    mock_incident_.get_incident.assert_called_once_with(incident_id='PT4KHLK')
