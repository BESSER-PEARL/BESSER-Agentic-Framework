from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from besser.agent.core.protocol.a2a.message_router import A2ARouter 

app = FastAPI()
router = A2ARouter()

#placeholder: dummy function
def ping():
    return "pong"

router.register("ping", ping) #method_name, function

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
