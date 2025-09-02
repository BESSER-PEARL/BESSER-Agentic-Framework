import inspect
import asyncio

from besser.agent.platforms.a2a.task_protocol import tasks, TaskStatus, TaskError
from besser.agent.platforms.a2a.errors import TaskError

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