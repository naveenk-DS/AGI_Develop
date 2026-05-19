import httpx
import pytest
import psycopg2

# Your actual settings
BASE     = "http://127.0.0.1:8001"   # FastAPI port
PG_HOST  = "127.0.0.1"
PG_PORT  = 5433                       # pgAdmin PostgreSQL port
PG_DB    = "AGI_Start"
PG_USER  = "postgres"
PG_PASS  = "Naveen@677"


def test_api_health():
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("✅ FastAPI health OK")


def test_ollama_reachable():
    r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=10)
    assert r.status_code == 200
    print("✅ Ollama reachable")


def test_ollama_chat():
    r = httpx.post("http://127.0.0.1:11434/api/chat", json={
        "model": "llama3",
        "messages": [{"role": "user", "content": "Reply only: WORKING"}],
        "stream": False
    }, timeout=120)
    assert r.status_code == 200
    print("✅ Ollama chat OK:", r.json()["message"]["content"][:30])


def test_postgres():
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    conn.close()
    print("✅ PostgreSQL OK")


def test_qdrant():
    r = httpx.get("http://127.0.0.1:6333/healthz")
    assert r.status_code == 200
    print("✅ Qdrant OK")


def test_n8n():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(("127.0.0.1", 5678))
    s.close()
    assert result == 0, "n8n port 5678 is not open"
    print("✅ n8n port open OK")


def test_api_chat():
    r = httpx.post(f"{BASE}/chat",
        json={"message": "say hi"}, timeout=120)
    assert r.status_code == 200
    assert "reply" in r.json()
    print("✅ /chat endpoint OK")
