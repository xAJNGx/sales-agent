from app.agent.state import AgentState

async def chitchat_node(state: AgentState) -> dict:
    return {"final_response": "Hey! How can I help you today?"}