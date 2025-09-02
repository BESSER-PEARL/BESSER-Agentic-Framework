# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
from aiohttp.web_request import Request
from aiohttp import web
from besser.agent.platforms.a2a.error_handler import error_middleware

from besser.agent.platforms.a2a.a2a_platform import A2APlatform

async def get_agent_card(request: Request):
    platform = request.app["a2a_platform"]
    return web.json_response(platform.get_agent_card())

async def a2a_handler(request: Request):
    platform = request.app["a2a_platform"]
    return await platform.router.aiohttp_handler(request)

# Multi-agent registry (peers)
async def list_peers(request: web.Request):
    return web.json_response(request.app.setdefault("peers", []))

async def add_peer(request: web.Request):
    body = await request.json()
    # body: {"name": "X", "base": "http://host:port"}
    peers = request.app.setdefault("peers", [])
    if not any(p["base"] == body["base"] for p in peers):
        peers.extend([{"name": body.get("name", body["base"]), "base": body["base"]}])
    return web.json_response({"ok": True, "peers": peers})

def create_app(platform: A2APlatform) -> web.Application:
    app = web.Application(middlewares=[error_middleware])
    app["a2a_platform"] = platform
    app.router.add_get("/agent-card", get_agent_card)
    app.router.add_post("/a2a", a2a_handler)
    return app

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
