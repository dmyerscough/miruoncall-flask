from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from oncall import db
from oncall.api.models import Incidents, Teams, Annotations

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
        return jsonify({"error": "requests must of type application/json"})

    # Check the team exists
    Teams.query.get_or_404(team_id)

    data = request.get_json()

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

    incidents = {'incidents': [], 'summary': {}}

    incidents['summary'] = {
        (datetime.fromisoformat(since) + timedelta(days=x)).strftime('%Y-%m-%d'): {'low': 0, 'high': 0} for x in range((datetime.fromisoformat(until) - datetime.fromisoformat(since)).days + 1)
    }

    for incident in Incidents.query.filter_by(team=team_id).filter(Incidents.created_at.between(since, until)).order_by('created_at'):
        incidents['summary'][incident.created_at.strftime('%Y-%m-%d')][incident.urgency.lower()] += 1

        incidents['incidents'].append(incident.to_dict())

    return jsonify(incidents)


@api.route('/incident/<string:incident_id>/annotate', methods=['POST', 'PUT', 'DELETE'])
def annotate(incident_id):
    """

    """
    if not request.is_json:
        return jsonify({"error": "requests must of type application/json"})

    # Check the team exists
    incident = Incidents.query.filter_by(id=incident_id).one_or_none()

    # if request.method != 'DELETE':
    data = request.get_json()

    description = data.get('annotation')

    if incident and incident.annotation is not None:
        annotation = Annotations.query.filter_by(id=incident.annotation).one_or_none()

        if request.method == 'PUT':
            db.session.query(Annotations).filter_by(id=incident.annotation).update({'annotation': description})
            db.session.commit()
        elif request.method == 'DELETE':
            db.session.delete(annotation)
            db.session.commit()
    else:
            annotation = Annotations(annotation=description, incident=incident_id)
            db.session.add(annotation)
            db.session.flush()

            db.session.query(Incidents).filter_by(id=incident_id).update({'annotation': annotation.id})
            db.session.commit()

    return jsonify({'annotation': annotation.to_dict()}), HTTPStatus.OK
