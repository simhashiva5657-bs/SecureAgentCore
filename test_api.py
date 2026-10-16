import os

os.environ["SECURE_AGENT_API_KEY"] = "test-api-key"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# 1. Health endpoint
def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# 2. Reject missing API key
def test_chat_rejects_missing_api_key():
    response = client.post(
        "/chat",
        json={"message": "Check laptop stock"},
    )

    assert response.status_code == 401


# 3. Reject invalid API key
def test_chat_rejects_invalid_api_key():
    response = client.post(
        "/chat",
        headers={"X-API-Key": "wrong-key"},
        json={"message": "Check laptop stock"},
    )

    assert response.status_code == 401


# 4. Employee can check inventory
def test_employee_role_has_inventory_access():
    response = client.post(
        "/chat",
        headers={"X-API-Key": "employee-dev-key"},
        json={"message": "Check laptop stock"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "employee"
    assert "10" in response.json()["response"]


# 5. HR can look up employees
def test_hr_role_has_employee_lookup_access():
    response = client.post(
        "/chat",
        headers={"X-API-Key": "hr-dev-key"},
        json={"message": "Look up employee EMP001"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "hr"
    assert "Arun" in response.json()["response"]


# 6. Admin can use both tools
def test_admin_role_can_use_both_tools():
    response = client.post(
        "/chat",
        headers={"X-API-Key": "test-api-key"},
        json={
            "message": (
                "Check laptop stock and look up "
                "employee EMP001."
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


# 7. Reject an unknown role
def test_invalid_role_is_rejected():
    from app.security import USERS

    USERS["test-unknown-role-key"] = "unknown"

    try:
        response = client.post(
            "/chat",
            headers={
                "X-API-Key": "test-unknown-role-key"
            },
            json={"message": "Check laptop stock"},
        )

        assert response.status_code == 403

    finally:
        USERS.pop("test-unknown-role-key", None)


# 8. Admin can view audit logs
def test_admin_can_view_audit_logs():
    response = client.get(
        "/admin/audit",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 200
    assert "events" in response.json()
    assert "count" in response.json()


# 9. Reject missing admin key
def test_audit_logs_reject_missing_key():
    response = client.get("/admin/audit")

    assert response.status_code == 401


# 10. Reject employee key for audit logs
def test_audit_logs_reject_employee_key():
    response = client.get(
        "/admin/audit",
        headers={"X-API-Key": "employee-dev-key"},
    )

    assert response.status_code == 401


# 11. Audit endpoint respects requested limit
def test_audit_logs_respects_limit():
    response = client.get(
        "/admin/audit?limit=2",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 200
    assert response.json()["count"] <= 2
    assert len(response.json()["events"]) <= 2


# 12. Reject zero limit
def test_audit_logs_rejects_zero_limit():
    response = client.get(
        "/admin/audit?limit=0",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 422


# 13. Reject limit above 100
def test_audit_logs_rejects_limit_above_100():
    response = client.get(
        "/admin/audit?limit=101",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 422
# 14. Every response includes a request ID
def test_response_includes_request_id():
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


# 15. Server generates its own request ID
def test_request_id_is_generated_by_server():
    response = client.get(
        "/health",
        headers={"X-Request-ID": "client-chosen-id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "client-chosen-id"
