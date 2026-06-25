/* ═══════════════════════════════════════════════════
   NAVIX Q&A LIVE PANEL — qa.js
   Polls backend at http://127.0.0.1:8001 for the
   latest voice interaction (question + response).
   Updates the center Q&A panel in real time.
═══════════════════════════════════════════════════ */
(function () {
  'use strict';

  const API = 'http://127.0.0.1:8001';
  const POLL_MS = 1500;

  /* ── DOM refs ─────────────────────────────────── */
  const qaBadge = document.getElementById('qaBadge');
  const qaQuestionEl = document.getElementById('qaQuestionText');
  const qaAnswerEl = document.getElementById('qaAnswerText');
  const qaRecList = document.getElementById('qaRecList');
  const orbStatus = document.getElementById('orbStatus');

  /* ── State ────────────────────────────────────── */
  let lastQuestion = '';
  let lastAnswer = '';
  let isTyping = false;

  /* ── Recommendations pool ─────────────────────── */
  const RECS = [
    'Try: "What\'s the latest AI news?"',
    'Try: "Summarize my notes"',
    'Try: "Open Chrome and search for AI news"',
    'Try: "What is the weather today?"',
    'Try: "Write a Python function to sort a list"',
    'Try: "Tell me a fun fact about space"',
    'Try: "Set a reminder for 5 PM"',
    'Try: "Explain quantum computing simply"',
    'Try: "What did we discuss yesterday?"',
    'Try: "Create a to-do list for today"',
  ];

  function shuffleRecs() {
    const picks = [...RECS].sort(() => Math.random() - 0.5).slice(0, 3);
    qaRecList.innerHTML = '';
    picks.forEach(r => {
      const s = document.createElement('span');
      s.className = 'qa-rec-item';
      s.textContent = r;
      // Click on recommendation to ask it
      s.addEventListener('click', () => askQuestion(r.replace('Try: "', '').replace('"', '')));
      qaRecList.appendChild(s);
    });
  }

  /* ── Type-writer effect ───────────────────────── */
  function typeWrite(el, text, speed = 18) {
    if (isTyping) { el.textContent = text; return; }
    isTyping = true;
    el.textContent = '';
    el.classList.add('qa-cursor');
    let i = 0;
    const iv = setInterval(() => {
      el.textContent += text[i++];
      if (i >= text.length) {
        clearInterval(iv);
        el.classList.remove('qa-cursor');
        isTyping = false;
      }
    }, speed);
  }

  /* ── Set badge state ──────────────────────────── */
  function setBadge(state) {
    const states = {
      ready: { text: 'READY', cls: '' },
      listening: { text: 'LISTENING', cls: 'listening' },
      thinking: { text: 'THINKING', cls: 'thinking' },
      speaking: { text: 'SPEAKING', cls: 'speaking' },
    };
    const s = states[state] || states.ready;
    qaBadge.textContent = s.text;
    qaBadge.className = 'qa-badge' + (s.cls ? ' ' + s.cls : '');

    // Also sync orb status
    const orbMap = { ready: '◈ ONLINE', listening: '◉ LISTENING', thinking: '◎ THINKING', speaking: '◉ SPEAKING' };
    if (orbStatus) orbStatus.textContent = orbMap[state] || '◈ ONLINE';
  }

  /* ── Ask a question via API ───────────────────── */
  async function askQuestion(q) {
    qaQuestionEl.textContent = q;
    setBadge('thinking');
    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q }),
      });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      const answer = data.reply || data.response || data.message || JSON.stringify(data);
      lastQuestion = q;
      lastAnswer = answer;
      setBadge('speaking');
      typeWrite(qaAnswerEl, answer);
      setTimeout(() => setBadge('ready'), 4000);
      shuffleRecs();
    } catch (e) {
      setBadge('ready');
      qaAnswerEl.textContent = 'Backend not responding. Make sure navix_start.py is running.';
    }
  }

  /* ── Poll backend for latest interaction ─────── */
  let pollActive = false;

  async function poll() {
    if (pollActive) return;
    pollActive = true;
    try {
      // Try to get latest session/conversation from dashboard or sessions endpoint
      const res = await fetch(`${API}/dashboard`, { signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        const data = await res.json();
        // Update metrics if available
        if (data.total_sessions !== undefined) {
          const alertEl = document.getElementById('alert-val');
          if (alertEl) alertEl.textContent = data.active_sessions ?? 0;
        }
      }
    } catch (_) {
      // Silent fail — backend might not have this endpoint
    } finally {
      pollActive = false;
    }
  }

  /* ── Listen for NAVIX events (from navix_start.py via custom events) ── */
  // navix_start.py can post to a /hud/event endpoint which we poll
  async function pollHudEvents() {
    try {
      const res = await fetch(`${API}/hud/latest`, { signal: AbortSignal.timeout(2000) });
      if (!res.ok) return;
      const ev = await res.json();

      if (ev.question && ev.question !== lastQuestion) {
        lastQuestion = ev.question;
        qaQuestionEl.textContent = ev.question;
        setBadge(ev.state || 'thinking');
      }
      if (ev.answer && ev.answer !== lastAnswer) {
        lastAnswer = ev.answer;
        typeWrite(qaAnswerEl, ev.answer);
        setBadge('ready');
        shuffleRecs();
      }
      if (ev.state) setBadge(ev.state);

    } catch (_) {
      // /hud/latest endpoint doesn't exist yet — silent fail
    }
  }

  /* ── Boot ─────────────────────────────────────── */
  document.addEventListener('navixUnlocked', () => {
    shuffleRecs();
    setBadge('ready');
    setInterval(poll, 10000);
    setInterval(pollHudEvents, POLL_MS);
  });

  // If already unlocked (page refresh)
  const overlay = document.getElementById('pinOverlay');
  if (!overlay || overlay.style.display === 'none') {
    shuffleRecs();
    setBadge('ready');
    setInterval(poll, 10000);
    setInterval(pollHudEvents, POLL_MS);
  }

})();
