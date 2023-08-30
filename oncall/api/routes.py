from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from oncall.api.models import Incidents, Teams

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/teams')
def get_teams():
    """
    Get all teams
    """
    teams = Teams.query.all()

    return jsonify({'teams': [{"id": team.id, "name": team.name, "alias": team.alias} for team in teams]})


@api.route('/incidents/<string:team_id>')
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

    for incident in Incidents.query.filter_by(team=team_id).filter(Incidents.created_at.between(since, until)).order_by('created_at'):
        incidents['summary'].setdefault(incident.created_at.strftime('%Y-%m-%d'), {'low': 0, 'high': 0})
        incidents['summary'][incident.created_at.strftime('%Y-%m-%d')][incident.urgency.lower()] += 1

        incidents['incidents'].append(incident.to_dict())

    return jsonify(incidents)
