from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import TenantConfig
from app.services.vectorstore import query_knowledge_base


@pytest.mark.asyncio
@patch("app.services.vectorstore.embed_text", new_callable=AsyncMock)
@patch("app.services.vectorstore._get_index_host", new_callable=AsyncMock)
@patch("app.services.vectorstore._get_client", new_callable=AsyncMock)
async def test_query_knowledge_base(
    mock_client,
    mock_host,
    mock_embed,
):
    tenant = TenantConfig(
        org_id="org1",
        branch_id="branch1",
        display_name="Demo",
        pinecone_namespace="demo",
        google_calendar_id="calendar",
        from_email="demo@test.com",
    )

    mock_embed.return_value = [0.1, 0.2]
    mock_host.return_value = "fake-host"

    fake_index = AsyncMock()
    fake_index.query.return_value = {
        "matches": [
            {
                "score": 0.95,
                "metadata": {
                    "text": "Pinecone is awesome",
                    "source": "docs",
                },
            }
        ]
    }

    # Mock the async context manager returned by IndexAsyncio()
    cm = AsyncMock()
    cm.__aenter__.return_value = fake_index
    cm.__aexit__.return_value = None

    # Mock the Pinecone client
    fake_client = MagicMock()
    fake_client.IndexAsyncio.return_value = cm

    # _get_client() returns the fake client
    mock_client.return_value = fake_client

    result = await query_knowledge_base(tenant, "What is Pinecone?")

    assert len(result) == 1
    assert result[0]["text"] == "Pinecone is awesome"
    assert result[0]["source"] == "docs"
    assert result[0]["score"] == 0.95

    fake_index.query.assert_awaited_once()