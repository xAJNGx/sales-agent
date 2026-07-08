"""
One /chat endpoint that runs the LangGraph agent for a given
(orgId, branchId, sessionId) turn.

Session state (partially-filled lead/booking slots, message history) is
kept in-memory here for simplicity — swap SESSIONS for Redis to run more
than one API replica.
"""

from fastapi import APIRouter, HTTPException

from app.agent.graph import compiled_graph
from app.agent.state import AgentState
from app.core.config import get_tenant
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

# for now just using inmemory state storage per session
SESSIONS: dict[str, AgentState] = {}

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Validate tenant up front — fail fast rather than silently querying nothing.
    try:
        get_tenant(req.orgId, req.branchId)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    state: AgentState = SESSIONS.get(req.sessionId, {
        "org_id": req.orgId,
        "branch_id": req.branchId,
        "session_id": req.sessionId,
        "messages": [],
        "lead_slots": {},
        "booking_slots": {},
        "lead_complete": False,
        "booking_confirmed": False,
        "notify_email": False,
    })

    state["messages"] = state.get("messages", []) + [{"role": "user", "content": req.message}]
    state["user_message"] = req.message

    result = await compiled_graph.ainvoke(state)
    result["messages"] = result.get("messages", []) + [
        {"role": "assistant", "content": result.get("final_response", "")}
    ]
    # notify_email is per-turn, reset so it doesn't re-fire on the next unrelated turn.
    result["notify_email"] = False

    SESSIONS[req.sessionId] = result

    return ChatResponse(
        reply=result.get("final_response", ""),
        intent=result.get("intent", "info"),
        leadComplete=result.get("lead_complete", False),
        bookingConfirmed=result.get("booking_confirmed", False),
    )
