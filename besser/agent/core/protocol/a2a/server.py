from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from besser.agent.core.protocol.a2a.message_router import A2ARouter
from besser.agent.core.agent import Agent

app = FastAPI()
router = A2ARouter()

agent = Agent('TestAgent')
agent.metadata(endpoints=['http://localhost:8000'], capabilities=["search", "summarise"])

#placeholder for agent logic: dummy function
def ping():
    return "pong"

router.register("ping", ping) #method_name, function

@app.get("/agent-card")
async def get_agent_card():
    return agent.get_agent_card()

@app.post("/a2a")
async def a2a_handler(request: Request):
    body = await request.json()
    # Placeholder: test by echo the request
    try: 
        result = router.handle(body['method'], body.get('params', {}))
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": result,
            "id": body.get("id", None)
        })
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": str(e)},
            "id": body.get("id")
        })
