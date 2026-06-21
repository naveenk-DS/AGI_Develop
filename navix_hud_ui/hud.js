/* ───────────────────────────────────────────
   NAVIX HUD — JavaScript Engine
─────────────────────────────────────────── */

// ── CLOCK ──
function updateClock() {
  const now = new Date();
  const h = String(now.getHours()).padStart(2, '0');
  const m = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  document.getElementById('clock').textContent = `${h}:${m}:${s}`;
}
setInterval(updateClock, 1000);
updateClock();

// ── SESSION TIMER ──
let sessionStart = Date.now();
function updateSession() {
  const elapsed = Math.floor((Date.now() - sessionStart) / 1000);
  const hh = String(Math.floor(elapsed / 3600)).padStart(2, '0');
  const mm = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
  const ss = String(elapsed % 60).padStart(2, '0');
  document.getElementById('session-val').textContent = `${hh}:${mm}:${ss}`;
}
setInterval(updateSession, 1000);

// ── RING CANVAS ──
const ringCanvas = document.getElementById('ringCanvas');
const rCtx = ringCanvas.getContext('2d');
const CX = ringCanvas.width / 2;
const CY = ringCanvas.height / 2;

const rings = [
  { r: 240, speed: 0.003, dashes: 48, w: 1.5, color: '#00f5ff', alpha: 0.8, angle: 0 },
  { r: 215, speed: -0.005, dashes: 36, w: 2, color: '#00f5ff', alpha: 0.6, angle: Math.PI / 6 },
  { r: 185, speed: 0.007, dashes: 0, w: 1, color: '#00f5ff', alpha: 0.3, angle: 0 },
  { r: 165, speed: -0.009, dashes: 24, w: 2.5, color: '#ff9800', alpha: 0.7, angle: 0 },
  { r: 145, speed: 0.012, dashes: 0, w: 1, color: '#ff9800', alpha: 0.2, angle: 0 },
  { r: 125, speed: -0.015, dashes: 60, w: 1, color: '#00f5ff', alpha: 0.5, angle: Math.PI / 4 },
  { r: 105, speed: 0.02, dashes: 12, w: 3, color: '#ff9800', alpha: 0.9, angle: 0 },
  { r: 80, speed: -0.025, dashes: 8, w: 2, color: '#00ff88', alpha: 0.6, angle: 0 },
  { r: 58, speed: 0.03, dashes: 0, w: 4, color: '#00f5ff', alpha: 0.9, angle: 0 },
];

// Ticks on outer ring
const TICK_COUNT = 72;

// Spiral arm data
let spiralPhase = 0;

function drawRings(ts) {
  rCtx.clearRect(0, 0, ringCanvas.width, ringCanvas.height);

  // ── tick marks outer ──
  rCtx.save();
  rCtx.translate(CX, CY);
  for (let i = 0; i < TICK_COUNT; i++) {
    const angle = (i / TICK_COUNT) * Math.PI * 2;
    const inner = 238; const outer = i % 6 === 0 ? 248 : 243;
    const lw = i % 6 === 0 ? 2 : 1;
    const alpha = i % 6 === 0 ? 1 : 0.4;
    rCtx.strokeStyle = `rgba(0,245,255,${alpha})`;
    rCtx.lineWidth = lw;
    rCtx.shadowColor = '#00f5ff';
    rCtx.shadowBlur = lw === 2 ? 6 : 2;
    rCtx.beginPath();
    rCtx.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner);
    rCtx.lineTo(Math.cos(angle) * outer, Math.sin(angle) * outer);
    rCtx.stroke();
  }
  rCtx.restore();

  // ── Draw rings ──
  rings.forEach(ring => {
    ring.angle += ring.speed;
    rCtx.save();
    rCtx.translate(CX, CY);
    rCtx.rotate(ring.angle);
    rCtx.strokeStyle = ring.color;
    rCtx.globalAlpha = ring.alpha;
    rCtx.lineWidth = ring.w;
    rCtx.shadowColor = ring.color;
    rCtx.shadowBlur = 10;
    if (ring.dashes > 0) {
      const dash = (2 * Math.PI * ring.r) / (ring.dashes * 2);
      rCtx.setLineDash([dash * 0.6, dash * 1.4]);
    } else {
      rCtx.setLineDash([]);
    }
    rCtx.beginPath();
    rCtx.arc(0, 0, ring.r, 0, Math.PI * 2);
    rCtx.stroke();
    rCtx.restore();
  });

  // ── Spiral sweep arm ──
  spiralPhase += 0.015;
  rCtx.save();
  rCtx.translate(CX, CY);
  const grad = rCtx.createConicalGradient
    ? null  // canvas doesn't have conical gradient natively; skip
    : null;

  // Draw sweep line
  rCtx.rotate(spiralPhase);
  rCtx.globalAlpha = 0.35;
  const swGrad = rCtx.createLinearGradient(0, 0, 240, 0);
  swGrad.addColorStop(0, 'rgba(0,245,255,0.9)');
  swGrad.addColorStop(1, 'rgba(0,245,255,0)');
  rCtx.strokeStyle = swGrad;
  rCtx.lineWidth = 2;
  rCtx.shadowBlur = 0;
  rCtx.setLineDash([]);
  rCtx.beginPath();
  rCtx.moveTo(0, 0);
  rCtx.lineTo(240, 0);
  rCtx.stroke();
  rCtx.restore();

  // ── Center glow ──
  rCtx.save();
  rCtx.translate(CX, CY);
  const glowGrad = rCtx.createRadialGradient(0, 0, 0, 0, 0, 55);
  glowGrad.addColorStop(0, 'rgba(0,245,255,0.15)');
  glowGrad.addColorStop(0.5, 'rgba(0,245,255,0.05)');
  glowGrad.addColorStop(1, 'rgba(0,245,255,0)');
  rCtx.fillStyle = glowGrad;
  rCtx.beginPath();
  rCtx.arc(0, 0, 55, 0, Math.PI * 2);
  rCtx.fill();
  rCtx.restore();

  requestAnimationFrame(drawRings);
}
requestAnimationFrame(drawRings);

// ── AUDIO WAVEFORM (simulated) ──
const waveCanvas = document.getElementById('waveCanvas');
const wCtx = waveCanvas.getContext('2d');
let wavePhase = 0;
let waveAmplitude = 8;

function drawWave() {
  wCtx.clearRect(0, 0, waveCanvas.width, waveCanvas.height);
  const W = waveCanvas.width;
  const H = waveCanvas.height;
  const cx = H / 2;

  // Noise amplitude that ebbs and flows
  waveAmplitude = 6 + Math.sin(wavePhase * 0.3) * 4 + Math.random() * 2;

  wCtx.strokeStyle = '#00f5ff';
  wCtx.lineWidth = 1.5;
  wCtx.shadowColor = '#00f5ff';
  wCtx.shadowBlur = 6;
  wCtx.beginPath();
  for (let x = 0; x < W; x++) {
    const t = x / W;
    const y = cx
      + Math.sin(t * 12 + wavePhase) * waveAmplitude
      + Math.sin(t * 7 - wavePhase * 1.3) * (waveAmplitude * 0.5)
      + (Math.random() - 0.5) * 1.5;
    x === 0 ? wCtx.moveTo(x, y) : wCtx.lineTo(x, y);
  }
  wCtx.stroke();
  wavePhase += 0.12;
  requestAnimationFrame(drawWave);
}
drawWave();

// ── DYNAMIC STATS ──
function randBetween(a, b) { return Math.floor(Math.random() * (b - a + 1)) + a; }

function animateBar(id, valId, newW, suffix) {
  const bar = document.getElementById(id);
  const val = document.getElementById(valId);
  if (bar) { bar.style.width = newW + '%'; }
  if (val) { val.textContent = newW + (suffix || '%'); }
}

function updateStats() {
  const temp = randBetween(60, 88);
  animateBar('bar-temp', 'val-temp', temp, '°C');
  const mem = randBetween(40, 80);
  animateBar('bar-mem', 'val-mem', mem, '%');
  const cpu = randBetween(20, 70);
  animateBar('bar-cpu', 'val-cpu', cpu, '%');
  const net = randBetween(75, 98);
  animateBar('bar-net', 'val-net', net, '%');

  // Metric panel
  document.getElementById('iq-val').textContent = (95 + Math.random() * 5).toFixed(1);
  document.getElementById('conf-val').textContent = randBetween(90, 99) + '%';
  document.getElementById('lang-val').textContent = randBetween(10, 14);

  // Strip
  document.getElementById('freq-val').textContent = (2.3 + Math.random() * 0.4).toFixed(1) + ' GHz';
  document.getElementById('lat-val').textContent = randBetween(8, 22) + 'ms';
  document.getElementById('pkt-val').textContent = (parseInt(document.getElementById('pkt-val').textContent.replace(',', '')) + randBetween(10, 60)).toLocaleString();
}
setInterval(updateStats, 2000);

// ── LOG FEED ──
const logMessages = [
  'Voice command received',
  'Graph node traversed',
  'Memory context loaded',
  'LLM response generated',
  'Persona matrix stable',
  'Context window: 8192 tokens',
  'Emotion state: neutral',
  'Task queued: ID-' + Math.floor(Math.random() * 9999),
  'Cache hit ratio: 94%',
  'Embedding updated',
  'Anomaly scan: clear',
  'API call: 200 OK',
];

function pushLog() {
  const feed = document.getElementById('logFeed');
  const now = new Date();
  const ts = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
  const msg = logMessages[Math.floor(Math.random() * logMessages.length)];
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `<span class="log-time">${ts}</span> ${msg}`;
  feed.appendChild(entry);
  if (feed.children.length > 12) feed.removeChild(feed.firstChild);
  feed.scrollTop = feed.scrollHeight;
}
setInterval(pushLog, 2500);

// ── ORB STATUS ──
const orbStatuses = ['◈ ONLINE', '◈ PROCESSING', '◈ LISTENING', '◈ THINKING', '◈ ACTIVE'];
function cycleOrbStatus() {
  const el = document.getElementById('orbStatus');
  el.style.opacity = '0';
  setTimeout(() => {
    el.textContent = orbStatuses[Math.floor(Math.random() * orbStatuses.length)];
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '1';
  }, 300);
}
setInterval(cycleOrbStatus, 4000);
