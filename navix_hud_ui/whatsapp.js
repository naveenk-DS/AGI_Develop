/* ═══════════════════════════════════════════════════
   NAVIX WHATSAPP PANEL — whatsapp.js
   Polls backend or listens to events for WhatsApp
   messages and displays them in the HUD.
═══════════════════════════════════════════════════ */
(function () {
  'use strict';

  const API = 'http://127.0.0.1:8001';
  const POLL_MS = 2000;

  const waFeed = document.getElementById('waFeed');
  const waStatusBadge = document.getElementById('waStatusBadge');

  let processedMessages = new Set();

  function getIconForType(type) {
    switch (type.toLowerCase()) {
      case 'text': return '💬';
      case 'image': return '📷';
      case 'voice_note': return '🎤';
      case 'document': return '📄';
      case 'location': return '📍';
      case 'contact': return '👤';
      case 'sticker': return '🏷️';
      case 'gif': return '🎬';
      case 'poll': return '📊';
      case 'status': return '🔄';
      default: return '✉️';
    }
  }

  function createMessageElement(msg) {
    const el = document.createElement('div');
    el.style.borderLeft = '2px solid var(--cyan)';
    el.style.paddingLeft = '8px';
    el.style.marginBottom = '4px';
    el.style.background = 'rgba(0, 255, 255, 0.05)';
    el.style.padding = '8px';
    el.style.borderRadius = '0 4px 4px 0';
    el.style.animation = 'fadeIn 0.3s ease-out';

    const header = document.createElement('div');
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.fontSize = '0.8rem';
    header.style.color = 'var(--cyan-dim)';
    header.style.marginBottom = '4px';

    const sender = document.createElement('span');
    sender.style.fontWeight = 'bold';
    sender.style.color = 'var(--amber)';
    sender.textContent = `${msg.sender_name || msg.sender} @ ${msg.chat_id}`;

    const timeStr = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const time = document.createElement('span');
    time.textContent = timeStr;

    header.appendChild(sender);
    header.appendChild(time);
    el.appendChild(header);

    const body = document.createElement('div');
    body.style.display = 'flex';
    body.style.alignItems = 'flex-start';
    body.style.gap = '8px';

    const icon = document.createElement('span');
    icon.textContent = getIconForType(msg.type);
    icon.style.fontSize = '1.2rem';
    body.appendChild(icon);

    const content = document.createElement('div');
    content.style.wordBreak = 'break-word';
    content.style.flex = '1';

    let typeLabel = `[${msg.type.toUpperCase()}]`;
    if (msg.type === 'text') typeLabel = '';

    let msgText = msg.content || '';
    if (typeLabel) {
      const typeSpan = document.createElement('span');
      typeSpan.style.color = 'var(--amber)';
      typeSpan.style.marginRight = '5px';
      typeSpan.style.fontSize = '0.8rem';
      typeSpan.textContent = typeLabel;
      content.appendChild(typeSpan);
    }

    const textSpan = document.createElement('span');
    textSpan.textContent = msgText;
    content.appendChild(textSpan);

    body.appendChild(content);
    el.appendChild(body);

    return el;
  }

  function addMessageToFeed(msg) {
    if (processedMessages.has(msg.id)) return;
    processedMessages.add(msg.id);

    // Remove initial sys message if present
    if (waFeed.children.length === 1 && waFeed.children[0].textContent.includes('[SYS]')) {
      waFeed.innerHTML = '';
    }

    const msgEl = createMessageElement(msg);
    waFeed.appendChild(msgEl);

    // Auto-scroll
    waFeed.scrollTop = waFeed.scrollHeight;

    // Keep feed trim
    while (waFeed.children.length > 20) {
      waFeed.removeChild(waFeed.firstChild);
    }
  }

  // Polling for whatsapp events
  async function pollWhatsAppEvents() {
    try {
      const res = await fetch(`${API}/whatsapp/events`, { signal: AbortSignal.timeout(1500) });
      if (!res.ok) return;

      const events = await res.json(); // Array of messages
      if (Array.isArray(events)) {
        events.forEach(msg => addMessageToFeed(msg));
      }
    } catch (_) {
      // Endpoint might not be available
    }
  }

  document.addEventListener('navixUnlocked', () => {
    setInterval(pollWhatsAppEvents, POLL_MS);
  });

  const overlay = document.getElementById('pinOverlay');
  if (!overlay || overlay.style.display === 'none') {
    setInterval(pollWhatsAppEvents, POLL_MS);
  }

  // --- MOCKING FOR DEMONSTRATION IF REQUESTED (Optional) ---
  // If you want to show a sequence right away:
  window.mockWhatsAppSequence = function () {
    const types = ['text', 'image', 'voice_note', 'document', 'location', 'contact', 'sticker', 'gif', 'poll', 'status'];
    let delay = 1000;
    waFeed.innerHTML = ''; // clear sys
    types.forEach((t, i) => {
      setTimeout(() => {
        addMessageToFeed({
          id: `mock-${i}`,
          chat_id: 'Secure Channel',
          sender: 'System Admin',
          sender_name: 'Admin',
          type: t,
          timestamp: new Date().toISOString(),
          content: t === 'text' ? 'Initiating payload transfer...' : `Incoming ${t.toUpperCase()} payload...`
        });
      }, delay);
      delay += 800; // Fast sequence to show the flow TEXT -> IMAGE -> VOICE NOTE etc
    });
  };

  // Trigger automatically to demonstrate the requested flow (Disabled for Real Mode)
  /*
  setTimeout(() => {
    if (typeof window.mockWhatsAppSequence === 'function') {
      window.mockWhatsAppSequence();
    }
  }, 2000);
  */

})();
