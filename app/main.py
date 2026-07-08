"""
FastAPI entrypoint for the multi-tenant conversational sales agent.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat, health

app = FastAPI(title="Multi-Tenant Sales Agent")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app)