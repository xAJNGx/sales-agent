"""
Async wrapper around Ollama OpenAI-compatible API.
"""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.core.config import settings


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client

    if _client is None:
        _client = AsyncOpenAI(
            api_key="ollama",
            base_url=settings.ollama_base_url,
        )

    return _client


async def chat_json(system_prompt: str, user_content: str) -> dict:
    """Force JSON output."""

    client = _get_client()

    resp = await client.chat.completions.create(
        model="qwen3.5:4b",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        response_format={
            "type": "json_object"
        },
        temperature=0,
        extra_body={
            "think": False
        }
    )

    return json.loads(
        resp.choices[0].message.content
    )


async def chat_text(system_prompt: str, messages: list[dict]) -> str:
    """Normal conversation."""

    client = _get_client()

    resp = await client.chat.completions.create(
        model="qwen3.5:4b",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *messages,
        ],
        temperature=0.4,
        extra_body={
            "think": False
        }
    )

    return resp.choices[0].message.content

async def embed_text(text: str) -> list[float]:

    client = _get_client()

    resp = await client.embeddings.create(
        model="nomic-embed-text",
        input=text,
    )

    return resp.data[0].embedding

if __name__ == "__main__":
    import asyncio


    async def main():
        print("=" * 50)
        print("Testing Ollama Chat Text")
        print("=" * 50)

        response = await chat_text(
            system_prompt="You are a helpful AI assistant.",
            messages=[
                {
                    "role": "user",
                    "content": "Explain RAG in 3 sentences."
                }
            ],
        )

        print(response)

        json_response = await chat_json(
            system_prompt="""
            Extract information from the user message.
            Return JSON with:
            {
                "name": string,
                "product": string,
                "intent": string
            }
            """,
            user_content="""
            My name is Anuj.
            I want to buy a laptop for AI development.
            """,
        )

        print(json.dumps(json_response, indent=2))

        embedding = await embed_text(
            "Retrieval augmented generation combines search with LLMs."
        )

        print("Embedding dimension:", len(embedding))
        print("First 10 values:", embedding[:10])


    asyncio.run(main())