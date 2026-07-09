import json

from app.agent.state import AgentState
from app.agent.nodes.constants import LEAD_ORDER
from app.core.config import get_tenant
from app.db.mongodb import upsert_lead
from app.utils.llm import chat_json, chat_text


async def lead_capture_node(state: AgentState) -> dict:
    tenant = get_tenant(state["org_id"], state["branch_id"])
    slots = dict(state.get("lead_slots", {}))

    extract_system = """
        You extract sales lead information from the conversation.

        Return ONLY valid JSON.

        Schema:

        {
            "products": ["string"],
            "reason": "string",
            "budget": "string",
            "name": "string",
            "email": "string",
            "phone": "string"
        }

        Rules:

        - Extract only information explicitly stated.
        - Do not infer or guess.
        - Products may contain multiple values.
        - Budget can be an approximate range.
        - Ignore assistant messages unless they repeat user-provided information.
        - Omit missing fields.
        """
    conversation = "\n".join(
        m["content"]
        for m in state["messages"][-8:]
        if m["role"] == "user"
    )
    extracted = await chat_json(extract_system, conversation)
    
    updated = False
    
    for k, v in extracted.items():
        if not v:
            continue

        if k == "products":
            existing = set(slots.get("products", []))
            new = set(v if isinstance(v, list) else [v])

            merged = list(existing | new)

            if merged != slots.get("products", []):
                slots["products"] = merged
                updated = True

        else:
            if slots.get(k) != v:
                slots[k] = v
                updated = True

    # Save whenever we learned something new
    if updated:
        await upsert_lead(
            state["org_id"],
            state["branch_id"],
            state["session_id"],
            slots,
        )

    missing = [f for f in LEAD_ORDER if not slots.get(f)]

    if not missing:
        response = (
            f"Perfect, thanks {slots.get('name', '')}! I've got everything I need — "
            f"{tenant.sales_rep_name} from our team will reach out to you at {slots.get('email')} "
            "shortly to discuss next steps. In the meantime, would you like to book a quick "
            "call so we can go over details together?"
        )
        return {"lead_slots": slots, "lead_complete": True, "lead_saved": True, "final_response": response}

    # Ask conversationally for 1-2 missing fields at a time rather than a checklist dump.
    persona_system = f"""
        You are {tenant.sales_rep_name}, a professional sales consultant at
        {tenant.display_name}.

        The customer has shown genuine purchase interest.

        Your goals are:

        1. Understand what they need.
        2. Recommend the right solution.
        3. Naturally collect lead information.
        4. Never sound like a form.

        Already collected:

        {json.dumps(slots, indent=2)}

        Missing fields:

        {json.dumps(missing)}

        Guidelines:

        - Continue the conversation naturally.
        - Acknowledge what the customer said.
        - If product interest is still unclear, ask about it first.
        - Then understand why they need it.
        - Then discuss budget naturally.
        - Only after understanding their needs should you ask for name,
        email, or phone.
        - Never ask more than two missing pieces of information in one reply.
        - Avoid sounding like a questionnaire.
        - If enough information exists to answer the user's question,
        answer it first before asking for the next missing detail.
        - Keep replies under 3 short paragraphs.
        - Be friendly and consultative like a real salesperson.
        """
    response = await chat_text(persona_system, state.get("messages", [])[-4:])

    return {"lead_slots": slots, "lead_complete": False, "final_response": response}

