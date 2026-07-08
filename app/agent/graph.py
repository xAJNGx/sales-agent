"""
Wires the nodes into a LangGraph StateGraph.

Flow:
    START -> intent_router -> {rag | lead_capture | booking | chitchat} -> notify -> END

`notify` only fires an email when booking/reschedule/cancel actually
completed this turn (state["notify_email"] is set by booking_node); it's a
no-op fan-in otherwise, which keeps the graph shape uniform.
"""
from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    booking_node,
    chitchat_node,
    intent_router_node,
    lead_capture_node,
    notify_node,
    rag_node,
)
from app.agent.state import AgentState



def route_from_intent(state: AgentState) -> str:
    intent = state["intent"]
    if intent == "purchase":
        return "lead_capture"
    if intent in ("booking", "reschedule", "cancel"):
        return "booking"
    if intent == "chitchat":
        return "chitchat"
    return "rag"  # "info" and fallback


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("lead_capture", lead_capture_node)
    graph.add_node("booking", booking_node)
    graph.add_node("chitchat", chitchat_node)
    graph.add_node("notify", notify_node)

    graph.set_entry_point("intent_router")

    graph.add_conditional_edges(
        "intent_router",
        route_from_intent,
        {
            "rag": "rag",
            "lead_capture": "lead_capture",
            "booking": "booking",
            "chitchat": "chitchat",
        },
    )

    # Every branch fans into notify, which only actually sends email
    # when booking_node set notify_email=True this turn.
    graph.add_edge("rag", "notify")
    graph.add_edge("lead_capture", "notify")
    graph.add_edge("booking", "notify")
    graph.add_edge("chitchat", "notify")
    graph.add_edge("notify", END)

    return graph.compile()


# Compiled once, reused across requests.
compiled_graph = build_graph()

if __name__ == "__main__":
    import asyncio
    from pprint import pprint
    

    async def main():
        graph = build_graph()

        initial_state = {
            "org_id": "org_1",
            "branch_id": "branch_a",
            "session_id": "test-session",
            "user_message": "I'd like to book a demo for tomorrow at 3 PM.",
            "messages": [
                {
                    "role": "user",
                    "content": "I'd like to book a demo for tomorrow at 3 PM.",
                }
            ],
            "intent": "",
            "lead_slots": {},
            "lead_complete": False,
            "lead_saved": False,
            "booking_slots": {},
            "booking_confirmed": False,
            "calendar_event_id": None,
            "notify_email": False,
            "retrieved_chunks": [],
            "rag_answer": "",
            "final_response": "",
        }

        result = await graph.ainvoke(initial_state)

        print("\n=== Final State ===")
        pprint(result)

        print("\n=== Assistant Response ===")
        print(result["final_response"])

    asyncio.run(main())
