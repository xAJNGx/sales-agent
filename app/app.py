"""
FastAPI entrypoint for the multi-tenant conversational sales agent.
"""
from fastapi import FastAPI

from app.routes import chat, health

app = FastAPI(title="Multi-Tenant Sales Agent")

app.include_router(chat.router)
app.include_router(health.router)
