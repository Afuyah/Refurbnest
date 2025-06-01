import eventlet
eventlet.monkey_patch()

from app import create_app
from app.celery import celery
import app.tasks.jobs 

app = create_app()
celery.conf.update(app.config)
