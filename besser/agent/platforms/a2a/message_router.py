from aiohttp import web
from aiohttp.web_request import Request

class A2ARouter:
    def __init__(self):
        self.methods = {}

    def register(self, method_name, func):
        self.methods[method_name] = func

    def handle(self, method_name, params):
        if method_name not in self.methods:
            raise Exception(f"Method '{method_name}' not found")
        return self.methods[method_name](**params)
    
    async def aiohttp_handler(self, request: Request):
        body = await request.json()
        try:
            result = self.handle(body['method'], body.get('params', {}))
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
