import json

from app.agent.state import AgentState
from app.agent.nodes.constants import REQUIRED_LEAD_FIELDS
from app.core.config import get_tenant
from app.db.mongodb import upsert_lead
from app.utils.llm import chat_json, chat_text



async def lead_capture_node(state: AgentState) -> dict:
    tenant = get_tenant(state["org_id"], state["branch_id"])
    slots = dict(state.get("lead_slots", {}))

    extract_system = """
        Extract sales lead details from the user's latest message.

        Return ONLY a valid JSON object.

        Schema:
        {
        "products": ["string"],
        "reason": "string",
        "budget": "string",
        "name": "string",
        "email": "string",
        "phone": "string"
        }

        Include only fields explicitly mentioned. Do not guess or invent values. Omit missing fields.
        """
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
    persona_system = f"""
        You are {tenant.sales_rep_name}, a friendly sales representative at {tenant.display_name}.

        Your goal is to collect the missing lead information.

        Already collected:
        {json.dumps(slots)}

        Missing fields:
        {json.dumps(missing)}

        Acknowledge the user's latest message naturally, then ask for only 1-2 missing fields in a conversational way. Do not ask for information that has already been collected. Do not use a numbered list, bullet points, or a form. Keep your response to 2-3 sentences.
        """
    response = await chat_text(persona_system, state.get("messages", [])[-4:])

    return {"lead_slots": slots, "lead_complete": False, "final_response": response}

