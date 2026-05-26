import httpx
import time
import tempfile
import os
from pathlib import Path

BASE = "http://127.0.0.1:8001"
TIMEOUT = 180

def test_full_rag_pipeline():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write("Naveen is building an AGI product using Python, FastAPI, Ollama and Qdrant.")
        tmp = f.name

    r = httpx.post(f"{BASE}/rag/ingest-path", json={
        "file_path": tmp.replace("\\", "/"),
        "doc_name": "integration-test-doc"
    }, timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.json()["chunks_stored"] >= 1
    os.unlink(tmp)

    r = httpx.post(f"{BASE}/rag/query", json={
        "question": "what is Naveen building?"
    }, timeout=TIMEOUT)
    assert r.status_code == 200
    assert "answer" in r.json()
    print("RAG pipeline OK:", r.json()["answer"][:60])

def test_full_agent_pipeline():
    session = "integration-agent-001"

    r1 = httpx.post(f"{BASE}/agent/run", json={
        "session_id": session,
        "message": "my project is called AGI_Start"
    }, timeout=TIMEOUT)
    assert r1.status_code == 200
    assert "tool_used" in r1.json()

    r2 = httpx.post(f"{BASE}/agent/run", json={
        "session_id": session,
        "message": "what is my project called?"
    }, timeout=TIMEOUT)
    assert r2.status_code == 200
    assert "AGI" in r2.json()["answer"] or "Start" in r2.json()["answer"]
    print("Agent pipeline OK:", r2.json()["answer"][:60])

def test_full_backup_pipeline():
    r = httpx.post(f"{BASE}/backup/run-now", timeout=300)
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    r2 = httpx.get(f"{BASE}/backup/list", timeout=30)
    assert r2.status_code == 200
    assert r2.json()["count"] >= 1
    print("Backup pipeline OK:", r2.json()["count"], "backups")

def test_full_config_pipeline():
    r = httpx.post(f"{BASE}/configs/set", json={
        "customer_id": "integration-test",
        "key": "test-config",
        "value": {"key": "value", "number": 42}
    }, timeout=30)
    assert r.status_code == 200

    r2 = httpx.get(f"{BASE}/configs/get/integration-test/test-config", timeout=30)
    assert r2.status_code == 200
    assert r2.json()["value"]["number"] == 42
    print("Config pipeline OK")

def test_all_endpoints_healthy():
    endpoints = [
        "/health",
        "/dashboard/stats",
        "/agent/tools",
        "/backup/list",
        "/license/status",
        "/chat/history/test",
    ]
    for ep in endpoints:
        r = httpx.get(f"{BASE}{ep}", timeout=30)
        assert r.status_code == 200, f"FAILED: {ep}"
    print("All endpoints healthy")