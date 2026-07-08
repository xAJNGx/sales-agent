"""
Shared state that flows through every LangGraph node.

Tenancy (org_id/branch_id) lives here so it's threaded automatically into
every node/tool call instead of being re-derived or passed around manually.
"""
from typing import Literal, Optional, TypedDict

Intent = Literal["info", "purchase", "booking", "reschedule", "cancel", "chitchat"]


class LeadSlots(TypedDict, total=False):
    products: list[str]
    reason: Optional[str]
    budget: Optional[str]
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]


class BookingSlots(TypedDict, total=False):
    service: Optional[str]
    date: Optional[str]                # ISO date, resolved from natural language
    time: Optional[str]                # ISO time
    duration_minutes: int
    existing_event_id: Optional[str]   # set when rescheduling/cancelling


class AgentState(TypedDict, total=False):
    # tenancy — set once per request, never mutated downstream
    org_id: str
    branch_id: str
    session_id: str

    # conversation
    messages: list[dict]        # [{"role": "user"|"assistant", "content": str}, ...]
    user_message: str           # latest turn, convenience field
    intent: Intent

    # RAG
    retrieved_chunks: list[dict]
    rag_answer: Optional[str]

    # lead capture
    lead_slots: LeadSlots
    lead_complete: bool
    lead_saved: bool

    # booking
    booking_slots: BookingSlots
    booking_confirmed: bool
    calendar_event_id: Optional[str]

    # output
    final_response: str
    notify_email: bool
