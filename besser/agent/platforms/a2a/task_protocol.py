import uuid
import time
import inspect
import asyncio
from enum import Enum

from besser.agent.platforms.a2a.error_handler import TaskError
from besser.agent.exceptions.logger import logger

class TaskStatus(str, Enum):
    """
    Constants for task status
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"

class Task:
    """
    Task initialises each task submitted to the agent that is added to the queue to be executed
    """
    def __init__(self, method: str, params: dict):
        self.id = str(uuid.uuid4())
        self.method = method
        self.params = params
        self.status = TaskStatus.PENDING
        self.created = time.time()
        self.result = None
        self.error = None
        self.subscribers = set()
    
    def subscribe(self, q: asyncio.Queue = None) -> asyncio.Queue:
        """
        Return an asyncio.Queue that will receive updates for this task.
        Caller should read until cancelled/closed.
        """
        if q is None:
            q = asyncio.Queue()
        self.subscribers.add(q)

        if hasattr(self, "result") and self.result:
            q.put_nowait({"type": "task_snapshot", "task": self.result})
        
        return q
    
    def unsubscribe(self, q: asyncio.Queue) -> None:
        """
        Remove tasks that do not need any monitoring.
        """
        try:
            self.subscribers.remove(q)
        except KeyError:
            # It's safe to ignore if the subscriber is not present; no action needed.
            pass

    async def notify_subscribers(self, message: dict) -> None:
        """
        Push non-blocking message to all subscribers in queues (awaits put).
        """
        for q in list(self.subscribers):
            try:
                await q.put(message)
            # except asyncio.QueueFull:
            except Exception:
                # if a subscriber is slow, drop updates or consider backpressure
                pass

tasks = {}  # Stores task_id and status -> Task

def create_task(method: str, params: dict, task_storage: dict = None) -> dict:
    """
    This is an internal method. It creates a new task and adds it to the tasks dictionary.
    """
    t = Task(method, params)
    target_storage = task_storage if task_storage is not None else tasks
    target_storage[t.id] = t
    return {"task_id": t.id, 
            "status": t.status}

def get_status(task_id: str, task_storage: dict = None) -> dict:
    """
    This is an internal method. It gets the status of a task given its task_id.
    """
    store = task_storage if task_storage is not None else tasks
    if task_id not in store:
        raise TaskError("TASK_NOT_FOUND", f"Task {task_id} not found")
    t = store.get(task_id)

    if t.status == TaskStatus.PENDING:
        raise TaskError("TASK_PENDING", "Task is still pending")

    if t.status == TaskStatus.ERROR:
        raise TaskError("TASK_FAILED", t.error)
    
    return {"task_id": t.id, 
            "status": t.status, 
            "result": t.result,
            "error": t.error
            }

def list_all_tasks(task_storage: dict = None) -> list:
    """
    Return status info for all tasks.
    """
    store = task_storage if task_storage is not None else tasks
    return [
        {
            "task_id": t.id,
            "status": t.status,
            "result": t.result,
            "error": t.error
        }
        for t in store.values()
    ]

async def execute_task(task_id: str, router, task_storage: dict = None, coroutine_func=None, params=None) -> dict:

    """
    This is an internal method. It executes a task given its task_id.
    In the case of Orchestration tasks, a coroutine function can be provided that
    will be awaited with task parameters instead of the default method handler.
    """
    store = task_storage if task_storage is not None else tasks
    if task_id not in store:
        raise TaskError("TASK_NOT_FOUND", f"Task {task_id} not found")
    
    t = store.get(task_id)
    
    try:
        t.status = TaskStatus.RUNNING
        if coroutine_func:
            result = await coroutine_func(router, params or t.params)
        else:
            result = await router.handle(t.method, t.params)
        
        if inspect.iscoroutine(result):
            result = await result
        t.result = result
        t.status = TaskStatus.DONE
    except Exception as e:
        t.status = TaskStatus.ERROR
        t.error = str(e)
        raise TaskError("TASK_FAILED", t.error)

    # notify subscribers of final state
    if getattr(t, "is_orchestration", False) is False:
        await t.notify_subscribers({
            "type": "task_final",
            "task_id": t.id,
            "status": t.status,
            "result": t.result,
            "error": t.error
        })
    
    return {
        "task_id": t.id,
        "status": t.status,
        "result": t.result,
        "error": t.error
    }
