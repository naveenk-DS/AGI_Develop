import httpx
import time
import tempfile
import os
from pathlib import Path

BASE    = "http://127.0.0.1:8001"
TIMEOUT = 180
API_KEY = "naveen-agi-webhook-key-2024"

def test_01_all_services_healthy():
    endpoints = [
        "/health",
        "/dashboard/stats",
        "/agent/tools",
        "/backup/list",
        "/license/status",
        "/templates/list",
        "/sessions/list",
        "/sessions/stats",
        "/analytics/overview",
        "/analytics/tools",
        "/analytics/version",
        "/settings/all",
    ]
    failed = []
    for ep in endpoints:
        r = httpx.get(f"{BASE}{ep}", timeout=15)
        if r.status_code != 200:
            failed.append(ep)

    assert not failed, f"Failed endpoints: {failed}"
    print(f"All {len(endpoints)} endpoints healthy")

def test_02_rag_full_pipeline():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write("AGI_Start is a local AI product built by Naveen using Python FastAPI Ollama and Qdrant running on Windows.")
        tmp = f.name

    r = httpx.post(f"{BASE}/rag/ingest-path", json={
        "file_path": tmp.replace("\\", "/"),
        "doc_name": "system-test-doc"
    }, timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.json()["chunks_stored"] >= 1
    os.unlink(tmp)

    r2 = httpx.post(f"{BASE}/rag/query", json={
        "question": "what is AGI_Start built with?"
    }, timeout=TIMEOUT)
    assert r2.status_code == 200
    assert "answer" in r2.json()
    print("RAG pipeline OK:", r2.json()["answer"][:60])

def test_03_chat_with_memory():
    session = "system-test-memory"
    r1 = httpx.post(f"{BASE}/chat/message", json={
        "session_id": session,
        "message": "my name is Naveen and I build AI products"
    }, timeout=TIMEOUT)
    assert r1.status_code == 200

    r2 = httpx.post(f"{BASE}/chat/message", json={
        "session_id": session,
        "message": "what is my name?"
    }, timeout=TIMEOUT)
    assert r2.status_code == 200
    assert "Naveen" in r2.json()["reply"]
    print("Memory OK:", r2.json()["reply"][:60])

def test_04_agent_tool_selection():
    tests = [
        ("what is 2 plus 2?", ["direct_chat"]),
        ("summarise everything you know", ["summarise", "direct_chat"]),
    ]
    for message, expected_tools in tests:
        r = httpx.post(f"{BASE}/agent/run", json={
            "session_id": "system-test-agent",
            "message": message
        }, timeout=TIMEOUT)
        assert r.status_code == 200
        assert "tool_used" in r.json()
        print(f"Agent OK — tool: {r.json()['tool_used']} for: {message[:30]}")

def test_05_streaming():
    r = httpx.post(f"{BASE}/stream/chat", json={
        "session_id": "system-test-stream",
        "message": "say hello in one word"
    }, timeout=TIMEOUT)
    assert r.status_code == 200
    assert len(r.text) > 0
    print("Streaming OK:", r.text[:40])

def test_06_template_system():
    r = httpx.post(f"{BASE}/templates/create", json={
        "name": "system_test_template",
        "description": "System test",
        "system": "You are a test bot. Always reply: SYSTEM TEST OK",
        "model": "llama3"
    })
    assert r.status_code == 200

    r2 = httpx.post(f"{BASE}/templates/run", json={
        "template_name": "system_test_template",
        "message": "hello",
        "session_id": "system-test-template"
    }, timeout=TIMEOUT)
    assert r2.status_code == 200
    assert "reply" in r2.json()

    httpx.delete(f"{BASE}/templates/delete/system_test_template")
    print("Template system OK:", r2.json()["reply"][:40])

def test_07_session_management():
    session = "system-test-session-mgmt"
    httpx.post(f"{BASE}/chat/message", json={
        "session_id": session,
        "message": "test message"
    }, timeout=TIMEOUT)

    r = httpx.get(f"{BASE}/sessions/get/{session}")
    assert r.status_code == 200
    assert r.json()["message_count"] >= 1

    httpx.delete(f"{BASE}/sessions/delete/{session}")

    r2 = httpx.get(f"{BASE}/sessions/get/{session}")
    assert r2.json().get("error") == "Session not found"
    print("Session management OK")

def test_08_encrypted_config():
    r = httpx.post(f"{BASE}/configs/set", json={
        "customer_id": "system-test",
        "key": "system-config",
        "value": {"test": True, "version": "0.3.0"}
    })
    assert r.status_code == 200

    r2 = httpx.get(f"{BASE}/configs/get/system-test/system-config")
    assert r2.status_code == 200
    assert r2.json()["value"]["version"] == "0.3.0"
    print("Encrypted config OK")

def test_09_analytics():
    endpoints = [
        "/analytics/overview",
        "/analytics/tools",
        "/analytics/daily?days=7",
        "/analytics/top-sessions?limit=5",
        "/analytics/response-times",
        "/analytics/version",
        "/analytics/rate-limits",
    ]
    for ep in endpoints:
        r = httpx.get(f"{BASE}{ep}", timeout=15)
        assert r.status_code == 200, f"Failed: {ep}"
    print("Analytics OK — all endpoints responding")

def test_10_backup():
    r = httpx.post(f"{BASE}/backup/run-now", timeout=120)
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    r2 = httpx.get(f"{BASE}/backup/list")
    assert r2.json()["count"] >= 1
    print("Backup OK:", r2.json()["count"], "backups")

def test_11_webhook_auth():
    r_no_key = httpx.get(f"{BASE}/webhook/test")
    assert r_no_key.status_code == 401

    r_with_key = httpx.get(
        f"{BASE}/webhook/test",
        headers={"X-API-Key": API_KEY}
    )
    assert r_with_key.status_code == 200
    print("Webhook auth OK")

def test_12_settings():
    r = httpx.get(f"{BASE}/settings/all")
    assert r.status_code == 200
    assert "default_model" in r.json()["settings"]

    r2 = httpx.post(f"{BASE}/settings/update", json={
        "key": "default_model",
        "value": "llama3"
    })
    assert r2.status_code == 200
    print("Settings OK:", r.json()["settings"]["default_model"])

def test_13_error_handling():
    r = httpx.post(f"{BASE}/chat/message", json={"wrong": "data"})
    assert r.status_code == 422
    assert "error" in r.json()

    r2 = httpx.get(f"{BASE}/this-endpoint-does-not-exist")
    assert r2.status_code == 404
    assert "error" in r2.json()
    print("Error handling OK")