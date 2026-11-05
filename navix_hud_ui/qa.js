/* ═══════════════════════════════════════════════════
   NAVIX HUD Q&A & CHAT ENGINE — qa.js
   Connects the Web HUD input fields to the FastAPI backend (http://127.0.0.1:8001/chat)
   and polls live voice interactions from /hud/latest.
═══════════════════════════════════════════════════ */
(function () {
  'use strict';

  const API = 'http://127.0.0.1:8001';
  const POLL_MS = 1500;

  // DOM elements
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatHistory = document.getElementById('chatHistory');
  const chatStatusBadge = document.getElementById('chatStatusBadge');
  const topSearchInput = document.getElementById('topSearchInput');
  const orbStatus = document.getElementById('orbStatus');

  let isSending = false;
  let lastVoiceQuestion = '';
  let lastVoiceAnswer = '';

  function setStatus(stateText, colorClass = 'emerald-text') {
    if (chatStatusBadge) {
      chatStatusBadge.className = colorClass;
      chatStatusBadge.innerHTML = `<i class="fa-solid fa-circle-dot" style="font-size: 8px;"></i> ${stateText}`;
    }
    if (orbStatus) {
      orbStatus.textContent = `◈ ${stateText}`;
    }
  }

  function appendMessage(sender, text) {
    if (!chatHistory) return;
    chatHistory.style.display = 'flex';

    const msgEl = document.createElement('div');
    msgEl.style.display = 'flex';
    msgEl.style.flexDirection = 'column';
    msgEl.style.gap = '2px';
    msgEl.style.padding = '8px 12px';
    msgEl.style.borderRadius = '8px';
    msgEl.style.fontSize = '0.9rem';
    msgEl.style.lineHeight = '1.4';

    if (sender === 'user') {
      msgEl.style.background = 'rgba(0, 245, 255, 0.1)';
      msgEl.style.border = '1px solid rgba(0, 245, 255, 0.3)';
      msgEl.style.alignSelf = 'flex-end';
      msgEl.style.maxWidth = '85%';
      msgEl.innerHTML = `<span style="font-size: 0.75rem; color: var(--cyan); font-weight: 700;">YOU</span><span>${escapeHtml(text)}</span>`;
    } else {
      msgEl.style.background = 'rgba(168, 85, 247, 0.1)';
      msgEl.style.border = '1px solid rgba(168, 85, 247, 0.3)';
      msgEl.style.alignSelf = 'flex-start';
      msgEl.style.maxWidth = '90%';
      msgEl.innerHTML = `<span style="font-size: 0.75rem; color: #a855f7; font-weight: 700;">NAVIX</span><span>${escapeHtml(text)}</span>`;
    }

    chatHistory.appendChild(msgEl);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return msgEl;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function handleSend(query) {
    if (!query || !query.trim() || isSending) return;
    const cleanQuery = query.trim();

    if (chatInput) chatInput.value = '';
    if (topSearchInput) topSearchInput.value = '';

    appendMessage('user', cleanQuery);
    isSending = true;
    setStatus('THINKING...', 'cyan-text');

    // Create placeholder for assistant
    const replyPlaceholder = appendMessage('assistant', 'Thinking...');

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: cleanQuery }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();
      const reply = data.reply || data.response || data.message || 'No answer received from AI.';

      setStatus('ONLINE • READY', 'emerald-text');
      if (replyPlaceholder) {
        replyPlaceholder.innerHTML = `<span style="font-size: 0.75rem; color: #a855f7; font-weight: 700;">NAVIX</span><span>${escapeHtml(reply)}</span>`;
      }
    } catch (err) {
      console.error('NAVIX chat error:', err);
      setStatus('ERROR • CHECK BACKEND', 'text-red');
      if (replyPlaceholder) {
        replyPlaceholder.innerHTML = `<span style="font-size: 0.75rem; color: #ff4d4d; font-weight: 700;">NAVIX</span><span style="color: #ff8888;">Could not connect to backend at ${API}. Make sure navix_start.py is running.</span>`;
      }
      setTimeout(() => setStatus('ONLINE • READY', 'emerald-text'), 5000);
    } finally {
      isSending = false;
      if (chatHistory) chatHistory.scrollTop = chatHistory.scrollHeight;
    }
  }

  // ── Event listeners ───────────────────────────────────────────
  if (chatSendBtn) {
    chatSendBtn.addEventListener('click', () => {
      if (chatInput) handleSend(chatInput.value);
    });
  }

  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSend(chatInput.value);
      }
    });
  }

  if (topSearchInput) {
    topSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSend(topSearchInput.value);
      }
    });
  }

  // Smart suggestions click handlers
  document.querySelectorAll('.sugg-item').forEach((item) => {
    item.style.cursor = 'pointer';
    item.addEventListener('click', () => {
      const text = item.textContent.trim();
      handleSend(text);
    });
  });

  // ── Poll voice HUD events ─────────────────────────────────────
  async function pollVoiceEvents() {
    try {
      const res = await fetch(`${API}/hud/latest`, { signal: AbortSignal.timeout(2000) });
      if (!res.ok) return;
      const ev = await res.json();

      if (ev.question && ev.question !== lastVoiceQuestion) {
        lastVoiceQuestion = ev.question;
        appendMessage('user', `🎙️ "${ev.question}"`);
      }
      if (ev.answer && ev.answer !== lastVoiceAnswer) {
        lastVoiceAnswer = ev.answer;
        appendMessage('assistant', ev.answer);
      }
      if (ev.state) {
        const stateMap = {
          listening: ['LISTENING...', 'cyan-text'],
          thinking: ['THINKING...', 'cyan-text'],
          speaking: ['SPEAKING...', 'purple-text'],
          ready: ['ONLINE • READY', 'emerald-text'],
        };
        const [txt, cls] = stateMap[ev.state] || ['ONLINE • READY', 'emerald-text'];
        setStatus(txt, cls);
      }
    } catch (_) {
      // Backend polling silent catch
    }
  }

  setInterval(pollVoiceEvents, POLL_MS);
})();
