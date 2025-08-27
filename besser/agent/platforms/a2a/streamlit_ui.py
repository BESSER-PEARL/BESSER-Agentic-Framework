# streamlit run apps/streamlit_ui.py
import json, requests, streamlit as st

st.set_page_config(page_title="BESSER A2A", layout="wide")
st.title("BESSER A2A Control Panel")

# In production, load from a registry service / config
default_agents = [
    {"name":"LocalAgent", "base":"http://localhost:8000"},
]

agents = st.session_state.get("agents", default_agents)
with st.sidebar:
    st.header("Agents")
    for a in agents:
        st.write(f"• {a['name']} → {a['base']}")

    st.subheader("Add Agent")
    name = st.text_input("Name", "")
    base = st.text_input("Base URL", "http://localhost:8000")
    if st.button("Add"):
        agents.append({"name":name or base, "base":base})
        st.session_state["agents"] = agents
        st.rerun()

agent = st.selectbox("Select agent", agents, format_func=lambda x: x["name"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Agent Card")
    if st.button("Fetch Card"):
        resp = requests.get(f"{agent['base']}/agent-card", timeout=10)
        st.code(json.dumps(resp.json(), indent=2))

with col2:
    st.subheader("JSON-RPC Call")
    method = st.text_input("method", "ping")
    params_raw = st.text_area("params (JSON)", "{}", height=120)
    req_id = st.number_input("id", value=1, min_value=1, step=1)
    if st.button("Send"):
        try:
            params = json.loads(params_raw or "{}")
            payload = {"jsonrpc":"2.0","method":method,"params":params,"id":req_id}
            resp = requests.post(f"{agent['base']}/a2a", json=payload, timeout=20)
            st.code(json.dumps(resp.json(), indent=2))
        except Exception as e:
            st.error(str(e))
