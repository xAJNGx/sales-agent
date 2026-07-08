from app.agent.state import AgentState
from app.utils.llm import chat_json


async def intent_router_node(state: AgentState) -> dict:
    """
    Classifies the latest user turn. Runs on every turn (not just the first)
    since intent can shift mid-conversation, e.g. a user asking an FAQ can
    suddenly show purchase interest, or a lead-capture chat can pivot to
    "actually can I just book a demo".
    """
    history = state.get("messages", [])[-6:]  # small rolling window is enough for intent
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    system = (
        "You classify the latest user message in a sales conversation into exactly one "
        "intent: info, purchase, booking, reschedule, cancel, or chitchat.\n"
        "- purchase: user expresses interest in buying/pricing/a product, even implicitly "
        "(e.g. 'how much does this cost', 'do you have anything for X').\n"
        "- booking: user wants to schedule a new appointment/demo/call.\n"
        "- reschedule: user wants to move an existing appointment.\n"
        "- cancel: user wants to cancel an existing appointment.\n"
        "- info: general question answerable from a knowledge base.\n"
        "- chitchat: greetings/small talk with no informational or transactional need.\n"
        "If the conversation is already mid-way through a lead capture or booking flow, and "
        "the user's message looks like an answer to the assistant's last question (e.g. just "
        "a name, email, phone number, date, or time), keep the SAME intent as before rather "
        "than reclassifying it as chitchat/info.\n"
        'Respond ONLY as JSON: {"intent": "..."}'
    )
    result = await chat_json(system, convo)
    intent = result.get("intent", "info")
    if intent not in ("info", "purchase", "booking", "reschedule", "cancel", "chitchat"):
        intent = "info"

    # Sticky intent: if we're mid-flow (slots partially filled) and classifier is unsure,
    # don't drop out of the flow.
    if state.get("lead_slots") and not state.get("lead_complete") and intent in ("info", "chitchat"):
        intent = "purchase"
    if state.get("booking_slots") and not state.get("booking_confirmed") and intent in ("info", "chitchat"):
        intent = state["intent"] if state.get("intent") in ("booking", "reschedule", "cancel") else intent

    return {"intent": intent}