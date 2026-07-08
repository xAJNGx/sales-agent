"""
Google Calendar integration, scoped per org/branch calendar.

Assumes a service account 
granted "Make changes to events" access on each branch's calendar. The
calendar to write to is resolved entirely from `tenant.google_calendar_id` —
never guessed or defaulted — so a booking can never land on the wrong
branch's calendar.
"""


import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import TenantConfig, settings

_service = None

def _build_service():
    global _service
    if _service is None:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            settings.google_service_account_json,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        _service = build("calendar", "v3", credentials=creds)
    return _service


def _check_availability_sync(calendar_id: str, start_iso: str, end_iso: str) -> bool:
    service = _build_service()
    body = {"timeMin": start_iso, "timeMax": end_iso, "items": [{"id": calendar_id}]}
    print(body)
    result = service.freebusy().query(body=body).execute()
    return len(result["calendars"][calendar_id]["busy"]) == 0


def _create_event_sync(
    calendar_id: str, summary: str, start_iso: str, duration_minutes: int, description: str,
) -> str:
    service = _build_service()
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()},
        "reminders": {"useDefault": True},
    }
    created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    return created["id"]


def _reschedule_event_sync(calendar_id: str, event_id: str, new_start_iso: str, duration_minutes: int) -> None:
    service = _build_service()
    start_dt = datetime.fromisoformat(new_start_iso)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    service.events().patch(
        calendarId=calendar_id,
        eventId=event_id,
        body={"start": {"dateTime": start_dt.isoformat()}, "end": {"dateTime": end_dt.isoformat()}},
        sendUpdates="all",
    ).execute()


def _cancel_event_sync(calendar_id: str, event_id: str) -> None:
    service = _build_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()


async def check_availability(tenant: TenantConfig, start_iso: str, end_iso: str) -> bool:
    return await asyncio.to_thread(_check_availability_sync, tenant.google_calendar_id, start_iso, end_iso)


async def create_event(
    tenant: TenantConfig, summary: str, start_iso: str, duration_minutes: int,
    attendee_email: Optional[str], description: str = "",
) -> str:
    return await asyncio.to_thread(
        _create_event_sync, tenant.google_calendar_id, summary, start_iso,
        duration_minutes, description,
    )


async def reschedule_event(tenant: TenantConfig, event_id: str, new_start_iso: str, duration_minutes: int) -> None:
    await asyncio.to_thread(_reschedule_event_sync, tenant.google_calendar_id, event_id, new_start_iso, duration_minutes)


async def cancel_event(tenant: TenantConfig, event_id: str) -> None:
    await asyncio.to_thread(_cancel_event_sync, tenant.google_calendar_id, event_id)


if __name__=="__main__":
    import asyncio

    from app.core.config import TenantConfig

    async def main():
        tenant =  TenantConfig(
            org_id="org_1",
            branch_id="branch_a",
            display_name="AJNG Corp — KTM Branch",
            pinecone_namespace="org_1__branch_a",
            google_calendar_id="206a991a8081eb369e5cc6e8921b4a212a4667fd538828c0cf4e9d1a2ac04077@group.calendar.google.com",
            from_email="noreply@anujnandagorkhali.com.np",
        )

        start = "2026-07-09T10:00:00+05:45"
        end = "2026-07-09T10:30:00+05:45"

        # Check availability
        available = await check_availability(
            tenant=tenant,
            start_iso=start,
            end_iso=end,
        )

        print(f"Available: {available}")

        if not available:
            print("Time slot is busy.")
            return

        # # Create event
        # event_id = await create_event(
        #     tenant=tenant,
        #     summary="Test Appointment",
        #     start_iso=start,
        #     duration_minutes=30,
        #     attendee_email="test@example.com",  # Optional
        #     description="Created from Python",
        # )

        # print(f"Created event: {event_id}")

        # # Reschedule
        # await reschedule_event(
        #     tenant=tenant,
        #     event_id=event_id,
        #     new_start_iso="2026-07-09T11:00:00+05:45",
        #     duration_minutes=30,
        # )

        # print("Event rescheduled.")

        # delete the event
        # await cancel_event(
        #     tenant=tenant,
        #     event_id=event_id,
        # )
        # print("Event cancelled.")
    asyncio.run(main())