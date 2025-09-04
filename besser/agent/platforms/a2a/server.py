# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
from aiohttp.web_request import Request
from aiohttp import web

from besser.agent.exceptions.logger import logger
from besser.agent.platforms.a2a.error_handler import error_middleware
from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from besser.agent.platforms.a2a.agent_registry import AgentRegistry
from besser.agent.platforms.a2a.error_handler import AgentNotFound

async def get_list_of_agents(request: Request):
    registry: AgentRegistry = request.app["registry"]
    return web.json_response(registry.list())
    # return web.json_response([platform.agent_card for platform in registry.list()])

async def get_agent_card(request: Request):
    platform = request.app["a2a_platform"]
    return web.json_response(platform.get_agent_card())

async def a2a_handler(request: Request):
    body = await request.json()
    agent_id = body.get("agent_id")
    platform = request.app["registry"].get(agent_id)

    if not platform:
        raise AgentNotFound(message=f'Agent ID "{agent_id}" not found')
    
    return await platform.router.aiohttp_handler(request)

# Multi-agent registry (peers). This block is for future use, when agents exist on multiple servers and need to communicate among themselves..
#---------------------------------------------------------------------------
async def list_peers(request: Request):
    return web.json_response(request.app.setdefault("peers", []))

async def add_peer(request: Request):
    body = await request.json()
    # body: {"name": "X", "base": "http://host:port"}
    peers = request.app.setdefault("peers", [])
    if not any(p["base"] == body["base"] for p in peers):
        peers.extend([{"name": body.get("name", body["base"]), "base": body["base"]}])
    return web.json_response({"ok": True, "peers": peers})
#---------------------------------------------------------------------------

def create_app(platform: A2APlatform = None, registry: AgentRegistry = None) -> web.Application:

    # Create the web application and set up routes
    app = web.Application(middlewares=[error_middleware])

    if platform is not None:
        reg = AgentRegistry()
        reg.register("default", platform)
        app["registry"] = reg
    elif registry is not None:
        app["registry"] = registry
    else:
        logger.error("Either platform or registry must be provided to create_app")
        raise ValueError("Either platform or registry must be provided to create_app")

    # Endpoints that are visible to all the users communicating with the platform
    app.router.add_get("/agents", get_list_of_agents)
    app.router.add_get("/agent-card", get_agent_card)
    app.router.add_post("/a2a", a2a_handler)
    return app

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
