from aiohttp import web
from besser.agent.platforms.a2a.errors import JSONRPCError

def error_response(exc: Exception, request_id=None):
    if isinstance(exc, JSONRPCError):
        return {
            "jsonrpc": "2.0",
            "error": {"code": exc.code, "message": exc.message, "data": exc.data},
            "id": request_id,
        }
    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(exc)},
            "id": request_id,
        }

@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except JSONRPCError as e:
        return web.json_response(error_response(e))
    except Exception as e:
        return web.json_response(error_response(e))
