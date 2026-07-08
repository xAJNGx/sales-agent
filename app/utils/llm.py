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
    content = resp.choices[0].message.content
    print(repr(content))
    try:
        return json.loads(content)
    except Exception:
        print("Raw response:")
        print(repr(content))
        raise
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
    print("___"*20)
    print(resp.choices[0].message.content)
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

        # response = await chat_text(
        #     system_prompt="You are a helpful AI assistant.",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": "Explain RAG in 3 sentences."
        #         }
        #     ],
        # )

        # print(response)
        from datetime import date

        system_prompt = f"""
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
        json_response = await chat_json(
            system_prompt=system_prompt,
            user_content="""
           I'd like to book a demo for tomorrow at 3 PM.
            """,
        )

        print(json.dumps(json_response, indent=2))

        embedding = await embed_text(
            "Retrieval augmented generation combines search with LLMs."
        )

        print("Embedding dimension:", len(embedding))
        print("First 10 values:", embedding[:10])


    asyncio.run(main())