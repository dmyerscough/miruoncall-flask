
from celery import current_app as current_celery_app


def make_celery(app):
    celery = current_celery_app
    celery.conf.update(app.config, namespace='CELERY')

    celery.autodiscover_tasks(['oncall.incidents.tasks'])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
