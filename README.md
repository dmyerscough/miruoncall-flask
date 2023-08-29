
# OnCall

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