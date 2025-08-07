import sys
sys.path.append("C:/Users/chidambaram/Downloads/GitHub/BESSER-Agentic-Framework_Natarajan")
from multiprocessing import freeze_support

import uvicorn
from besser.agent.core.agent import Agent

def main():
    agent = Agent('TestAgent')
    agent.metadata(endpoints=['http://localhost:8000'], 
                capabilities=["search", "summarise"])
    print(agent.get_agent_card())

    uvicorn.run("besser.agent.core.protocol.a2a.server:app", host="0.0.0.0", port=8000, reload=True)

#required on windows for multiprocessing
if __name__ == '__main__':
    freeze_support()
    main()