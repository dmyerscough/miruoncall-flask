
from oncall import db

# import uuid


class Annotations(db.Model):

    __tablename__ = 'annotations'

    id = db.Column(db.Integer, primary_key=True)

    summary = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    incidents = db.relationship('Incidents', back_populates='annotation')

    # created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, annotation):
        self.summary = annotation

    def __repr__(self):
        return f'<Annotation: {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'summary': self.summary,
            'created_at': self.created_at,
        }


class Teams(db.Model):

    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)

    alias = db.Column(db.String(30), unique=True, nullable=True)

    name = db.Column(db.String(255))
    team_id = db.Column(db.String(255))

    summary = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_checked = db.Column(db.DateTime)

    def __init__(self, name, team_id, summary, last_checked):
        self.name = name
        self.team_id = team_id
        self.summary = summary
        self.last_checked = last_checked

    def __repr__(self):
        return f'<Team ID: {self.team_id} - {self.name}>'


class Incidents(db.Model):

    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(25))
    description = db.Column(db.String(100))
    summary = db.Column(db.String(100))

    status = db.Column(db.String(12))

    actionable = db.Column(db.Boolean, nullable=True)

    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, nullable=True)

    incident_id = db.Column(db.String(50))

    urgency = db.Column(db.String(15))

    team = db.Column(db.Integer, db.ForeignKey('teams.id'))

    annotation_id = db.Column(db.Integer, db.ForeignKey('annotations.id'))
    annotation = db.relationship('Annotations', back_populates='incidents')

    def __init__(self, title, description, summary, status, actionable, created_at, incident_id, annotation, urgency, team):
        self.title = title
        self.description = description
        self.summary = summary
        self.status = status
        self.actionable = actionable
        self.created_at = created_at
        self.incident_id = incident_id
        self.annotation = annotation
        self.urgency = urgency
        self.team = team

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'summary': self.summary,
            'status': self.status,
            'actionable': self.actionable,
            'created_at': self.created_at,
            'incident_id': self.incident_id.split('_')[0],
            'urgency': self.urgency,
            'team': self.team,
            'annotation': self.annotation.to_dict() if self.annotation_id else None,
        }

    def __repr__(self):
        return f'<Incident ID: {self.incident_id} - {self.title}>'
