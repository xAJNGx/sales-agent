from app.agent.state import AgentState
from app.core.config import get_tenant
from app.services import email_service



async def notify_node(state: AgentState) -> dict:
    if not state.get("notify_email"):
        return {}

    tenant = get_tenant(state["org_id"], state["branch_id"])
    to_email = state.get("lead_slots", {}).get("email")
    # to_email = "harcoded@gmail.com" #for testing purpose comment this out if you want to check 
    if not to_email:
        return {}

    slots = state.get("booking_slots", {})
    service = slots.get("service", "your appointment")
    start_iso = f"{slots.get('date', '')}T{slots.get('time', '')}"

    try:
        if state["intent"] == "booking":
            await email_service.send_booking_confirmation(tenant, to_email, service, start_iso)
        elif state["intent"] == "reschedule":
            await email_service.send_reschedule_confirmation(tenant, to_email, service, start_iso)
        elif state["intent"] == "cancel":
            await email_service.send_cancellation_confirmation(tenant, to_email, service)
    except RuntimeError:
        pass

    return {}
