/* ═══════════════════════════════════════════════════════
   NAVIX PIN LOCK — pin.js
   ─────────────────────────────────────────────────────
   Flow:
   1. On load — if no PIN stored → show SET PIN mode
   2. If PIN stored → show ENTER PIN mode
   3. Correct PIN → flash + fade overlay, HUD activates
   4. Wrong PIN → shake + red dots + error msg
   5. "SET / CHANGE PIN" link → set-new-PIN flow
═══════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Constants ──────────────────────────────────── */
  const PIN_KEY = 'navix_pin';
  const MAX_DIGITS = 4;
  const MAX_ATTEMPTS = 5;

  /* ── State ──────────────────────────────────────── */
  let inputBuffer = '';
  let mode = 'enter';   // 'enter' | 'set_new' | 'confirm_new'
  let pendingPin = '';
  let attempts = 0;
  let locked = false;
  let lockTimer = null;

  /* ── DOM refs ───────────────────────────────────── */
  const overlay = document.getElementById('pinOverlay');
  const statusEl = document.getElementById('pinStatus');
  const subtitleEl = document.getElementById('pinSubtitle');
  const dotsEl = document.getElementById('pinDots');
  const numpad = document.getElementById('pinNumpad');
  const setPinLink = document.getElementById('setPinLink');

  /* ── Init ───────────────────────────────────────── */
  function init() {
    const stored = getPin();
    if (!stored) {
      enterSetMode();
    } else {
      enterEnterMode();
    }
    bindEvents();
  }

  /* ── PIN storage (obfuscated in localStorage) ───── */
  function getPin() {
    try {
      const raw = localStorage.getItem(PIN_KEY);
      if (!raw) return null;
      return atob(raw);
    } catch { return null; }
  }

  function savePin(pin) {
    localStorage.setItem(PIN_KEY, btoa(pin));
  }

  /* ── Mode switching ─────────────────────────────── */
  function enterEnterMode() {
    mode = 'enter';
    inputBuffer = '';
    setStatus('ENTER YOUR PIN TO ACTIVATE', '');
    subtitleEl.textContent = 'AGI INTERFACE v3.0 — SECURE ACCESS';
    resetDots();
    setPinLink.style.display = '';
  }

  function enterSetMode() {
    mode = 'set_new';
    inputBuffer = '';
    pendingPin = '';
    setStatus('SET A NEW 4-DIGIT PIN', 'set-txt');
    subtitleEl.textContent = 'FIRST-TIME SETUP — CREATE YOUR PASSCODE';
    resetDots();
    setPinLink.style.display = 'none';
  }

  function enterConfirmMode() {
    mode = 'confirm_new';
    inputBuffer = '';
    setStatus('CONFIRM YOUR NEW PIN', 'set-txt');
    resetDots();
  }

  /* ── Dot rendering ──────────────────────────────── */
  function resetDots(cls) {
    for (let i = 0; i < MAX_DIGITS; i++) {
      const d = document.getElementById('pd' + i);
      d.className = 'pin-dot' + (cls ? ' ' + cls : '');
    }
  }

  function renderDots(n, cls) {
    for (let i = 0; i < MAX_DIGITS; i++) {
      const d = document.getElementById('pd' + i);
      d.className = 'pin-dot' + (i < n ? ' ' + (cls || 'filled') : '');
    }
  }

  /* ── Status helper ──────────────────────────────── */
  function setStatus(text, cls) {
    statusEl.textContent = text;
    statusEl.className = 'pin-status' + (cls ? ' ' + cls : '');
  }

  /* ── Input handling ─────────────────────────────── */
  function pressDigit(d) {
    if (locked) return;
    if (inputBuffer.length >= MAX_DIGITS) return;
    inputBuffer += d;
    renderDots(inputBuffer.length);
  }

  function pressClear() {
    if (locked) return;
    inputBuffer = inputBuffer.slice(0, -1);
    renderDots(inputBuffer.length);
    if (inputBuffer.length === 0) setStatus(
      mode === 'enter' ? 'ENTER YOUR PIN TO ACTIVATE' :
        mode === 'set_new' ? 'SET A NEW 4-DIGIT PIN' : 'CONFIRM YOUR NEW PIN',
      mode === 'enter' ? '' : 'set-txt'
    );
  }

  function pressEnter() {
    if (locked) return;
    if (inputBuffer.length < MAX_DIGITS) {
      shake();
      setStatus('ENTER ALL 4 DIGITS', 'error-txt');
      return;
    }

    if (mode === 'enter') {
      verifyPin();
    } else if (mode === 'set_new') {
      pendingPin = inputBuffer;
      enterConfirmMode();
    } else if (mode === 'confirm_new') {
      confirmNewPin();
    }
  }

  /* ── PIN verification ───────────────────────────── */
  function verifyPin() {
    const stored = getPin();
    if (inputBuffer === stored) {
      unlockHUD();
    } else {
      attempts++;
      inputBuffer = '';
      resetDots('error');
      shake();

      if (attempts >= MAX_ATTEMPTS) {
        lockout();
      } else {
        const left = MAX_ATTEMPTS - attempts;
        setStatus(`WRONG PIN — ${left} ATTEMPT${left !== 1 ? 'S' : ''} LEFT`, 'error-txt');
        setTimeout(() => {
          if (mode === 'enter') {
            resetDots();
            setStatus('ENTER YOUR PIN TO ACTIVATE', '');
          }
        }, 1500);
      }
    }
  }

  function confirmNewPin() {
    if (inputBuffer === pendingPin) {
      savePin(pendingPin);
      resetDots('success');
      setStatus('PIN SAVED — ACTIVATING…', 'success-txt');
      setTimeout(() => unlockHUD(), 900);
    } else {
      inputBuffer = '';
      pendingPin = '';
      shake();
      resetDots('error');
      setStatus('PINs DO NOT MATCH — TRY AGAIN', 'error-txt');
      setTimeout(() => enterSetMode(), 1600);
    }
  }

  /* ── Lockout ────────────────────────────────────── */
  function lockout() {
    locked = true;
    let secs = 30;
    numpad.style.pointerEvents = 'none';
    numpad.style.opacity = '0.3';

    function tick() {
      setStatus(`TOO MANY ATTEMPTS — LOCKED ${secs}s`, 'error-txt');
      if (secs <= 0) {
        locked = false;
        attempts = 0;
        numpad.style.pointerEvents = '';
        numpad.style.opacity = '';
        inputBuffer = '';
        resetDots();
        setStatus('ENTER YOUR PIN TO ACTIVATE', '');
        return;
      }
      secs--;
      lockTimer = setTimeout(tick, 1000);
    }
    tick();
  }

  /* ── Unlock HUD ─────────────────────────────────── */
  function unlockHUD() {
    resetDots('success');
    setStatus('ACCESS GRANTED — ONLINE', 'success-txt');
    document.dispatchEvent(new CustomEvent('navixUnlocked', {
      detail: { mode: sessionStorage.getItem('navix_mode') || 'offline' }
    }));

    // Flash → then fade out
    overlay.classList.add('flash-unlock');
    setTimeout(() => {
      overlay.classList.add('unlocking');
      setTimeout(() => {
        overlay.style.display = 'none';
      }, 850);
    }, 400);
  }

  /* ── Shake util ─────────────────────────────────── */
  function shake() {
    const dots = document.getElementById('pinDots');
    dots.classList.remove('pin-shake');
    void dots.offsetWidth; // reflow
    dots.classList.add('pin-shake');
    setTimeout(() => dots.classList.remove('pin-shake'), 600);
  }

  /* ── Events ─────────────────────────────────────── */
  function bindEvents() {
    // Numpad buttons
    numpad.querySelectorAll('.pin-key[data-val]').forEach(btn => {
      btn.addEventListener('click', () => pressDigit(btn.dataset.val));
    });
    document.getElementById('pkClear').addEventListener('click', pressClear);
    document.getElementById('pkEnter').addEventListener('click', pressEnter);

    // Physical keyboard support
    document.addEventListener('keydown', e => {
      if (overlay.style.display === 'none') return;
      if (e.key >= '0' && e.key <= '9') pressDigit(e.key);
      else if (e.key === 'Backspace') pressClear();
      else if (e.key === 'Enter') pressEnter();
    });

    // Set / Change PIN link
    setPinLink.addEventListener('click', () => {
      if (locked) return;
      enterSetMode();
    });
  }

  /* ── Boot ───────────────────────────────────────── */
  init();

})();
