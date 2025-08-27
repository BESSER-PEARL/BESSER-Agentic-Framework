# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
from aiohttp.web_request import Request
from aiohttp import web

async def get_agent_card(request: Request):
    platform = request.app["a2a_platform"]
    return web.json_response(platform.get_agent_card())

async def a2a_handler(request: Request):
    platform = request.app["a2a_platform"]
    return await platform.router.aiohttp_handler(request)

def create_app(platform) -> web.Application:
    app = web.Application()
    app["a2a_platform"] = platform
    app.router.add_get("/agent-card", get_agent_card)
    app.router.add_post("/a2a", a2a_handler)
    return app

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
