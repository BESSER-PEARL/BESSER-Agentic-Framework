import logging
import sys
sys.path.append("C:/Users/chidambaram/Downloads/GitHub/BESSER-Agentic-Framework_Natarajan")
import uvicorn

from fastapi import FastAPI
from multiprocessing import freeze_support

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)
logger1 = logging.getLogger(__name__)

def main():
    # agent.metadata(endpoints=['http://localhost:8000'], 
    #             capabilities=["search", "summarise"])
    # print(agent.get_agent_card())

    uvicorn.run("besser.agent.platforms.A2A.server:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")

#required on windows for multiprocessing
if __name__ == '__main__':
    # agent = Agent('TestAgent')
    freeze_support()
    main()