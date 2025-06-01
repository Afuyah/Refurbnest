from flask import jsonify, request
from celery.result import AsyncResult
from . import tasks_bp
from .jobs import test_task
from app import csrf
from functools import wraps
from .facebook_posting import auto_post_products


def json_response(f):
    """Decorator to standardize JSON responses."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return jsonify({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    return wrapper

@tasks_bp.route('/run-test-task', methods=['POST'])
@csrf.exempt
@json_response
def run_test_task():
    """Endpoint to submit a new Celery task."""
    # Optional: Get parameters from request
    # data = request.get_json()
    # Validate data here if needed
    
    task = test_task.delay()  # Add parameters if needed
    return {
        "message": "Task submitted successfully",
        "task_id": task.id
    }, 202

@tasks_bp.route('/task-status/<task_id>', methods=['GET'])
@json_response
def task_status(task_id):
    """Endpoint to check Celery task status."""
    if not task_id:
        raise ValueError("Task ID is required")
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.status == 'FAILURE':
        # Return the exception info if task failed
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": str(task_result.result)
        }
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }
