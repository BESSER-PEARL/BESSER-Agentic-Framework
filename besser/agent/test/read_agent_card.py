import requests
from besser.agent.core.agent import Agent

response = requests.get("http://localhost:8000/agent-card", verify=False)

if response.status_code == 200:
    print("Agent Card:")
    print(response.json())
else:
    print(f"Failed to fetch agent card: {response.status_code} - {response.text}")