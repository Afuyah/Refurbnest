from app.celery import celery
import time
import logging
from datetime import datetime
from celery.exceptions import MaxRetriesExceededError
from app import create_app  # Import your Flask app factory

logger = logging.getLogger(__name__)

@celery.task(
    name="tasks.test_task",
    bind=True,  # Gives access to self parameter
    max_retries=3,
    default_retry_delay=30,  # 30 seconds between retries
    soft_time_limit=60,  # 60 seconds soft limit
    time_limit=120  # 120 seconds hard limit
)
def test_task(self):
    """Example Celery task that simulates work and returns a message."""
    try:
        # Create Flask app context for task
        flask_app = create_app()
        with flask_app.app_context():
            start_time = datetime.utcnow()
            logger.info("⏳ Starting test_task at %s", start_time)
            
            # Simulate work
            time.sleep(3)
            
            # Task logic would go here
            result = "Hello from Celery!"
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                "✅ Task completed successfully in %.2f seconds. Result: %s",
                duration,
                result
            )
            return result
            
    except Exception as exc:
        logger.error("❌ Task failed with error: %s", str(exc), exc_info=True)
        try:
            # Retry the task
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.critical("🚨 Max retries exceeded for task!")
            raise