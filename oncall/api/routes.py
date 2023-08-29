from flask import Blueprint, jsonify

from oncall.api.models import Teams

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/teams')
def get_teams():
    """
    Get all teams
    """
    teams = Teams.query.all()

    return jsonify({'teams': [{"id": team.id, "name": team.name, "alias": team.alias} for team in teams]})
