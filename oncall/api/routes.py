from datetime import datetime, timedelta
from http import HTTPStatus
import pytz

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from oncall import db
from oncall.api.models import Annotations, Incidents, Teams

from sqlalchemy import func, and_


api = Blueprint('api', __name__, url_prefix='/api/v1')


@api.route('/teams')
def get_teams():
    """
    Get all teams
    """
    teams = Teams.query.all()

    return jsonify({'teams': [{'id': team.id, 'name': team.name, 'alias': team.alias} for team in teams]})


@api.route('/mostincidents', methods=['GET'])
def mostincidents():
    """
    Get all teams with poor PagerDuty integration
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    incident_count = func.count(Incidents.id).label('incident_count')

    query = (
        db.session.query(
            Teams.id.label('team_id'), Teams.name.label('team_name'), Teams.alias.label('alias'), incident_count
        )
        .outerjoin(Incidents, and_(Teams.id == Incidents.team, Incidents.created_at >= seven_days_ago))
        .group_by(Teams.id)
        .order_by(incident_count.desc())
    )

    teams = query.all()

    return jsonify(
        {
            'teams': [
                {'id': team.team_id, 'name': team.team_name, 'alias': team.alias, 'incident_count': team.incident_count}
                for team in teams
            ]
        }
    ), HTTPStatus.OK


@api.route('/incidents/<string:team_id>', methods=['POST'])
def get_incidents(team_id):
    """
    Get incidents for a specific team
    """
    if not request.is_json:
        return jsonify({'error': 'requests must of type application/json'}), HTTPStatus.BAD_REQUEST

    # Check the team exists
    team = Teams.query.filter_by(id=team_id).one_or_none()

    if team is None:
        return jsonify({'error': 'team does not exist'}), HTTPStatus.NOT_FOUND

    try:
        data = request.get_json()
    except BadRequest:
        return jsonify({'error': 'invalid json receieved'}), HTTPStatus.BAD_REQUEST

    since = data.get('since')
    until = data.get('until')
    timezone = data.get('timezone', 'UTC')  # Default to UTC if not provided

    if since is None or until is None:
        return jsonify({'error': 'since and until are required arguments'}), HTTPStatus.BAD_REQUEST

    try:
        target_timezone = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return jsonify(
            {'error': f'Invalid timezone: {timezone}. Use IANA timezone names like "America/New_York" or "UTC"'}
        ), HTTPStatus.BAD_REQUEST

    try:
        since_date = datetime.fromisoformat(since)
        until_date = datetime.fromisoformat(until)

        # Convert to UTC if timezone-aware, otherwise assume UTC
        if since_date.tzinfo is not None:
            since_date_utc = since_date.astimezone(pytz.UTC)
        else:
            since_date_utc = pytz.UTC.localize(since_date)

        if until_date.tzinfo is not None:
            until_date_utc = until_date.astimezone(pytz.UTC)
        else:
            until_date_utc = pytz.UTC.localize(until_date)

        if since_date.tzinfo is None:
            since_date_target_tz = target_timezone.localize(since_date)
        else:
            since_date_target_tz = since_date.astimezone(target_timezone)

        if until_date.tzinfo is None:
            until_date_target_tz = target_timezone.localize(until_date)
        else:
            until_date_target_tz = until_date.astimezone(target_timezone)

        since_date_target_tz = since_date_target_tz.replace(tzinfo=None)
        until_date_target_tz = until_date_target_tz.replace(tzinfo=None)
    except ValueError:
        return jsonify(
            {'error': 'since and until require ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+TZ)'}
        ), HTTPStatus.BAD_REQUEST

    if since_date_utc > until_date_utc:
        return jsonify({'error': 'since cannot be greater than until'}), HTTPStatus.BAD_REQUEST

    incidents = {'incidents': [], 'summary': {}, 'team': team.to_dict()}

    # Generate summary dates in target timezone - loop over each day in the range
    incidents['summary'] = {
        (since_date_target_tz + timedelta(days=x)).strftime('%Y-%m-%d'): {
            'low': 0,
            'high': 0,
        }
        for x in range((until_date_target_tz - since_date_target_tz).days + 1)
    }

    for incident in (
        Incidents.query.filter_by(team=team_id)
        .filter(Incidents.created_at.between(since_date_utc, until_date_utc))
        .order_by('created_at')
    ):
        incident_date_utc = pytz.UTC.localize(incident.created_at)
        incident_date_target_tz = incident_date_utc.astimezone(target_timezone)

        incident_date_str = incident_date_target_tz.strftime('%Y-%m-%d')

        # Only add to summary if the date exists in our summary dict
        if incident_date_str in incidents['summary']:
            incidents['summary'][incident_date_str][incident.urgency.lower()] += 1

        # Convert incident times to target timezone and add to response
        incident_dict = incident.to_dict()
        if incident.created_at:
            if incident.created_at.tzinfo is not None:
                incident_dict['created_at'] = incident.created_at.astimezone(target_timezone).isoformat()
            else:
                # Assume UTC and convert
                incident_utc = pytz.UTC.localize(incident.created_at)
                incident_dict['created_at'] = incident_utc.astimezone(target_timezone).isoformat()

        incidents['incidents'].append(incident_dict)

    return jsonify(incidents)


@api.route('/incident/<string:incident_id>/annotation', methods=['POST', 'PUT', 'DELETE'])
def annotation(incident_id: str):
    """
    Annotation for an incident
    """
    if not request.is_json and request.method != 'DELETE':
        return jsonify({'error': 'requests must of type application/json'}), HTTPStatus.BAD_REQUEST

    # Check the team exists
    incident = Incidents.query.filter_by(incident_id=incident_id).one_or_none()

    if incident is None:
        return jsonify({'error': 'incident does not exist'}), HTTPStatus.BAD_REQUEST

    if request.method != 'DELETE':
        data = request.get_json()
        description = data.get('annotation')

    if incident and incident.annotation_id is not None:
        annotation = Annotations.query.filter_by(id=incident.annotation_id).one_or_none()

        if request.method in ['PUT', 'POST']:
            db.session.query(Annotations).filter_by(id=incident.annotation_id).update({'summary': description})
            db.session.commit()
        elif request.method == 'DELETE':
            db.session.delete(annotation)
            db.session.commit()

            return jsonify({'annotation': None}), HTTPStatus.OK
    else:
        annotation = Annotations(annotation=description)
        annotation.incidents.append(incident)

        db.session.add(annotation)
        db.session.commit()

    return jsonify({'annotation': annotation.to_dict()}), HTTPStatus.OK


@api.route('/incident/<string:incident_id>/actionable', methods=['POST'])
def actionable_incident(incident_id: str):
    """
    Mark an incident as actionable or not
    """
    # Check the team exists
    incident = Incidents.query.filter_by(incident_id=incident_id).one_or_none()

    if incident is None:
        return jsonify({'error': 'incident does not exist'}), HTTPStatus.BAD_REQUEST

    if not request.is_json:
        return jsonify({'error': 'requests must of type application/json'}), HTTPStatus.BAD_REQUEST

    data = request.get_json()
    actionable = data.get('actionable')

    if actionable is None:
        return jsonify({'error': 'actionable is a required argument'}), HTTPStatus.BAD_REQUEST

    if actionable.lower() not in ['true', 'false']:
        return jsonify({'error': 'actionable must be either true or false'}), HTTPStatus.BAD_REQUEST

    db.session.query(Incidents).filter_by(incident_id=incident_id).update({'actionable': actionable.lower() == 'true'})
    db.session.commit()

    return jsonify({'actionable': actionable.lower() == 'true'}), HTTPStatus.OK
