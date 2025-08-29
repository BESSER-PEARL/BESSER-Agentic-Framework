import inspect
import asyncio

from besser.agent.platforms.a2a.task_protocol import tasks, TaskStatus

async def execute_task(task_id: str, router):
    if task_id not in tasks:
        return {"error": "Task not found"}
    
    t = tasks.get(task_id)
    try:
        t.status = TaskStatus.RUNNING
        result = router.handle(t.method, t.params)
        print(f"Before execution: method={t.method}, got={result}, type={type(result)}")
        if inspect.iscoroutine(result):
            result = await result
        t.result = result
        t.status = TaskStatus.DONE
    except Exception as e:
        t.status = TaskStatus.ERROR
        t.error = str(e)
    print(f"After Execution: method={t.method}, got={result}, type={type(result)}")
    return {
        "task_id": t.id,
        "status": t.status,
        "result": t.result,
        "error": t.error
    }