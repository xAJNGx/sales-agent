"""
Async wrapper around Ollama OpenAI-compatible API.
"""



import json

from openai import AsyncOpenAI

from app.core.config import settings


_openai_client : AsyncOpenAI | None = None
_ollama_client : AsyncOpenAI | None = None


def _get_client_ollama() -> AsyncOpenAI:
    global _ollama_client

    if _ollama_client is None:
        _ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=settings.ollama_base_url,
        )

    return _ollama_client

def _get_client() -> AsyncOpenAI:
    global _openai_client

    if _openai_client is None:
        _openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

    return _openai_client


async def chat_json(system_prompt: str, user_content: str) -> dict:
    """Force JSON output."""

    client = _get_client()

    resp = await client.chat.completions.create(
        # model="qwen3.5:4b", #uncomment for ollama 
        model=settings.openai_model,
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
        # extra_body={
        #     "think": False
        # }
    )
    content = resp.choices[0].message.content
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
        # model="qwen3.5:4b", #uncomment for ollama 
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *messages,
        ],
        temperature=0.4,
        # extra_body={
        #     "think": False
        # }
    )
    return resp.choices[0].message.content

async def embed_text(text: str) -> list[float]:

    client = _get_client_ollama()

    resp = await client.embeddings.create(
        model="nomic-embed-text",
        input=text,
    )

    return resp.data[0].embedding

if __name__ == "__main__":
    import asyncio
    from datetime import date

    async def main():

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