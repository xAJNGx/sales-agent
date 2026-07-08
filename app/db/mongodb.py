"""
MongoDB access for leads and appointments (async, via Motor).

Every read/write is scoped by (org_id, branch_id) so tenants never see or
overwrite each other's data even though they share one database.
"""


from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def _get_db():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client[settings.mongodb_db_name]


def _leads():
    return _get_db()["leads"]


def _appointments():
    return _get_db()["appointments"]


async def upsert_lead(org_id: str, branch_id: str, session_id: str, lead_slots: dict) -> str:
    """
    Upsert a lead keyed by (org, branch, email) once we have an email —
    until then keyed by session_id, so partial progress isn't lost if the
    user drops off mid-conversation.
    """
    key = {"orgId": org_id, "branchId": branch_id}
    if lead_slots.get("email"):
        key["email"] = lead_slots["email"]
    else:
        key["sessionId"] = session_id

    doc = {
        **key,
        "sessionId": session_id,
        "products": lead_slots.get("products", []),
        "reason": lead_slots.get("reason"),
        "budget": lead_slots.get("budget"),
        "name": lead_slots.get("name"),
        "email": lead_slots.get("email"),
        "phone": lead_slots.get("phone"),
        "updatedAt": datetime.now(timezone.utc),
    }
    result = await _leads().update_one(
        key, {"$set": doc, "$setOnInsert": {"createdAt": datetime.now(timezone.utc)}}, upsert=True
    )
    return str(result.upserted_id) if result.upserted_id else "updated"


async def save_appointment(
    org_id: str,
    branch_id: str,
    session_id: str,
    calendar_event_id: str,
    service: str,
    start_iso: str,
    attendee_email: Optional[str],
) -> str:
    doc = {
        "orgId": org_id,
        "branchId": branch_id,
        "sessionId": session_id,
        "calendarEventId": calendar_event_id,
        "service": service,
        "startTime": start_iso,
        "attendeeEmail": attendee_email,
        "status": "confirmed",
        "createdAt": datetime.now(timezone.utc),
    }
    result = await _appointments().insert_one(doc)
    return str(result.inserted_id)


async def find_appointment_by_event_id(org_id: str, branch_id: str, calendar_event_id: str) -> Optional[dict]:
    return await _appointments().find_one(
        {"orgId": org_id, "branchId": branch_id, "calendarEventId": calendar_event_id}
    )


async def update_appointment_status(org_id: str, branch_id: str, calendar_event_id: str, status: str) -> None:
    await _appointments().update_one(
        {"orgId": org_id, "branchId": branch_id, "calendarEventId": calendar_event_id},
        {"$set": {"status": status, "updatedAt": datetime.now(timezone.utc)}},
    )
    
if __name__ == "__main__":
    import asyncio

    async def main():
        org_id = "org-001"
        branch_id = "branch-001"
        session_id = "session-123"

        print("=== Testing Lead Upsert ===")

        lead_slots = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "products": ["Dental Cleaning", "Whitening"],
            "reason": "Routine checkup",
            "budget": "$100-$200",
        }

        result = await upsert_lead(
            org_id=org_id,
            branch_id=branch_id,
            session_id=session_id,
            lead_slots=lead_slots,
        )

        print("Lead result:", result)

        print("\n=== Testing Appointment Save ===")

        appointment_id = await save_appointment(
            org_id=org_id,
            branch_id=branch_id,
            session_id=session_id,
            calendar_event_id="event-001",
            service="Dental Cleaning",
            start_iso="2026-07-08T15:00:00Z",
            attendee_email="john@example.com",
        )

        print("Appointment ID:", appointment_id)

        print("\n=== Finding Appointment ===")

        appointment = await find_appointment_by_event_id(
            org_id=org_id,
            branch_id=branch_id,
            calendar_event_id="event-001",
        )

        print(appointment)

        print("\n=== Updating Appointment Status ===")

        await update_appointment_status(
            org_id=org_id,
            branch_id=branch_id,
            calendar_event_id="event-001",
            status="cancelled",
        )

        updated = await find_appointment_by_event_id(
            org_id=org_id,
            branch_id=branch_id,
            calendar_event_id="event-001",
        )

        print(updated)

    asyncio.run(main())
