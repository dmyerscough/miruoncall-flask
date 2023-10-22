from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from oncall import db
from oncall.api.models import Annotations, Incidents, Teams

api = Blueprint('api', __name__, url_prefix='/api/v1')


@api.route('/teams')
def get_teams():
    """
    Get all teams
    """
    teams = Teams.query.all()

    return jsonify({'teams': [{"id": team.id, "name": team.name, "alias": team.alias} for team in teams]})


@api.route('/incidents/<string:team_id>', methods=['POST'])
def get_incidents(team_id):
    """
    Get incidents for a specific team
    """
    if not request.is_json:
        return jsonify({"error": "requests must of type application/json"}), HTTPStatus.BAD_REQUEST

    # Check the team exists
    team = Teams.query.filter_by(id=team_id).one_or_none()

    if team is None:
        return jsonify({"error": "team does not exist"}), HTTPStatus.NOT_FOUND

    try:
        data = request.get_json()
    except BadRequest:
        return jsonify({"error": "invalid json receieved"}), HTTPStatus.BAD_REQUEST

    since = data.get('since')
    until = data.get('until')

    if since is None or until is None:
        return jsonify({"error": "since and until are required arguments"}), HTTPStatus.BAD_REQUEST

    try:
        since = datetime.fromisoformat(since).strftime('%Y-%m-%d')
        until = datetime.fromisoformat(until).strftime('%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'since and until require the format of YYYY-MM-DD'}), HTTPStatus.BAD_REQUEST

    if datetime.fromisoformat(since) > datetime.fromisoformat(until):
        return jsonify({'error': 'since cannot be greater than until'}), HTTPStatus.BAD_REQUEST

    incidents = {'incidents': [], 'summary': {}, 'team': team.to_dict()}

    incidents['summary'] = {
        (datetime.fromisoformat(since) + timedelta(days=x)).strftime('%Y-%m-%d'): {'low': 0, 'high': 0} for x in range((datetime.fromisoformat(until) - datetime.fromisoformat(since)).days + 1)
    }

    for incident in Incidents.query.filter_by(team=team_id).filter(Incidents.created_at.between(since, until)).order_by('created_at'):
        incidents['summary'][incident.created_at.strftime('%Y-%m-%d')][incident.urgency.lower()] += 1

        incidents['incidents'].append(incident.to_dict())

    return jsonify(incidents)


@api.route('/incident/<string:incident_id>/annotation', methods=['POST', 'PUT', 'DELETE'])
def annotation(incident_id: str):
    """
    Annotation for an incident
    """
    if not request.is_json and request.method != 'DELETE':
        return jsonify({"error": "requests must of type application/json"}), HTTPStatus.BAD_REQUEST

    # Check the team exists
    incident = Incidents.query.filter_by(incident_id=incident_id).one_or_none()

    if incident is None:
        return jsonify({"error": "incident does not exist"}), HTTPStatus.BAD_REQUEST

    if request.method != 'DELETE':
        data = request.get_json()
        description = data.get('annotation')

    if incident and incident.annotation_id is not None:
        annotation = Annotations.query.filter_by(id=incident.annotation_id).one_or_none()

        if request.method == 'PUT':
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
        return jsonify({"error": "incident does not exist"}), HTTPStatus.BAD_REQUEST

    if not request.is_json:
        return jsonify({"error": "requests must of type application/json"}), HTTPStatus.BAD_REQUEST

    data = request.get_json()
    actionable = data.get('actionable')

    if actionable is None:
        return jsonify({"error": "actionable is a required argument"}), HTTPStatus.BAD_REQUEST

    if actionable.lower() not in ['true', 'false']:
        return jsonify({"error": "actionable must be either true or false"}), HTTPStatus.BAD_REQUEST

    db.session.query(Incidents).filter_by(incident_id=incident_id).update({'actionable': actionable.lower() == 'true'})
    db.session.commit()

    return jsonify({'actionable': actionable.lower() == 'true'}), HTTPStatus.OK