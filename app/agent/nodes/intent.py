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
    system = """
        You classify the latest user message into exactly one intent.

        Possible intents:
        - purchase
        - booking
        - reschedule
        - cancel
        - info
        - chitchat

        Choose purchase whenever the user is showing buying intent, even if they are not
        explicitly asking to buy.

        Examples of purchase:
        - I need a CRM
        - Which package is best?
        - Do you have something for schools?
        - Can your software do payroll?
        - What's the price?
        - Tell me more about this product.
        - I'm looking for an ERP.
        - We need accounting software.
        - I'm comparing solutions.

        Choose info only if the user is clearly asking for general information with no
        interest in purchasing.

        If the conversation is already collecting lead information, keep purchase intent
        until the lead is complete.

        Return only JSON:
        {
        "intent":"purchase"
        }
        """
    
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