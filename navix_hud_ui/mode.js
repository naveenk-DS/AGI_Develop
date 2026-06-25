/* ═══════════════════════════════════════════════
   NAVIX MODE SELECTOR — mode.js
   Shows before PIN screen; user picks OFFLINE or ONLINE.
   Stores choice in sessionStorage('navix_mode').
   Dispatches 'navixModeSelected' event when done.
═══════════════════════════════════════════════ */
(function () {
  'use strict';

  const modeOverlay = document.getElementById('modeOverlay');
  const pinOverlay = document.getElementById('pinOverlay');
  const btnOffline = document.getElementById('modeOffline');
  const btnOnline = document.getElementById('modeOnline');

  function selectMode(mode) {
    sessionStorage.setItem('navix_mode', mode);

    // Animate selected card
    const card = mode === 'offline' ? btnOffline : btnOnline;
    card.classList.add('card-selected');

    setTimeout(() => {
      // Fade out mode overlay
      modeOverlay.classList.add('hiding');

      // Reveal PIN overlay
      pinOverlay.style.transition = 'opacity 0.6s ease';
      pinOverlay.style.opacity = '1';
      pinOverlay.style.pointerEvents = '';

      // Notify other modules
      document.dispatchEvent(new CustomEvent('navixModeSelected', { detail: { mode } }));

      // Remove mode overlay from layout after transition
      setTimeout(() => { modeOverlay.style.display = 'none'; }, 800);
    }, 350);
  }

  btnOffline.addEventListener('click', () => selectMode('offline'));
  btnOnline.addEventListener('click', () => selectMode('online'));

  // Keyboard shortcut: O = offline, N = online
  document.addEventListener('keydown', function onKey(e) {
    if (modeOverlay.style.display === 'none') { document.removeEventListener('keydown', onKey); return; }
    if (e.key === 'o' || e.key === 'O') selectMode('offline');
    if (e.key === 'n' || e.key === 'N') selectMode('online');
  });
})();
