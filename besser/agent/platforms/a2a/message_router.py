import inspect
import asyncio

from aiohttp import web
from aiohttp.web_request import Request

from besser.agent.exceptions.logger import logger
from besser.agent.platforms.a2a.error_handler import JSONRPCError, MethodNotFound, InvalidParams, TaskError
from besser.agent.platforms.a2a.error_handler import INTERNAL_ERROR, PARSE_ERROR, INVALID_REQUEST, TASK_PENDING, TASK_FAILED, TASK_NOT_FOUND
from besser.agent.platforms.a2a.task_protocol import create_task, get_status, execute_task, list_all_tasks

class A2ARouter:
    def __init__(self) -> None:
        self.methods = {}

    def register(self, method_name, func) -> None:
        self.methods[method_name] = func

    async def handle(self, method_name: str, params: dict) -> web.json_response:
        
        if method_name not in self.methods:
                logger.error(f"Method '{method_name}' not found")
                raise MethodNotFound(message=f"Method '{method_name}' not found")
        
        if not isinstance(params, dict):
            logger.error(f"Params must be a dictionary")
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
            logger.error(PARSE_ERROR)
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": PARSE_ERROR,
                "id": request_id
                })
        
        if "method" not in body or not isinstance(body["method"], str):
            logger.error(INVALID_REQUEST)
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
            logger.error(error_map.get(e.code, INTERNAL_ERROR))
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": error_map.get(e.code, INTERNAL_ERROR), 
                "id": request_id
                })
        except Exception as e:
            # print(f"Error: \n{e}")
            logger.error(f"Internal error: {str(e)}")
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {**INTERNAL_ERROR, 
                            "message": str(e)},
                "id": request_id
            })
    
    def register_task_methods(self, platform) -> None:
        '''
        Auto-register task endpoints.
        '''
        self.register("create_task_and_run", platform.rpc_create_task)
        self.register("task_create", platform.create_task)
        self.register("task_status", platform.get_status)