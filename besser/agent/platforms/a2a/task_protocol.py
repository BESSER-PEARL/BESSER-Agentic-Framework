import uuid, time
import inspect
from enum import Enum

from besser.agent.platforms.a2a.error_handler import TaskError

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

tasks = {}  # Stores task_id and status -> Task

def create_task(method: str, params: dict):
    '''
    This is an internal method. It creates a new task and adds it to the tasks dictionary.
    '''
    t = Task(method, params)
    tasks[t.id] = t
    return {"task_id": t.id, 
            "status": t.status}

def get_status(task_id: str):
    '''
    This is an internal method. It gets the status of a task given its task_id.
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

async def execute_task(task_id: str, router):
    if task_id not in tasks:
        raise TaskError("TASK_NOT_FOUND", f"Task {task_id} not found")
    
    t = tasks.get(task_id)
    # print(f"[EXECUTOR] Starting execution of task {t}")
    
    try:
        t.status = TaskStatus.RUNNING
        result = await router.handle(t.method, t.params)
        # print(f"Before execution: method={t.method}, got={result}, type={type(result)}")
        if inspect.iscoroutine(result):
            result = await result
        t.result = result
        t.status = TaskStatus.DONE
    except Exception as e:
        t.status = TaskStatus.ERROR
        t.error = str(e)
        raise TaskError("TASK_FAILED", t.error)
    # print(f"After Execution: method={t.method}, got={result}, type={type(result)}")
    # print(f"[EXECUTOR] Finished execution of task {t}, status={t.status}. Got {t.result}")
    return {
        "task_id": t.id,
        "status": t.status,
        "result": t.result,
        "error": t.error
    }

# async def _execute_task_bg(task_id: str, router):
#     try:
#         await execute_task(task_id, router)
#     except TaskError as e:
#         # Already handled in execute_task: status updated inside the task object
#         # Exceptions are caught internally, preventing "Task exception was never retrieved".
#         print(f"[EXECUTOR] Task {task_id} failed: {e}")
