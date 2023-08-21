# -*- coding: utf-8 -*-

import uuid
import pytest

from datetime import datetime
from mock import MagicMock, patch

from oncall.incidents.models import Incidents, Teams
from oncall.incidents.tasks import (_populate_incident, _update_incident, populate_incidents, populate_teams, update_incidents)


@patch('oncall.incidents.tasks._populate_incident')
@patch('oncall.incidents.tasks.datetime')
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

@patch('oncall.incidents.tasks.PagerDuty')
@patch('oncall.incidents.tasks.datetime')
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

#     @skip('Needs implemented')
#     def test_populate_alerts_request_failure(self):
#         pass

#     @patch('oncall.tasks.PagerDuty')
#     def test_populate_teams(self, mock_teams):
#         """
#         Test populating teams
#         """
#         mock_team = MagicMock()
#         mock_team.get_teams.return_value = [
#             [
#                 {
#                     "id": "PQ9K7I8",
#                     "type": "team",
#                     "summary": "Engineering",
#                     "self": "https://api.pagerduty.com/teams/PQ9K7I8",
#                     "html_url": "https://subdomain.pagerduty.com/teams/PQ9K7I8",
#                     "name": "Engineering",
#                     "description": "All engineering"
#                 }
#             ]
#         ]

#         mock_teams.return_value = mock_team

#         self.assertTrue(populate_teams())

#     @skip('Needs implemented')
#     def test_populate_teams_request_failure(self):
#         pass

#     @patch('oncall.tasks.PagerDuty')
#     def test_update_incident_helper_status_mismatch(self, mock_incident):
#         """
#         Test incident helper when the status does not match the status stored in the database
#         """
#         mock_incident_ = MagicMock()
#         mock_incident_.get_incident.return_value = {
#             'id': 'PT4KHLK',
#             'type': 'incident',
#             'summary': '[#1234] The server is on fire.',
#             'self': 'https://api.pagerduty.com/incidents/PT4KHLK',
#             'html_url': 'https://subdomain.pagerduty.com/incidents/PT4KHLK',
#             'incident_number': 1234,
#             'created_at': '2015-10-06T21:30:42Z',
#             'status': 'resolved',
#             'title': 'The server is on fire.',
#             'urgency': 'high'
#         }

#         mock_incident.return_value = mock_incident_

#         Incidents.objects.create(
#             id='96e3d488-52b8-4b86-906e-8bc5b3b7504b',
#             title='Down Replica DB',
#             description='Down Replica DB',
#             summary='Down Replica DB',
#             status='triggered',
#             created_at=timezone.now(),
#             incident_id='PT4KHLK',
#             urgency='high',
#             team=Team.objects.create(
#                 name='PANW SRE',
#                 team_id='PANW',
#                 summary='The Oncall Team for XYZ',
#             )
#         )

#         self.assertTrue(_update_incident('96e3d488-52b8-4b86-906e-8bc5b3b7504b'))
#         self.assertEqual(Incidents.objects.get(id='96e3d488-52b8-4b86-906e-8bc5b3b7504b').status, 'resolved')

#         mock_incident_.get_incident.assert_called_once_with(incident_id='PT4KHLK')

#     @patch('oncall.tasks._update_incident')
#     def test_update_incident(self, mock_update_incident):
#         """
#         Test updaing an incident that is not marked as resolved
#         """
#         current_time = timezone.now()

#         with patch.object(timezone, 'now', return_value=current_time):
#             Incidents.objects.create(
#                 id='96e3d488-52b8-4b86-906e-8bc5b3b7504b',
#                 title='Down Replica DB',
#                 description='Down Replica DB',
#                 summary='Down Replica DB',
#                 status='triggered',
#                 created_at=timezone.now(),
#                 incident_id='PT4KHLK',
#                 urgency='high',
#                 team=Team.objects.create(
#                     name='PANW SRE',
#                     team_id='PANW',
#                     summary='The Oncall Team for XYZ',
#                 )
#             )

#             self.assertTrue(update_incidents())

#         mock_update_incident.delay.assert_called_once_with(
#             incident_id=uuid.UUID('96e3d488-52b8-4b86-906e-8bc5b3b7504b'),
#         )