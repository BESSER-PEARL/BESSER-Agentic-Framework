import requests
import time
import httpx

class A2AClient:
    def __init__(self, base_url: str, timeout: int = 20):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, method: str, params: dict | None = None, id: int | None = None):
        payload = {"jsonrpc":"2.0","method":method,"params":params or {}, "id": id or int(time.time()*1000)}
        r = requests.post(f"{self.base}/run", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data["result"]

    def card(self):
        r = requests.get(f"{self.base}/agent-card", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    async def stream(self, method: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base}", json={"jsonrpc":"2.0","method":method,"params":params or {}, "id":int(time.time()*1000)}) as r:
                async for line in r.aiter_lines():
                    if line.strip():
                        yield line
                        