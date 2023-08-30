from sqlalchemy import and_
from flask import Blueprint, jsonify, request

from oncall.api.models import Teams, Incidents


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

    since = '2023-08-20'
    until = '2023-08-29'

    incidents = {'incidents': [], 'summary': {}}

    for incident in Incidents.query.filter_by(team=team_id).filter(Incidents.created_at.between(since, until)).order_by('created_at'):
        incidents['summary'].setdefault(incident.created_at.strftime('%Y-%m-%d'), {'low': 0, 'high': 0})
        incidents['summary'][incident.created_at.strftime('%Y-%m-%d')][incident.urgency.lower()] += 1

        incidents['incidents'].append(incident.to_dict())

    return jsonify(incidents)
