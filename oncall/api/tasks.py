# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime, timedelta

from oncall import db
from oncall.api.models import Incidents, Teams
from oncall.app import app, celery
from oncall.utils.pagerduty import PagerDuty, RequestFailure

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def populate_incidents(self):
    """
    Trigger a celery job for each team to populate alerts
    """
    until = datetime.now()

    for team in Teams.query.all():
        # TODO(damian): Update the last checked time
        _populate_incident.delay(team_id=team.id, since=team.last_checked, until=until)

    return True


@celery.task(bind=True, autoretry_for=(Exception,), exponential_backoff=2, retry_kwargs={'max_retries': 3}, retry_jitter=False)
def _populate_incident(self, team_id: str, since: datetime, until: datetime):
    """
    Populate team alerts

    :param team: PagerDuty Team ID
    :param since:
    :param until:

    :return: (bool) successful
    """
    pyduty = PagerDuty(os.getenv('PAGERDUTY_KEY'))

    team = Teams.query.filter_by(id=team_id).one_or_none()

    if team is None:
        return

    try:
        for incidents in pyduty.get_incidents(team_id=team.team_id, since=since, until=until):
            for incident in incidents:
                # Create a unique identifier since incident ID can be duplicated across teams
                incident_id = f"{incident['id']}_{team.team_id}"

                if Incidents.query.filter_by(incident_id=incident_id).one_or_none() is None:
                    new_incident = Incidents(
                        title=incident.get('title', 'No title'),
                        description=incident.get('description', 'No description'),
                        summary=incident.get('summary', 'No summary'),
                        status=incident.get('status', 'No status'),
                        actionable=None,
                        created_at=datetime.fromisoformat(incident['created_at']),
                        incident_id=incident_id,
                        annotation=None,
                        urgency=incident['urgency'],
                        team=team.id,
                    )

                    db.session.add(new_incident)
                    db.session.commit()

                    logger.info(f"{incident_id} has been created")
    except RequestFailure as err:
        logger.error(f'Failed to query PagerDuty: {err}')

        return False

    # Update the last checked time
    db.session.query(Teams).filter_by(id=team_id).update({'last_checked': until})
    db.session.commit()

    return True


@celery.task(bind=True, autoretry_for=(Exception,), exponential_backoff=2, retry_kwargs={'max_retries': 3}, retry_jitter=False)
def populate_teams(self):
    """
    Populate team details
    """
    pyduty = PagerDuty(os.getenv('PAGERDUTY_KEY'))

    try:
        for teams in pyduty.get_teams():
            for team in teams:
                if Teams.query.filter_by(team_id=team['id']).one_or_none() is None:
                    new_team = Teams(
                        name=team['name'],
                        team_id=team['id'],
                        summary=team['summary'],
                        last_checked=datetime.now(),
                    )

                    if app.config.get('INITIAL_INCIDENT_LOOKBACK') is not None:
                        # When the team bootstrap occurs query the past X days for incidents
                        new_team.last_checked = new_team.last_checked - timedelta(days=int(app.config['INITIAL_INCIDENT_LOOKBACK']))

                    db.session.add(new_team)
                    db.session.commit()

                    logger.info(f'{team["name"]} has been created')
    except RequestFailure as err:
        logger.error(f'Failed to query PagerDuty: {err}')

        return False

    return True


@celery.task(bind=True)
def update_incidents(self):
    """
    Check the status on unresolved tickets
    """
    for incident in Incidents.query.filter(Incidents.status != 'resolved').all():
        _update_incident.delay(incident_id=incident.id)

    return True


@celery.task(bind=True, autoretry_for=(Exception,), exponential_backoff=2, retry_kwargs={'max_retries': 3}, retry_jitter=False)
def _update_incident(self, incident_id):
    """
    Check the status of a ticket and update the status
    """
    pyduty = PagerDuty(os.getenv('PAGERDUTY_KEY'))

    incident = Incidents.query.filter_by(id=incident_id).one_or_none()

    if incident is None:
        logger.error(f'Failed to find incident {incident_id}')
        return False

    resp = pyduty.get_incident(incident_id=incident.incident_id)

    if resp['status'] != incident.status:
        logger.info(f'Updated incident {incident.incident_id} with the new status of {resp["status"]}')

        incident.status = resp['status']

        db.session.commit()

    return True
