from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.routes.chat.compiled_graph")
@patch("app.routes.chat.get_tenant")
def test_chat(mock_tenant, mock_graph):
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "final_response": "Hello!",
            "intent": "info",
            "lead_complete": False,
            "booking_confirmed": False,
            "messages": [],
        }
    )

    response = client.post(
        "/chat",
        json={
            "orgId": "org1",
            "branchId": "branch_a",
            "sessionId": "123",
            "message": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Hello!"