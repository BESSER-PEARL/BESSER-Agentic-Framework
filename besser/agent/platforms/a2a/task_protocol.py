import uuid, time
from enum import Enum

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
    t = Task(method, params)
    tasks[t.id] = t
    return {"task_id": t.id, 
            "status": t.status}

def get_status(task_id: str):
    if task_id not in tasks:
        return {"error": "Task not found"}
    t = tasks.get(task_id)
    return {"task_id": t.id, 
            "status": t.status, 
            "result": t.result, 
            "error": t.error}
