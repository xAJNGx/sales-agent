from pydantic import BaseModel

class ChatRequest(BaseModel):
    orgId: str
    branchId: str
    sessionId: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    leadComplete: bool
    bookingConfirmed: bool
