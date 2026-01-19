from aiohttp import web

# JSON-RPC standard errors
PARSE_ERROR = {"code": -32700, "message": "Parse error"}
INVALID_REQUEST = {"code": -32600, "message": "Invalid Request"}
METHOD_NOT_FOUND = {"code": -32601, "message": "Method not found"}
INVALID_PARAMS = {"code": -32602, "message": "Invalid params"}
INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}

# Custom task-related errors for A2A
TASK_PENDING = {"code": -32000, "message": "Task is still pending"}
TASK_FAILED = {"code": -32001, "message": "Task execution failed"}
TASK_NOT_FOUND = {"code": -32002, "message": "Task not found"}

class JSONRPCError(Exception):
    def __init__(self, code=-32000, message="Server error", data=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

class AgentNotFound(JSONRPCError):
    def __init__(self, message="Agent not found"):
        super().__init__(-32003, message)

class MethodNotFound(JSONRPCError):
    def __init__(self, message="Method not found"):
        super().__init__(-32601, message)

class InvalidParams(JSONRPCError):
    def __init__(self, message="Invalid params"):
        super().__init__(-32602, message)

class TaskError(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message)
        self.code = code
        self.message = message

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
