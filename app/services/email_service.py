"""
Sends booking confirmation / reschedule / cancellation emails via async SMTP
"""


from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import TenantConfig, settings


async def _send(to_email: str, from_email: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is not set. Add SMTP credentials to .env to send email.")

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        start_tls=True,
    )


async def send_booking_confirmation(tenant: TenantConfig, to_email: str, service: str, start_iso: str) -> None:
    subject = f"Confirmed: {service} at {tenant.display_name}"
    body = (
        f"Hi,\n\nYour appointment for \"{service}\" at {tenant.display_name} "
        f"is confirmed for {start_iso}.\n\n"
        "If you need to reschedule or cancel, just reply to this email or "
        f"tell our assistant.\n\nSee you then!\n{tenant.display_name}"
    )
    await _send(to_email, tenant.from_email, subject, body)


async def send_reschedule_confirmation(tenant: TenantConfig, to_email: str, service: str, new_start_iso: str) -> None:
    subject = f"Rescheduled: {service} at {tenant.display_name}"
    body = (
        f"Hi,\n\nYour appointment for \"{service}\" at {tenant.display_name} "
        f"has been moved to {new_start_iso}.\n\n{tenant.display_name}"
    )
    await _send(to_email, tenant.from_email, subject, body)


async def send_cancellation_confirmation(tenant: TenantConfig, to_email: str, service: str) -> None:
    subject = f"Cancelled: {service} at {tenant.display_name}"
    body = (
        f"Hi,\n\nYour appointment for \"{service}\" at {tenant.display_name} "
        "has been cancelled. Let us know if you'd like to rebook.\n\n"
        f"{tenant.display_name}"
    )
    await _send(to_email, tenant.from_email, subject, body)


if __name__=="__main__":
    import asyncio

    from app.core.config import TenantConfig

    tenant = TenantConfig(
        org_id="test",
        branch_id="test",
        display_name="Demo Clinic",
        pinecone_namespace="test",
        google_calendar_id="test",
        from_email="noreply@anujnandagorkhali.com.np",
    )

    async def main():
        await send_booking_confirmation(
            tenant=tenant,
            to_email="ajngworks@gmail.com",
            service="Dental Consultation",
            start_iso="2026-07-10 15:00",
        )

    asyncio.run(main())