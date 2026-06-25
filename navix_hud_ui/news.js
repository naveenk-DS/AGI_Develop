/* ═══════════════════════════════════════════════
   NAVIX NEWS ENGINE — news.js
   OFFLINE: uses curated hardcoded AI headlines.
   ONLINE : fetches live feed via rss2json API
            (falls back to offline on failure).
   Renders into #newsTickerLeft and #newsTickerRight.
   Auto-scroll on left ticker starts after PIN unlock.
═══════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── Offline dataset ──────────────────────── */
  const OFFLINE_NEWS = [
    { title: 'GPT-5 Achieves Human-Level Reasoning on All Benchmarks', source: 'OpenAI Blog', time: '1h ago', tag: 'LLM' },
    { title: 'Google DeepMind Gemini Ultra 2.0 Breaks AGI Score Records', source: 'DeepMind', time: '3h ago', tag: 'AGI' },
    { title: 'Meta LLaMA 4 Released — 405B Parameters, Fully Open Source', source: 'Meta AI', time: '5h ago', tag: 'OPEN' },
    { title: 'Anthropic Claude 4 Surpasses Humans in Competitive Coding', source: 'Anthropic', time: '7h ago', tag: 'CODE' },
    { title: 'AI Model Discovers Novel Antibiotic Compound in 48 Hours', source: 'Nature', time: '9h ago', tag: 'BIO' },
    { title: 'Microsoft Copilot Now Integrated Into Every Windows App', source: 'Microsoft', time: '11h ago', tag: 'TOOL' },
    { title: 'NVIDIA H200 GPUs Ship to 50+ Nations — AI Race Accelerates', source: 'Reuters', time: '13h ago', tag: 'HW' },
    { title: 'OpenAI o3 Achieves PhD-Level Performance Across All STEM', source: 'MIT TR', time: '1d ago', tag: 'BENCH' },
    { title: 'EU AI Act Enforcement Begins — Firms Face €30M Fines', source: 'TechCrunch', time: '1d ago', tag: 'POLICY' },
    { title: 'Sora 2.0 Generates 10-Minute Photorealistic Video from Text', source: 'OpenAI', time: '2d ago', tag: 'VIDEO' },
    { title: 'AI Chip Startup Raises $4B Challenging NVIDIA Dominance', source: 'Bloomberg', time: '2d ago', tag: 'CHIPS' },
    { title: 'Autonomous Agents Complete 72h Business Tasks Unattended', source: 'VentureBeat', time: '2d ago', tag: 'AGENT' },
    { title: 'Mistral AI "Mistral 3" Released — Outperforms GPT-4o', source: 'Mistral', time: '3d ago', tag: 'LLM' },
    { title: 'Apple Intelligence Expands to 40 Languages Worldwide', source: 'Apple', time: '3d ago', tag: 'PROD' },
    { title: 'Boston Dynamics Unveils AI-Powered Atlas 2 Humanoid Robot', source: 'BD', time: '4d ago', tag: 'ROBOT' },
    { title: 'Gemini 2.5 Flash Becomes Default Model in Google Search', source: 'Google', time: '4d ago', tag: 'SEARCH' },
    { title: 'Stanford HAI Report: AI Investment Hits $320B in 2025', source: 'Stanford', time: '5d ago', tag: 'ECON' },
    { title: 'OpenAI Launches "Operator" for Fully Autonomous Web Tasks', source: 'OpenAI', time: '5d ago', tag: 'AGENT' },
  ];

  /* ── RSS feed (online mode) ───────────────── */
  const RSS_URL = 'https://venturebeat.com/ai/feed/';

  async function fetchOnlineNews() {
    try {
      const api = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(RSS_URL)}&count=18`;
      const res = await fetch(api, { signal: AbortSignal.timeout(8000) });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      if (data.status !== 'ok' || !data.items?.length) throw new Error('bad feed');
      return data.items.map(item => ({
        title: (item.title || '').replace(/&amp;/g, '&').slice(0, 95),
        source: 'VentureBeat',
        time: formatAge(new Date(item.pubDate)),
        tag: 'LIVE',
      }));
    } catch (err) {
      console.warn('[NAVIX News] Online fetch failed — using offline data.', err.message);
      return null; // signal fallback
    }
  }

  function formatAge(date) {
    const h = Math.floor((Date.now() - date) / 3_600_000);
    if (h < 1) return 'JUST NOW';
    if (h < 24) return h + 'h ago';
    return Math.floor(h / 24) + 'd ago';
  }

  /* ── Render helpers ───────────────────────── */
  function setBadge(id, mode) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = mode === 'online' ? '● LIVE' : 'OFFLINE';
    el.className = 'news-badge' + (mode === 'online' ? ' badge-online' : '');
  }

  function renderLeft(items) {
    const el = document.getElementById('newsTickerLeft');
    if (!el) return;
    el.innerHTML = '';
    items.forEach(item => {
      const d = document.createElement('div');
      d.className = 'news-ticker-item';
      d.innerHTML = `<span class="news-tag${item.tag === 'LIVE' ? ' tag-live' : ''}">${item.tag}</span>
        <span class="news-title-text">${item.title}</span>
        <span class="news-meta">${item.source} · ${item.time}</span>`;
      el.appendChild(d);
    });
  }

  function renderRight(items) {
    const el = document.getElementById('newsTickerRight');
    if (!el) return;
    el.innerHTML = '';
    items.slice(0, 7).forEach((item, i) => {
      const d = document.createElement('div');
      d.className = 'news-right-item';
      d.style.animationDelay = (i * 0.1) + 's';
      d.innerHTML = `
        <div class="news-right-header">
          <span class="news-tag${item.tag === 'LIVE' ? ' tag-live' : ''}">${item.tag}</span>
          <span class="news-right-time">${item.time}</span>
        </div>
        <div class="news-right-title">${item.title}</div>
        <div class="news-right-source">${item.source}</div>`;
      el.appendChild(d);
    });
  }

  /* ── Auto-scroll left ticker ──────────────── */
  let scrollRaf = null;
  function startScroll() {
    const el = document.getElementById('newsTickerLeft');
    if (!el) return;
    let pos = 0;
    function tick() {
      pos += 0.4;
      if (pos >= el.scrollHeight - el.clientHeight + 1) pos = 0;
      el.scrollTop = pos;
      scrollRaf = requestAnimationFrame(tick);
    }
    scrollRaf = requestAnimationFrame(tick);
  }

  /* ── Main init ────────────────────────────── */
  async function init(mode) {
    setBadge('newsBadgeLeft', mode);
    setBadge('newsBadgeRight', mode);

    let items = OFFLINE_NEWS;

    if (mode === 'online') {
      const live = await fetchOnlineNews();
      items = live ?? OFFLINE_NEWS; // fallback if fetch failed
      if (!live) {
        setBadge('newsBadgeLeft', 'offline');
        setBadge('newsBadgeRight', 'offline');
      }
      // Refresh live news every 5 minutes
      setInterval(async () => {
        const fresh = await fetchOnlineNews();
        if (fresh) { renderLeft(fresh); renderRight(fresh); }
      }, 300_000);
    }

    renderLeft(items);
    renderRight(items);
  }

  /* ── Wait for unlock before auto-scroll ──── */
  document.addEventListener('navixUnlocked', () => {
    setTimeout(startScroll, 600); // slight delay after fade-in
  });

  /* ── Boot: wait for mode selection ─────────── */
  document.addEventListener('navixModeSelected', (e) => {
    init(e.detail.mode);
  });

  // If mode was already set (e.g. page refresh), init immediately
  const storedMode = sessionStorage.getItem('navix_mode');
  if (storedMode) init(storedMode);

})();
