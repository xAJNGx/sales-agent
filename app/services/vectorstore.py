"""
Multi-tenant retrieval over a single Pinecone index (async client).

Isolation is enforced two ways so a bug in one layer can't leak data across
tenants:
  1. Pinecone `namespace` — a query in namespace A structurally cannot
     return vectors stored in namespace B.
  2. Metadata `filter` on orgId/branchId — belt-and-braces, and lets us
     later merge namespaces without losing isolation.
"""
from __future__ import annotations

from pinecone import PineconeAsyncio

from app.core.config import TenantConfig, settings
from app.utils.llm import embed_text

_pc: PineconeAsyncio | None = None
_index_host: str | None = None


async def _get_client() -> PineconeAsyncio:
    global _pc
    if _pc is None:
        if not settings.pinecone_api_key:
            raise RuntimeError("PINECONE_API_KEY is not set. Add it to .env to enable retrieval.")
        _pc = PineconeAsyncio(api_key=settings.pinecone_api_key)
    return _pc


async def _get_index_host() -> str:
    global _index_host
    if _index_host is None:
        pc = await _get_client()
        desc = await pc.describe_index(name=settings.pinecone_index_name)
        _index_host = desc.host
    return _index_host


async def query_knowledge_base(tenant: TenantConfig, query: str, top_k: int = 5) -> list[dict]:
    """Return the top_k most relevant chunks scoped strictly to this tenant."""
    pc = await _get_client()
    host = await _get_index_host()
    vector = await embed_text(query)

    async with pc.IndexAsyncio(host=host) as idx:
        result = await idx.query(
            vector=vector,
            top_k=top_k,
            namespace=tenant.pinecone_namespace,           # (1) namespace isolation
            filter={                                        # (2) metadata isolation
                "orgId": {"$eq": tenant.org_id},
                "branchId": {"$eq": tenant.branch_id},
            },
            include_metadata=True,
        )

    return [
        {
            "text": match["metadata"].get("text", ""),
            "source": match["metadata"].get("source", "unknown"),
            "score": match["score"],
        }
        for match in result.get("matches", [])
    ]


async def upsert_document(tenant: TenantConfig, doc_id: str, text: str, source: str = "manual") -> None:
    """Ingest a document chunk into this tenant's namespace (offline ingestion job)."""
    pc = await _get_client()
    host = await _get_index_host()
    vector = await embed_text(text)

    async with pc.IndexAsyncio(host=host) as idx:
        await idx.upsert(
            vectors=[
                {
                    "id": doc_id,
                    "values": vector,
                    "metadata": {
                        "text": text,
                        "source": source,
                        "orgId": tenant.org_id,
                        "branchId": tenant.branch_id,
                    },
                }
            ],
            namespace=tenant.pinecone_namespace,
        )


if __name__ == "__main__":
    import asyncio

    async def main():
        # Replace these with values from your application
        tenant = TenantConfig(
            org_id="test",
            branch_id="test",
            display_name="Demo Clinic",
            pinecone_namespace="test",
            google_calendar_id="test",
            from_email="noreply@anujnandagorkhali.com.np",
        )

        print("Upserting test document...")
        await upsert_document(
            tenant=tenant,
            doc_id="test-doc-1",
            text="Pinecone is a vector database used for semantic search.",
            source="test",
        )

        print("Querying knowledge base...")
        results = await query_knowledge_base(
            tenant=tenant,
            query="What is Pinecone?",
            top_k=3,
        )

        print("\nResults:")
        for i, result in enumerate(results, start=1):
            print(f"\nResult {i}")
            print(f"Score : {result['score']:.4f}")
            print(f"Source: {result['source']}")
            print(f"Text  : {result['text']}")

    asyncio.run(main())