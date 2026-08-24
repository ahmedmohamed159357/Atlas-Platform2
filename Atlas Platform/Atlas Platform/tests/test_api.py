import pytest
import json
from app.core.red_cipher import RedCipher
from datetime import datetime

@pytest.mark.integration
def test_api_status(test_client):
    """Verify the /api/status endpoint."""
    response = test_client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "ONLINE"
    assert "hive_mind" in data

@pytest.mark.integration
def test_api_hive_checkin_flow(test_client):
    """Verify the full check-in flow with the server's actual cipher."""
    from app.main import cipher_engine
    
    # 2. Prepare Payload
    agent_id = "test_agent_full_flow"
    payload_data = {
        "agent_id": agent_id,
        "info": {"os": "TestOS", "user": "testuser"}
    }
    encrypted_data = cipher_engine.encrypt(json.dumps(payload_data))
    
    # 3. Request
    response = test_client.post("/api/hive/checkin", json={
        "agent_id": agent_id,
        "data": encrypted_data
    })
    assert response.status_code == 200
    
    # 4. Decrypt Response
    resp_json = response.json()
    assert "data" in resp_json
    decrypted_resp = json.loads(cipher_engine.decrypt(resp_json["data"]))
    assert "jitter" in decrypted_resp
    assert "commands" in decrypted_resp

@pytest.mark.integration
async def test_api_consult_mocked(test_client, monkeypatch):
    """Verify the /api/consult endpoint with a mocked hive mind."""
    async def mock_advice(query: str):
        return "Mocked Advice"
    
    monkeypatch.setattr("app.main.hive_mind.get_strategic_advice", mock_advice)
    
    response = test_client.post("/api/consult", json={"query": "How to hack?"})
    assert response.status_code == 200
    assert response.json()["response"] == "Mocked Advice"


@pytest.mark.integration
def test_storage_lifecycle(test_client):
    """Verify the generic storage key/value API persists and deletes data."""
    key = "phase14_temp_store"
    payload = {"value": {"status": "ok", "count": 2}}

    create_response = test_client.post(f"/api/storage/{key}", json=payload)
    assert create_response.status_code == 200
    assert create_response.json()["value"] == payload["value"]

    get_response = test_client.get(f"/api/storage/{key}")
    assert get_response.status_code == 200
    assert get_response.json()["value"] == payload["value"]

    delete_response = test_client.delete(f"/api/storage/{key}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_response = test_client.get(f"/api/storage/{key}")
    assert missing_response.status_code == 404


@pytest.mark.integration
def test_investigation_lifecycle(test_client):
    """Verify investigation list/create/update/delete routes work with the frontend contract."""
    payload = {"title": "Phase 14 Test Investigation", "status": "open"}

    create_response = test_client.post("/api/investigations", json=payload)
    assert create_response.status_code == 200
    created = create_response.json()["investigation"]
    assert created["title"] == payload["title"]
    investigation_id = created["id"]

    list_response = test_client.get("/api/investigations")
    assert list_response.status_code == 200
    investigations = list_response.json()["investigations"]
    assert any(item["id"] == investigation_id for item in investigations)

    update_response = test_client.put(f"/api/investigations/{investigation_id}", json={"status": "in-progress"})
    assert update_response.status_code == 200
    assert update_response.json()["investigation"]["status"] == "in-progress"

    timeline_response = test_client.get(f"/api/investigations/{investigation_id}/timeline")
    assert timeline_response.status_code == 200

    evidence_response = test_client.get(f"/api/investigations/{investigation_id}/evidence")
    assert evidence_response.status_code == 200

    delete_response = test_client.delete(f"/api/investigations/{investigation_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
