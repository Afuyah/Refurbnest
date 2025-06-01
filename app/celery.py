import eventlet
eventlet.monkey_patch()  # Must remain first

from celery import Celery
from flask import Flask
from typing import Any
from config import Config

celery = Celery(
    __name__,
    broker=Config.CELERY_BROKER_URL,
    backend=Config.RESULT_BACKEND,  # More explicit name
    broker_connection_retry_on_startup=True  # Important for containerized environments
)

def init_celery(app: Flask) -> None:
    """Initialize Celery with Flask application context.
    
    Args:
        app: Flask application instance
    """
    # Update Celery config from Flask app config
    celery.conf.update(app.config)
    
    # Set more explicit task routing if needed
    celery.conf.task_routes = {
        'app.tasks.*': {'queue': 'default'},
        'app.tasks.high_priority.*': {'queue': 'high_priority'}
    }
    
    # Configure result expiration (24 hours by default)
    celery.conf.result_expires = 60 * 60 * 24
    
    # Context task class with improved typing
    class ContextTask(celery.Task):
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            with app.app_context():
                try:
                    return self.run(*args, **kwargs)
                except Exception as e:
                    # Add custom error handling here
                    app.logger.error(f"Task failed: {str(e)}")
                    raise

    celery.Task = ContextTask
    celery.set_default()  # this instance is used everywhere