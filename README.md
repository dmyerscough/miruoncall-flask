
# Starting Oncall webapp

```bash
$ FLASK_APP=oncall/app.py flask run
```

# Celery

Configure celery to run the periodic tasks.

```bash
$ celery -A oncall.app.celery beat --loglevel=info
```

```bash
$ export PAGERDUTY_KEY="u+XXXXXXXXX"
$ celery -A oncall.app.celery worker --loglevel=info
```

# Database Setup

```bash
$ FLASK_APP=oncall/app.py flask db init
$ FLASK_APP=oncall/app.py flask db migrate -m "Initial migration."
$ FLASK_APP=oncall/app.py flask db upgrade
```

# Querying incidents

```bash
$ curl -s -XPOST -H 'Content-type: application/json' --data '{"since": "2023-08-20", "until": "2023-08-31"}' http://127.0.0.1:5000/api/v1/incidents/223
```

# Querying teams

```bash
$ curl -s -XGET http://127.0.0.1:5000/api/v1/teams
```

# Create annotation

```bash
$ curl -s -XPOST -H 'Content-type: application/json' --data '{"annotation": "Test annotation"}' http://127.0.0.1:5000/api/v1/incident/Q2U9JA89EK0C17_PPXN2GC/annotation
```

# Update annotation

```bash
$ curl -s -XPUT -H 'Content-type: application/json' --data '{"annotation": "Test annotation 2"}' http://127.0.0.1:5000/api/v1/incident/Q2U9JA89EK0C17_PPXN2GC/annotation
```

# Delete annotation

```bash
$ curl -s -XDELETE -H 'Content-type: application/json' http://127.0.0.1:5000/api/v1/incident/2/annotation
```