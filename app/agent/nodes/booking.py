from datetime import date,datetime, timedelta
from zoneinfo import ZoneInfo

from app.agent.state import AgentState
from app.core.config import get_tenant
from app.db.mongodb import (
    save_appointment,
    update_appointment_status,
)
from app.services import calendar_service
from app.utils.llm import chat_json, chat_text


async def booking_node(state: AgentState) -> dict:
    tenant = get_tenant(state["org_id"], state["branch_id"])
    slots = dict(state.get("booking_slots", {}))
    intent = state["intent"]

    extract_system = f"""
        Extract booking details from the user's latest message.

        Today is {date.today():%Y-%m-%d}. Resolve relative dates (e.g. "tomorrow", "next Monday") against this date.

        Return ONLY a valid JSON object. Include only fields you can confidently determine.

        Schema:
        {{
        "service": string,
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration_minutes": integer,
        "email": string
        }}

        Do not invent values. Omit unknown fields. No markdown or explanations.
        """
    extracted = await chat_json(extract_system, state["user_message"])
    for k, v in extracted.items():
        if v:
            slots[k] = v
    slots.setdefault("duration_minutes", 30)

    lead_email = state.get("lead_slots", {}).get("email") or extracted.get("email")

    if intent == "booking":
        missing = [f for f in ("service", "date", "time") if not slots.get(f)]
        if missing:
            ask_system = (
                f"You are {tenant.sales_rep_name} helping a customer book an appointment at "
                f"{tenant.display_name}. You still need: {missing}. Ask for it conversationally, "
                "in 1-2 sentences, no numbered lists."
            )
            response = await chat_text(ask_system, state.get("messages", [])[-4:])
            return {"booking_slots": slots, "booking_confirmed": False, "final_response": response}
        
        tz = ZoneInfo("Asia/Kathmandu")

        start_dt = datetime.fromisoformat(
            f"{slots['date']}T{slots['time']}:00"
        ).replace(tzinfo=tz)

        end_dt = start_dt + timedelta(
            minutes=extracted.get("duration_minutes", 30)
        )

        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()
                
        available = await calendar_service.check_availability(
            tenant,
            start_iso,
            end_iso,
        )
        if not available:
            return {
                "booking_slots": slots,
                "booking_confirmed": False,
                "final_response": (
                    f"That slot ({slots['date']} {slots['time']}) is already booked at "
                    f"{tenant.display_name} — could you share another date/time that works for you?"
                ),
            }

        event_id = await calendar_service.create_event(
            tenant,
            summary=f"{slots['service']} — {slots.get('name', 'Customer')}",
            start_iso=start_iso,
            duration_minutes=slots["duration_minutes"],
            attendee_email=lead_email,
        )
        await save_appointment(
            state["org_id"], state["branch_id"], state["session_id"],
            event_id, slots["service"], start_iso, lead_email,
        )
        response = (
            f"You're booked! {slots['service']} on {slots['date']} at {slots['time']} "
            f"with {tenant.display_name}."
        )
        return {
            "booking_slots": slots,
            "booking_confirmed": True,
            "calendar_event_id": event_id,
            "notify_email": bool(lead_email),
            "final_response": response,
        }

    if intent == "reschedule":
        missing = [f for f in ("date", "time") if not slots.get(f)]
        event_id = slots.get("existing_event_id") or state.get("calendar_event_id")
        if not event_id:
            return {
                "final_response": "Sure — which appointment would you like to reschedule? "
                                   "Can you share the date it's currently booked for or your confirmation email?"
            }
        if missing:
            response = await chat_text(
                f"You are {tenant.sales_rep_name}. Ask conversationally for the new "
                f"{' and '.join(missing)} for the rescheduled appointment.",
                state.get("messages", [])[-4:],
            )
            return {"booking_slots": slots, "final_response": response}

        new_start_iso = f"{slots['date']}T{slots['time']}:00"
        await calendar_service.reschedule_event(tenant, event_id, new_start_iso, slots.get("duration_minutes", 30))
        await update_appointment_status(state["org_id"], state["branch_id"], event_id, "rescheduled")
        return {
            "booking_slots": slots,
            "booking_confirmed": True,
            "calendar_event_id": event_id,
            "notify_email": bool(lead_email),
            "final_response": f"Done — your appointment has been moved to {slots['date']} at {slots['time']}.",
        }

    if intent == "cancel":
        event_id = slots.get("existing_event_id") or state.get("calendar_event_id")
        if not event_id:
            return {
                "final_response": "Which appointment would you like to cancel? "
                                   "Can you share the date/time or your confirmation email?"
            }
        await calendar_service.cancel_event(tenant, event_id)
        await update_appointment_status(state["org_id"], state["branch_id"], event_id, "cancelled")
        return {
            "booking_confirmed": True,
            "calendar_event_id": event_id,
            "notify_email": bool(lead_email),
            "final_response": "Your appointment has been cancelled. Let us know if you'd like to rebook anytime.",
        }

    return {"final_response": "Sorry, I didn't quite catch what you'd like to do with your booking."}
