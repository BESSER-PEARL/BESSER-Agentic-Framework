import inspect

from aiohttp import web
from aiohttp.web_request import Request
from besser.agent.platforms.a2a.error_handler import JSONRPCError, MethodNotFound, InvalidParams, TaskError
from besser.agent.platforms.a2a.error_handler import INTERNAL_ERROR, PARSE_ERROR, INVALID_REQUEST, TASK_PENDING, TASK_FAILED, TASK_NOT_FOUND

class A2ARouter:
    def __init__(self):
        self.methods = {}

    def register(self, method_name, func):
        self.methods[method_name] = func

    async def handle(self, method_name: str, params: dict):
        
        if method_name not in self.methods:
                raise MethodNotFound(message=f"Method '{method_name}' not found")
        
        if not isinstance(params, dict):
            raise InvalidParams()
        
        method = self.methods[method_name]

        # for handling async tasks, else it is sync
        if inspect.iscoroutinefunction(method):
            return await method(**params)
        else:
            return method(**params)
    
    async def aiohttp_handler(self, request: Request) -> web.json_response:
        request_id = None
        try:
            body = await request.json()
            request_id = body.get("id")
        except Exception:
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": PARSE_ERROR,
                "id": request_id
                })
        
        if "method" not in body or not isinstance(body["method"], str):
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": INVALID_REQUEST, 
                "id": body.get("id")
                })
        
        method = body['method']
        params = body.get('params', {})

        try:
            result = await self.handle(method, params)
            return web.json_response({
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
            })
        # except ValueError as e:
        #     error_map = {
        #     "METHOD_NOT_FOUND": METHOD_NOT_FOUND,
        #     "INVALID_PARAMS": INVALID_PARAMS,
        #     }
        #     return web.json_response({
        #         "jsonrpc": "2.0", 
        #         "error": error_map.get(e.code, INTERNAL_ERROR), 
        #         "id": request_id
        #         })
        except JSONRPCError as e:
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": {"code": e.code, "message": e.message}, 
                "id": request_id
                })
        
        except TaskError as e:
            error_map = {
            "TASK_PENDING": TASK_PENDING,
            "TASK_FAILED": TASK_FAILED,
            "TASK_NOT_FOUND": TASK_NOT_FOUND
            }
            print("TASK_FAILED error_map:", error_map["TASK_FAILED"])
            print(error_map.get(e.code))
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": error_map.get(e.code, INTERNAL_ERROR), 
                "id": request_id
                })
        except Exception as e:
            # print(f"Error: \n{e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {**INTERNAL_ERROR, 
                            "message": str(e)},
                "id": request_id
            })