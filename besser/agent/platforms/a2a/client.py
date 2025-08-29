import requests, time
from typing import Any, Dict, Optional

class A2AClient:
    def __init__(self, base_url: str, timeout: int = 20):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, method: str, params: Dict[str, Any] | None = None, id: Optional[int] = None):
        payload = {"jsonrpc":"2.0","method":method,"params":params or {}, "id": id or int(time.time()*1000)}
        r = requests.post(f"{self.base}/a2a", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data["result"]

    def card(self):
        r = requests.get(f"{self.base}/agent-card", timeout=self.timeout)
        r.raise_for_status()
        return r.json()
