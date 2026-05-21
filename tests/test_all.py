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


def test_rag_ingest_and_query():
    # Create a small test document
    content = b"My AI product is built with Python, FastAPI, Ollama, and PostgreSQL. It runs locally on Windows."
    
    # Ingest
    r = httpx.post(
        f"{BASE}/rag/ingest",
        files={"file": ("test.txt", content, "text/plain")},
        timeout=60
    )
    assert r.status_code == 200
    assert r.json()["chunks_stored"] >= 1
    print("RAG ingest OK:", r.json())

    # Query
    r = httpx.post(
        f"{BASE}/rag/query",
        json={"question": "what language is this product built with?"},
        timeout=60
    )
    assert r.status_code == 200
    assert "answer" in r.json()
    print("RAG query OK:", r.json()["answer"][:80])


def test_chat_with_memory():
    session = "pytest-session-day3"

    # first message
    r1 = httpx.post(f"{BASE}/chat/message", json={
        "session_id": session,
        "message": "My name is Naveen. Remember this."
    }, timeout=60)
    assert r1.status_code == 200
    assert "reply" in r1.json()
    print("Turn 1:", r1.json()["reply"][:60])

    # second message — should remember name
    r2 = httpx.post(f"{BASE}/chat/message", json={
        "session_id": session,
        "message": "What is my name?"
    }, timeout=60)
    assert r2.status_code == 200
    assert "Naveen" in r2.json()["reply"]
    print("Turn 2:", r2.json()["reply"][:60])

    # check history saved in postgres
    r3 = httpx.get(f"{BASE}/chat/history/{session}")
    assert r3.status_code == 200
    assert r3.json()["count"] >= 4  # 2 user + 2 assistant
    print("History count:", r3.json()["count"])

def test_clear_history():
    session = "pytest-clear-test"
    httpx.post(f"{BASE}/chat/message", json={
        "session_id": session,
        "message": "hello"
    }, timeout=60)
    r = httpx.post(f"{BASE}/chat/clear", json={"session_id": session})
    assert r.status_code == 200
    history = httpx.get(f"{BASE}/chat/history/{session}")
    assert history.json()["count"] == 0
    print("Clear history: OK")


def test_daily_summary():
    r = httpx.post("http://127.0.0.1:8001/summary/daily", timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "stats" in data
    print("Summary:", data["summary"][:80])

def test_ingest_path():
    import tempfile, os
    # create a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write("This is a test document about Python and AI automation.")
        tmp_path = f.name

    r = httpx.post("http://127.0.0.1:8001/rag/ingest-path", json={
        "file_path": tmp_path,
        "doc_name": "temp-test-doc"
    }, timeout=60)
    assert r.status_code == 200
    assert r.json()["chunks_stored"] >= 1
    print("Ingest path OK:", r.json())
    os.unlink(tmp_path)

def test_webhook_via_n8n():
    r = httpx.post("http://127.0.0.1:5678/webhook/ai-chat",
        headers={"Content-Type": "application/json"},
        json={"session_id": "n8n-pytest", "message": "say hello"},
        timeout=60
    )
    assert r.status_code == 200
    assert "reply" in r.json()
    print("n8n webhook OK:", r.json()["reply"][:60])

def test_encrypted_config():
    # save encrypted
    r = httpx.post("http://127.0.0.1:8001/configs/set", json={
        "customer_id": "test-naveen",
        "key": "settings",
        "value": {"model": "llama3", "temp": 0.7}
    })
    assert r.status_code == 200
    assert r.json()["status"] == "saved"

    # read back decrypted
    r = httpx.get("http://127.0.0.1:8001/configs/get/test-naveen/settings")
    assert r.status_code == 200
    assert r.json()["value"]["model"] == "llama3"
    print("Encrypted config OK:", r.json()["value"])

def test_license_create_and_activate():
    # create
    r = httpx.post("http://127.0.0.1:8001/license/create", json={
        "license_key": "PYTEST-LICENSE-DAY5",
        "plan": "starter"
    })
    assert r.status_code == 200

    # activate
    r = httpx.post("http://127.0.0.1:8001/license/activate", json={
        "license_key": "PYTEST-LICENSE-DAY5"
    })
    assert r.status_code == 200
    assert r.json()["valid"] == True
    print("License OK:", r.json()["plan"])

def test_invalid_license():
    r = httpx.post("http://127.0.0.1:8001/license/activate", json={
        "license_key": "FAKE-KEY-000"
    })
    assert r.status_code == 200
    assert r.json()["valid"] == False
    print("Invalid license correctly rejected")


def test_dashboard_loads():
    r = httpx.get("http://127.0.0.1:8001/dashboard/")
    assert r.status_code == 200
    assert "MyAIProduct" in r.text
    print("Dashboard OK")

def test_dashboard_stats():
    r = httpx.get("http://127.0.0.1:8001/dashboard/stats")
    assert r.status_code == 200
    assert "total_events" in r.json()
    print("Dashboard stats OK:", r.json()["total_events"])


import time
from pathlib import Path

def test_file_watcher():
    import uuid
    watch_folder = Path("F:/naveen/AGI_Start/watch")
    test_file_name = f"watcher-test-{uuid.uuid4().hex[:6]}.txt"
    test_file = watch_folder / test_file_name

    # drop a file in watch folder
    test_file.write_text("The file watcher test is working correctly with Python watchdog.")

    # wait for watcher to process it (up to 30 seconds since local Ollama can be slow)
    for _ in range(15):
        time.sleep(2)
        processed = watch_folder / "processed" / test_file_name
        if processed.exists():
            break

    assert processed.exists(), "File was not moved to processed folder (watcher timed out or failed)"
    print("File watcher OK — file moved to processed")

    # verify it was ingested by querying
    r = httpx.post("http://127.0.0.1:8001/rag/query",
        json={"question": "what is working correctly with watchdog?"},
        timeout=60
    )
    assert r.status_code == 200
    print("Watcher RAG query OK:", r.json()["answer"][:60])


def test_csv_ingest():
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                     delete=False, encoding='utf-8') as f:
        f.write("product,price,category\n")
        f.write("Python Book,500,Education\n")
        f.write("AI Course,2000,Technology\n")
        tmp = f.name

    r = httpx.post("http://127.0.0.1:8001/rag/ingest-path", json={
        "file_path": tmp.replace("\\", "/"),
        "doc_name": "test-csv"
    }, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data["chunks_stored"] >= 1
    assert data["file_type"] == ".csv"
    print("CSV ingest OK:", data)
    os.unlink(tmp)

def test_txt_ingest_still_works():
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write("FastAPI is a modern Python web framework for building APIs quickly.")
        tmp = f.name

    r = httpx.post("http://127.0.0.1:8001/rag/ingest-path", json={
        "file_path": tmp.replace("\\", "/"),
        "doc_name": "test-txt-day8"
    }, timeout=60)
    assert r.status_code == 200
    assert r.json()["file_type"] == ".txt"
    print("TXT still works OK")
    os.unlink(tmp)

def test_unsupported_file_rejected():
    r = httpx.post("http://127.0.0.1:8001/rag/ingest-path", json={
        "file_path": "F:/naveen/AGI_Start/app/main.py",
        "doc_name": "python-file"
    }, timeout=30)
    assert r.status_code == 200
    assert "error" in r.json()
    print("Unsupported file correctly rejected:", r.json()["error"])

def test_agent_direct_chat():
    r = httpx.post("http://127.0.0.1:8001/agent/run", json={
        "session_id": "pytest-agent-001",
        "message": "what is 2 plus 2?"
    }, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "tool_used" in data
    print("Agent chat OK — tool:", data["tool_used"])

def test_agent_rag_search():
    r = httpx.post("http://127.0.0.1:8001/agent/run", json={
        "session_id": "pytest-agent-002",
        "message": "what documents have been ingested?"
    }, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    print("Agent RAG OK — tool:", data["tool_used"])

def test_agent_tools_list():
    r = httpx.get("http://127.0.0.1:8001/agent/tools")
    assert r.status_code == 200
    assert "tools" in r.json()
    print("Agent tools:", list(r.json()["tools"].keys()))

def test_agent_remembers_context():
    session = "pytest-agent-memory"
    # first message
    httpx.post("http://127.0.0.1:8001/agent/run", json={
        "session_id": session,
        "message": "my favourite language is Python"
    }, timeout=60)
    # second message — should remember
    r = httpx.post("http://127.0.0.1:8001/agent/run", json={
        "session_id": session,
        "message": "what is my favourite language?"
    }, timeout=60)
    assert r.status_code == 200
    assert "Python" in r.json()["answer"]
    print("Agent memory OK:", r.json()["answer"][:60])