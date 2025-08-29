import inspect
import asyncio

from aiohttp import web
from aiohttp.web_request import Request

class A2ARouter:
    def __init__(self):
        self.methods = {}

    def register(self, method_name, func):
        self.methods[method_name] = func

    async def handle(self, method_name: str, params: dict):
        if method_name not in self.methods:
            raise Exception(f"Method '{method_name}' not found")
        method = self.methods[method_name]
        # for handling async tasks, else it is sync
        if inspect.iscoroutinefunction(method):
            return await method(**params)
        else:
            return method(**params)
    
    async def aiohttp_handler(self, request: Request) -> web.json_response:
        try:
            body = await request.json()
            result = await self.handle(body['method'], body.get('params', {}))
            return web.json_response({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id")
            })
        except Exception as e:
            print(f"Error: \n{e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": str(e)},
                "id": body.get("id")
            })
