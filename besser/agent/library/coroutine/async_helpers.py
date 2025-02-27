import asyncio
import threading


def sync_coro_call(coro):
    def start_event_loop(coro, returnee):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        returnee['result'] = loop.run_until_complete(coro)

    returnee = {'result': None}
    thread = threading.Thread(target=start_event_loop, args=[coro, returnee])
    thread.start()
    thread.join()
    return returnee['result']