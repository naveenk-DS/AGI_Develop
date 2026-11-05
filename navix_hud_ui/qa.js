
/* =========================================================
   NAVIX — CHAT ENGINE & CONVERSATION HISTORY
   FastAPI: http://127.0.0.1:8001
   History: Browser localStorage
========================================================= */

(function () {
  'use strict';

  const API = 'http://127.0.0.1:8001';
  const POLL_MS = 1500;
  const STORAGE_KEY = 'navix_conversations_v1';

  // DOM
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatHistory = document.getElementById('chatHistory');
  const chatStatusBadge = document.getElementById('chatStatusBadge');
  const orbStatus = document.getElementById('orbStatus');

  const newChatBtn = document.getElementById('newChatBtn');
  const searchBtn = document.getElementById('sidebarSearchBtn');
  const historySearch = document.getElementById('historySearch');
  const historySearchInput = document.getElementById('chatHistorySearch');
  const historyList = document.getElementById('chatHistoryList');

  let isSending = false;
  let lastVoiceQuestion = '';
  let lastVoiceAnswer = '';

  let conversations = loadConversations();
  let activeConversationId = null;

  // ---------------------------------------------------------
  // STORAGE
  // ---------------------------------------------------------

  function loadConversations() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      const parsed = saved ? JSON.parse(saved) : [];

      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.error('Could not load NAVIX history:', error);
      return [];
    }
  }

  function saveConversations() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(conversations)
      );
    } catch (error) {
      console.error('Could not save NAVIX history:', error);
      setStatus('HISTORY STORAGE ERROR', 'text-red');
    }
  }

  function createId() {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }

  function getActiveConversation() {
    return conversations.find(
      conversation => conversation.id === activeConversationId
    );
  }

  function createConversation(firstMessage) {
    const conversation = {
      id: createId(),
      title: firstMessage.slice(0, 45),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages: []
    };

    conversations.unshift(conversation);
    activeConversationId = conversation.id;

    saveConversations();
    renderConversationList();

    return conversation;
  }

  // ---------------------------------------------------------
  // STATUS
  // ---------------------------------------------------------

  function setStatus(stateText, colorClass = 'emerald-text') {
    if (chatStatusBadge) {
      chatStatusBadge.className = colorClass;
      chatStatusBadge.textContent = stateText;
    }

    if (orbStatus) {
      orbStatus.textContent = `◈ ${stateText}`;
    }
  }

  // ---------------------------------------------------------
  // MESSAGE RENDERING
  // ---------------------------------------------------------

  function createMessageElement(sender, text) {
    const message = document.createElement('div');

    message.className = `navix-message ${sender}`;
    message.style.display = 'flex';
    message.style.flexDirection = 'column';
    message.style.gap = '5px';
    message.style.padding = '12px 15px';
    message.style.marginBottom = '12px';
    message.style.borderRadius = '12px';
    message.style.fontSize = '13px';
    message.style.lineHeight = '1.6';
    message.style.maxWidth = sender === 'user' ? '85%' : '95%';
    message.style.alignSelf =
      sender === 'user' ? 'flex-end' : 'flex-start';

    message.style.background =
      sender === 'user'
        ? 'rgba(25, 197, 209, 0.10)'
        : 'rgba(255, 255, 255, 0.035)';

    message.style.border =
      sender === 'user'
        ? '1px solid rgba(25, 197, 209, 0.25)'
        : '1px solid rgba(255, 255, 255, 0.08)';

    const label = document.createElement('strong');
    label.textContent = sender === 'user' ? 'YOU' : 'NAVIX';
    label.style.fontSize = '11px';
    label.style.color =
      sender === 'user' ? '#19c5d1' : '#a78bfa';

    const content = document.createElement('span');
    content.textContent = text;

    message.append(label, content);

    return { element: message, content };
  }

  function appendMessage(sender, text) {
    if (!chatHistory) return null;

    chatHistory.style.display = 'flex';
    chatHistory.style.flexDirection = 'column';

    const message = createMessageElement(sender, text);

    chatHistory.appendChild(message.element);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    return message;
  }

  function addMessageToConversation(sender, text) {
    const conversation = getActiveConversation();
    if (!conversation) return;

    conversation.messages.push({
      sender,
      text,
      timestamp: new Date().toISOString()
    });

    conversation.updatedAt = new Date().toISOString();

    conversations.sort(
      (a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)
    );

    saveConversations();
    renderConversationList();
  }

  function renderMessages(messages) {
    if (!chatHistory) return;

    chatHistory.innerHTML = '';
    chatHistory.style.display = messages.length ? 'flex' : 'none';
    chatHistory.style.flexDirection = 'column';

    messages.forEach(message => {
      appendMessage(message.sender, message.text);
    });
  }

  // ---------------------------------------------------------
  // CONVERSATION HISTORY SIDEBAR
  // ---------------------------------------------------------

  function renderConversationList(filter = '') {
    if (!historyList) return;

    historyList.innerHTML = '';

    const heading = document.createElement('div');
    heading.className = 'sidebar-section-title';
    heading.textContent = 'YOUR CHATS';

    historyList.appendChild(heading);

    const query = filter.trim().toLowerCase();

    const filtered = conversations.filter(conversation => {
      const titleMatch = conversation.title.toLowerCase().includes(query);

      const messageMatch = conversation.messages.some(message =>
        message.text.toLowerCase().includes(query)
      );

      return titleMatch || messageMatch;
    });

    if (!filtered.length) {
      const empty = document.createElement('div');
      empty.className = 'history-empty';
      empty.textContent = query
        ? 'No matching conversations'
        : 'Your conversations will appear here';

      historyList.appendChild(empty);
      return;
    }

    filtered.forEach(conversation => {
      const item = document.createElement('div');
      item.className = 'history-item';

      if (conversation.id === activeConversationId) {
        item.classList.add('active');
      }

      const openButton = document.createElement('button');
      openButton.type = 'button';
      openButton.className = 'history-open';

      const icon = document.createElement('i');
      icon.className = 'fa-regular fa-message';

      const title = document.createElement('span');
      title.textContent = conversation.title;

      openButton.append(icon, title);

      openButton.addEventListener('click', () => {
        openConversation(conversation.id);
      });

      const menuButton = document.createElement('button');
      menuButton.type = 'button';
      menuButton.className = 'history-menu';
      menuButton.innerHTML = '<i class="fa-solid fa-ellipsis"></i>';
      menuButton.setAttribute('aria-label', 'Conversation options');

      menuButton.addEventListener('click', event => {
        event.stopPropagation();

        const action = prompt(
          'Enter 1 to rename or 2 to delete this conversation:'
        );

        if (action === '1') {
          renameConversation(conversation.id);
        } else if (action === '2') {
          deleteConversation(conversation.id);
        }
      });

      item.append(openButton, menuButton);
      historyList.appendChild(item);
    });
  }

  function openConversation(id) {
    const conversation = conversations.find(item => item.id === id);
    if (!conversation) return;

    activeConversationId = id;

    renderMessages(conversation.messages);
    renderConversationList(historySearchInput?.value || '');

    setStatus('ONLINE • READY');
  }

  function renameConversation(id) {
    const conversation = conversations.find(item => item.id === id);
    if (!conversation) return;

    const newTitle = prompt(
      'Enter a new conversation title:',
      conversation.title
    );

    if (!newTitle || !newTitle.trim()) return;

    conversation.title = newTitle.trim().slice(0, 80);

    saveConversations();
    renderConversationList(historySearchInput?.value || '');
  }

  function deleteConversation(id) {
    const confirmed = confirm(
      'Are you sure you want to delete this conversation?'
    );

    if (!confirmed) return;

    conversations = conversations.filter(
      conversation => conversation.id !== id
    );

    if (activeConversationId === id) {
      activeConversationId = null;

      if (chatHistory) {
        chatHistory.innerHTML = '';
        chatHistory.style.display = 'none';
      }
    }

    saveConversations();
    renderConversationList(historySearchInput?.value || '');
  }

  // ---------------------------------------------------------
  // NEW CHAT
  // ---------------------------------------------------------

  function startNewChat() {
    if (isSending) return;

    activeConversationId = null;

    if (chatHistory) {
      chatHistory.innerHTML = '';
      chatHistory.style.display = 'none';
    }

    if (chatInput) {
      chatInput.value = '';
      chatInput.focus();
    }

    const welcome = document.getElementById('welcomeHeader');
    const suggestions = document.getElementById('quickActions');

    if (welcome) welcome.style.display = '';
    if (suggestions) suggestions.style.display = '';

    setStatus('ONLINE • READY');
    renderConversationList();
  }

  // ---------------------------------------------------------
  // SEND MESSAGE
  // ---------------------------------------------------------

  async function handleSend(query) {
    if (!query || !query.trim() || isSending) return;

    const cleanQuery = query.trim();

    if (chatInput) chatInput.value = '';

    const welcome = document.getElementById('welcomeHeader');
    const suggestions = document.getElementById('quickActions');

    if (welcome) welcome.style.display = 'none';
    if (suggestions) suggestions.style.display = 'none';

    if (!activeConversationId) {
      createConversation(cleanQuery);
    }

    appendMessage('user', cleanQuery);
    addMessageToConversation('user', cleanQuery);

    isSending = true;
    setStatus('THINKING...', 'cyan-text');

    const placeholder = appendMessage('assistant', 'Thinking...');

    try {
      const response = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: cleanQuery
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      const reply =
        data.reply ||
        data.response ||
        data.message ||
        'No answer received from AI.';

      if (placeholder) {
        placeholder.content.textContent = reply;
      }

      addMessageToConversation('assistant', reply);
      setStatus('ONLINE • READY');

    } catch (error) {
      console.error('NAVIX chat error:', error);

      const errorMessage =
        `Could not connect to backend at ${API}. ` +
        'Make sure navix_start.py is running.';

      if (placeholder) {
        placeholder.content.textContent = errorMessage;
      }

      addMessageToConversation('assistant', errorMessage);

      setStatus('ERROR • CHECK BACKEND', 'text-red');

    } finally {
      isSending = false;

      if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
      }
    }
  }

  // ---------------------------------------------------------
  // EVENT LISTENERS
  // ---------------------------------------------------------

  newChatBtn?.addEventListener('click', startNewChat);

  searchBtn?.addEventListener('click', () => {
    if (!historySearch) return;

    historySearch.hidden = !historySearch.hidden;

    if (!historySearch.hidden) {
      historySearchInput?.focus();
    } else if (historySearchInput) {
      historySearchInput.value = '';
      renderConversationList();
    }
  });

  historySearchInput?.addEventListener('input', event => {
    renderConversationList(event.target.value);
  });

  chatSendBtn?.addEventListener('click', () => {
    handleSend(chatInput?.value || '');
  });

  chatInput?.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend(chatInput.value);
    }
  });

  document.querySelectorAll('.sugg-item').forEach(item => {
    item.style.cursor = 'pointer';

    item.addEventListener('click', () => {
      handleSend(item.textContent.trim());
    });
  });

  // ---------------------------------------------------------
  // VOICE HUD POLLING
  // ---------------------------------------------------------

  async function pollVoiceEvents() {
    try {
      const response = await fetch(`${API}/hud/latest`, {
        signal: AbortSignal.timeout(2000)
      });

      if (!response.ok) return;

      const event = await response.json();

      if (event.question && event.question !== lastVoiceQuestion) {
        lastVoiceQuestion = event.question;

        if (!activeConversationId) {
          createConversation(event.question);
        }

        const question = `🎙️ "${event.question}"`;

        appendMessage('user', question);
        addMessageToConversation('user', question);
      }

      if (event.answer && event.answer !== lastVoiceAnswer) {
        lastVoiceAnswer = event.answer;

        appendMessage('assistant', event.answer);
        addMessageToConversation('assistant', event.answer);
      }

      if (event.state) {
        const states = {
          listening: ['LISTENING...', 'cyan-text'],
          thinking: ['THINKING...', 'cyan-text'],
          speaking: ['SPEAKING...', 'purple-text'],
          ready: ['ONLINE • READY', 'emerald-text']
        };

        const [text, color] =
          states[event.state] || ['ONLINE • READY', 'emerald-text'];

        setStatus(text, color);
      }

    } catch (_) {
      // Voice polling errors are intentionally silent.
    }
  }

  // ---------------------------------------------------------
  // INITIALIZATION
  // ---------------------------------------------------------

  renderConversationList();

  // Restore the most recent conversation on page refresh.
  if (conversations.length > 0) {
    openConversation(conversations[0].id);
  }

  setInterval(pollVoiceEvents, POLL_MS);

})();
