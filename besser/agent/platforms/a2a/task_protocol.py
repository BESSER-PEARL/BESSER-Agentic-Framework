import uuid, time
from enum import Enum

from besser.agent.platforms.a2a.errors import TaskError

class TaskStatus(str, Enum):
    PENDING="PENDING"; RUNNING="RUNNING"; DONE="DONE"; ERROR="ERROR"

class Task:
    def __init__(self, method: str, params: dict):
        self.id = str(uuid.uuid4())
        self.method = method
        self.params = params
        self.status = TaskStatus.PENDING
        self.created = time.time()
        self.result = None
        self.error = None

tasks = {}  # id -> Task

def create_task(method: str, params: dict):
    '''
    Creates a new task and adds it to the tasks dictionary.
    '''
    t = Task(method, params)
    tasks[t.id] = t
    return {"task_id": t.id, 
            "status": t.status}

def get_status(task_id: str):
    '''
    Gets the status of a task given its task_id.
    '''
    if task_id not in tasks:
        raise TaskError("TASK_NOT_FOUND", f"Task {task_id} not found")
    t = tasks.get(task_id)

    if t.status == TaskStatus.PENDING:
        raise TaskError("TASK_PENDING", "Task is still pending")

    if t.status == TaskStatus.ERROR:
        raise TaskError("TASK_FAILED", t.error)
    
    return {"task_id": t.id, 
            "status": t.status, 
            "result": t.result,
            "error": t.error
            }
