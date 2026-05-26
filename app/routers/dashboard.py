from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models import UsageLog, Conversation, License
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=24)

    total_logs = await db.execute(select(func.count(UsageLog.id)))
    total_convs = await db.execute(select(func.count(Conversation.id)))
    recent_logs = await db.execute(
        select(UsageLog)
        .order_by(UsageLog.created_at.desc())
        .limit(10)
    )

    logs = recent_logs.scalars().all()

    return {
        "total_events": total_logs.scalar(),
        "total_messages": total_convs.scalar(),
        "recent_logs": [
            {
                "event_type": l.event_type,
                "customer_id": l.customer_id,
                "created_at": str(l.created_at),
                "event_data": l.event_data
            }
            for l in logs
        ]
    }

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>MyAIProduct Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui; background: #0a0c10; color: #e2e8f0; padding: 24px; }
        h1 { font-size: 1.5rem; margin-bottom: 20px; color: #00d4aa; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
        .card { background: #0f1218; border: 1px solid #1e2736; border-radius: 10px; padding: 16px; }
        .card h3 { font-size: 0.8rem; color: #6b7a9a; margin-bottom: 8px; }
        .card p { font-size: 1.8rem; font-weight: 700; color: #00d4aa; }
        .logs { background: #0f1218; border: 1px solid #1e2736; border-radius: 10px; padding: 16px; margin-bottom: 24px; }
        .logs h2 { font-size: 1rem; margin-bottom: 12px; }
        .log-item { padding: 8px; border-bottom: 1px solid #1e2736; font-size: 0.78rem; }
        .log-item span { color: #00d4aa; margin-right: 8px; }
        .chat { background: #0f1218; border: 1px solid #1e2736; border-radius: 10px; padding: 16px; }
        .chat h2 { font-size: 1rem; margin-bottom: 12px; }
        #messages { height: 200px; overflow-y: auto; margin-bottom: 12px; padding: 8px; background: #070b10; border-radius: 6px; font-size: 0.8rem; }
        .msg-user { color: #9b72ff; margin: 4px 0; }
        .msg-ai { color: #00d4aa; margin: 4px 0; }
        .input-row { display: flex; gap: 8px; }
        input { flex: 1; background: #070b10; border: 1px solid #1e2736; color: #e2e8f0; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; }
        button { background: #00d4aa; color: #0a0c10; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 700; }
        .status { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; }
        .green { background: #00d4aa20; border: 1px solid #00d4aa; color: #00d4aa; }
        .red { background: #ff6b6b20; border: 1px solid #ff6b6b; color: #ff6b6b; }
    </style>
</head>
<body>
    <h1>🤖 MyAGIProduct Dashboard</h1>

    <div class="status" id="status-bar">
        <div class="badge" id="api-status">API: checking...</div>
        <div class="badge" id="ollama-status">Ollama: checking...</div>
        <div class="badge" id="qdrant-status">Qdrant: checking...</div>
    </div>

    <div class="grid">
        <div class="card"><h3>Total Events</h3><p id="total-events">-</p></div>
        <div class="card"><h3>Total Messages</h3><p id="total-messages">-</p></div>
        <div class="card"><h3>Status</h3><p style="font-size:1rem;margin-top:4px" id="uptime">Live</p></div>
    </div>

    <div class="logs" id="analytics-section">
        <h2>Analytics</h2>
        <div id="analytics-content">Loading...</div>
    </div>

    <div class="logs">
        <h2>Recent Activity</h2>
        <div id="log-list">Loading...</div>
    </div>

    <div class="chat">
        <h2>Quick Chat</h2>
        <div id="messages"></div>
        <div class="input-row">
            <input id="msg-input" placeholder="Ask your AI..." onkeypress="if(event.key==='Enter')sendMsg()"/>
            <button onclick="sendMsg()">Send</button>
        </div>
    </div>

<script>
const SESSION = "dashboard-" + Date.now()

async function loadStats() {
    try {
        const r = await fetch("/dashboard/stats")
        const d = await r.json()
        document.getElementById("total-events").textContent = d.total_events
        document.getElementById("total-messages").textContent = d.total_messages
        const list = document.getElementById("log-list")
        if (d.recent_logs.length === 0) {
            list.innerHTML = "<div class='log-item'>No activity yet</div>"
        } else {
            list.innerHTML = d.recent_logs.map(l =>
                `<div class='log-item'><span>${l.event_type}</span>${l.customer_id} — ${l.created_at.substring(0,19)}</div>`
            ).join("")
        }
    } catch(e) { console.error(e) }
}

async function checkServices() {
    const checks = [
        { id: "api-status", url: "/health", label: "API" },
        { id: "ollama-status", url: "http://127.0.0.1:11434/api/tags", label: "Ollama" },
        { id: "qdrant-status", url: "http://127.0.0.1:6333/healthz", label: "Qdrant" }
    ]
    for (const c of checks) {
        try {
            await fetch(c.url)
            const el = document.getElementById(c.id)
            el.textContent = c.label + ": Online"
            el.className = "badge green"
        } catch {
            const el = document.getElementById(c.id)
            el.textContent = c.label + ": Offline"
            el.className = "badge red"
        }
    }
}

async function sendMsg() {
    const input = document.getElementById("msg-input")
    const msg = input.value.trim()
    if (!msg) return
    input.value = ""

    const messages = document.getElementById("messages")
    messages.innerHTML += `<div class='msg-user'>You: ${msg}</div>`

    const aiDiv = document.createElement("div")
    aiDiv.className = "msg-ai"
    aiDiv.textContent = "AI: "
    messages.appendChild(aiDiv)
    messages.scrollTop = messages.scrollHeight

    try {
        const response = await fetch("/stream/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({session_id: SESSION, message: msg})
        })

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
            const {done, value} = await reader.read()
            if (done) break
            aiDiv.textContent += decoder.decode(value)
            messages.scrollTop = messages.scrollHeight
        }

        loadStats()
    } catch(e) {
        aiDiv.textContent += " [Error: could not reach API]"
        aiDiv.style.color = "#ff6b6b"
    }
}

async function loadAnalytics() {
    try {
        const r = await fetch("/analytics/overview")
        const d = await r.json()
        document.getElementById("analytics-content").innerHTML = `
            <div class="log-item">Events last 24h: <span>${d.events_last_24h}</span></div>
            <div class="log-item">Events last 7d: <span>${d.events_last_7d}</span></div>
            <div class="log-item">Total sessions: <span>${d.total_sessions}</span></div>
            <div class="log-item">Total messages: <span>${d.total_messages}</span></div>
        `
    } catch(e) { console.error(e) }
}

loadAnalytics()
setInterval(loadAnalytics, 30000)

loadStats()
checkServices()
setInterval(loadStats, 10000)
setInterval(checkServices, 30000)
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)