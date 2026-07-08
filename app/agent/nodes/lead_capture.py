import json

from app.agent.state import AgentState
from app.agent.nodes.constants import REQUIRED_LEAD_FIELDS
from app.core.config import get_tenant
from app.db.mongodb import upsert_lead
from app.utils.llm import chat_json, chat_text



async def lead_capture_node(state: AgentState) -> dict:
    tenant = get_tenant(state["org_id"], state["branch_id"])
    slots = dict(state.get("lead_slots", {}))

    extract_system = (
        "Extract any of the following sales-lead fields present in the user's latest message. "
        "Only include fields actually stated — do not guess or invent values.\n"
        "Fields: products (list of strings), reason (string - why they want it), "
        "budget (string), name (string), email (string), phone (string).\n"
        'Respond ONLY as JSON with just the fields you found, e.g. {"email": "a@b.com"}.'
    )
    extracted = await chat_json(extract_system, state["user_message"])
    for k, v in extracted.items():
        if k == "products" and v:
            slots["products"] = list(set(slots.get("products", []) + (v if isinstance(v, list) else [v])))
        elif v:
            slots[k] = v

    missing = [f for f in REQUIRED_LEAD_FIELDS if not slots.get(f)]

    if not missing:
        await upsert_lead(state["org_id"], state["branch_id"], state["session_id"], slots)
        response = (
            f"Perfect, thanks {slots.get('name', '')}! I've got everything I need — "
            f"{tenant.sales_rep_name} from our team will reach out to you at {slots.get('email')} "
            "shortly to discuss next steps. In the meantime, would you like to book a quick "
            "call so we can go over details together?"
        )
        return {"lead_slots": slots, "lead_complete": True, "lead_saved": True, "final_response": response}

    # Ask conversationally for 1-2 missing fields at a time rather than a checklist dump.
    persona_system = (
        f"You are {tenant.sales_rep_name}, a friendly, low-pressure sales rep at "
        f"{tenant.display_name}. You're chatting with a prospective customer. You already "
        f"know: {json.dumps(slots)}. You still need: {missing}. Naturally acknowledge what "
        "they just said, then ask for 1-2 of the missing pieces of information in a warm, "
        "conversational way — never as a numbered list or form. Keep it to 2-3 sentences."
    )
    response = await chat_text(persona_system, state.get("messages", [])[-4:])

    return {"lead_slots": slots, "lead_complete": False, "final_response": response}

