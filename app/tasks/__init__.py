from flask import Blueprint

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

from . import views  
