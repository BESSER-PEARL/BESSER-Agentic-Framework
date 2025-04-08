import asyncio
import threading


def sync_coro_call(coro):
    """Executes an asynchronous coroutine synchronously.

    This function runs the given coroutine in a separate thread with its own event loop,
    allowing synchronous code to await the result of an async function.

    Args:
        coro (coroutine): The asynchronous coroutine to execute.

    Returns:
        Any: The result of the coroutine execution.
    """
    def start_event_loop(coro, returnee):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        returnee['result'] = loop.run_until_complete(coro)

    returnee = {'result': None}
    thread = threading.Thread(target=start_event_loop, args=[coro, returnee])
    thread.start()
    thread.join()
    return returnee['result']