# from typing import TYPE_CHECKING

import inspect

from aiohttp import web
from aiohttp.web_request import Request

from besser.agent.exceptions.logger import logger
from besser.agent.platforms.a2a.error_handler import JSONRPCError, MethodNotFound, InvalidParams, TaskError
from besser.agent.platforms.a2a.error_handler import INTERNAL_ERROR, PARSE_ERROR, INVALID_REQUEST, TASK_PENDING, TASK_FAILED, TASK_NOT_FOUND
from besser.agent.platforms.a2a.agent_registry import AgentRegistry
# if TYPE_CHECKING:
#     from besser.agent.platforms.a2a.a2a_platform import A2APlatform

class A2ARouter:
    def __init__(self) -> None:
        self.methods = {}

    def register(self, method_name, func) -> None:
        '''
        Register a method (coupled to its name, also called as key) that can be called via RPC.
        '''
        self.methods[method_name] = func

    async def handle(self, method_name: str, params: dict) -> web.json_response:
        """
        Execute the method given its name and parameters
        """
        
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
        """
        Handle HTTP requests from the server
        """
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
    
    def register_task_methods(self, platform: 'A2APlatform') -> None:
        """
        Auto-register internal methods for creating, executing and getting task status.
        """
        self.register("create_task_and_run", platform.rpc_create_task)
        self.register("task_create", platform.create_task)
        self.register("task_status", platform.get_status)
    
    # 
    def register_orchestration_methods(self, platform: 'A2APlatform', registry: AgentRegistry) -> None:
        """
        Register methods used for orchestration in its router. Enables one agent to call another agent.
        """
        async def call_agent_rpc(target_agent_id: str, method: str, params: dict):
            return await platform.rpc_call_agent(target_agent_id, method, params, registry)

        self.register("call_agent", call_agent_rpc)
