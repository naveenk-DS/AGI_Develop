import tkinter as tk
import threading
import time
import math
import queue
from loguru import logger

# ── Thread-safe queues ────────────────────────────────────────────────────────
_state_queue = queue.Queue()
_chat_queue  = queue.Queue()
_overlay: "NAVIXOverlay | None" = None

# ── Public API (called from ANY thread) ───────────────────────────────────────

def start_tray() -> "NAVIXOverlay":
    global _overlay
    _overlay = NAVIXOverlay()
    return _overlay

def set_tray_state(state: str):
    _state_queue.put(state)

def add_chat_message(sender: str, text: str):
    _chat_queue.put((sender, text))


# ── Design tokens ─────────────────────────────────────────────────────────────
BG          = "#000000"   # transparent key colour — Windows will make this see-through
HEADER_BG   = "#000000"
ACCENT      = "#00d4aa"

PALETTES = {
    "sleeping":  ["#1e6655", "#2a9a7e", "#248060", "#166045"],
    "listening": ["#ff2d78", "#cc1155", "#ff6aaa", "#ff4499"],
    "active":    ["#8b21e8", "#6010c0", "#c070ff", "#a040ff"],
    "talking":   ["#00d4aa", "#00aa88", "#40ffdd", "#00ffbb"],
}

STATUS_TEXT = {
    "sleeping":  ("●  Sleeping",   "#3a4570"),
    "listening": ("◉  Listening…", "#ff2d78"),
    "active":    ("◎  Thinking…",  "#a040ff"),
    "talking":   ("◉  Speaking…",  "#00d4aa"),
}


class NAVIXOverlay:
    W, H = 240, 240   # just the orb — no panel behind it

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 1.0)          # fully opaque canvas; transparency via key
        self.root.configure(bg=BG)                   # BG = #000000 → transparent on Windows
        self.root.attributes("-transparentcolor", BG) # make black pixels see-through

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = sw - self.W - 32
        y  = (sh - self.H) // 2
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

        self.state  = "sleeping"
        self._t     = 0.0
        self._dx    = 0
        self._dy    = 0

        self._build_ui()
        self._update_loop()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        r = self.root

        # Orb canvas — full window, black bg (transparent key)
        self.orb = tk.Canvas(r, width=self.W, height=self.H,
                              bg=BG, highlightthickness=0)
        self.orb.pack()

        # Status label drawn on canvas (transparent friendly)
        self.status_var = tk.StringVar(value="●  Sleeping")
        self.status_lbl = tk.Label(r, textvariable=self.status_var,
                                   font=("Segoe UI", 9, "bold"),
                                   fg="#3a4570", bg=BG)
        # Place status at bottom of orb canvas
        self.orb.create_window(self.W // 2, self.H - 22,
                               window=self.status_lbl, anchor="center")

        # Drag the whole orb
        self.orb.bind("<Button-1>",  self._start_drag)
        self.orb.bind("<B1-Motion>", self._drag)

        # Right-click to hide
        self.orb.bind("<Button-3>", lambda e: r.withdraw())

        # Dummy chat internals so _add_bubble doesn't crash
        self.chat_canvas  = None
        self.chat_inner   = None
        self._cwin        = None

    # ── Chat bubbles ── (hidden in transparent mode; kept for API compatibility)

    def _add_bubble(self, sender: str, text: str):
        pass  # chat panel hidden — overlay is transparent orb only

    # ── Orb animation ─────────────────────────────────────────────────────────

    def _draw_orb(self):
        c  = self.orb
        c.delete("w")
        W, H   = self.W, self.H
        cx, cy = W // 2, H // 2 - 12
        t      = self._t
        pal    = PALETTES.get(self.state, PALETTES["sleeping"])
        speed  = 0.6 if self.state == "sleeping" else 1.4

        # Soft glow ring
        gr = 72 + 7 * math.sin(t * speed)
        c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                      fill="", outline=pal[0], width=1, tags="w")

        # 8 flowing Lissajous curves
        for i in range(8):
            base_phase = i * (math.pi / 4)
            color      = pal[i % len(pal)]
            pts        = []
            N          = 200
            for j in range(N + 1):
                θ = (j / N) * 2 * math.pi
                a = 65 + 18 * math.sin(2 * θ + t * speed + base_phase)
                b = 42 + 12 * math.sin(3 * θ + t * speed * 0.7 + base_phase)
                rot = base_phase + t * speed * 0.35
                xr  = a * math.cos(θ)
                yr  = b * math.sin(θ)
                x   = cx + xr * math.cos(rot) - yr * math.sin(rot)
                y   = cy + xr * math.sin(rot) + yr * math.cos(rot)
                pts.extend([x, y])
            if len(pts) >= 4:
                c.create_line(pts, fill=color, width=1.4,
                              smooth=True, tags="w")

        # Centre dot
        dot_r = 4 + 2 * math.sin(t * 2)
        c.create_oval(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
                      fill=pal[-1], outline="", tags="w")

    # ── State application ─────────────────────────────────────────────────────

    def _apply_state(self, state: str):
        self.state = state
        text, color = STATUS_TEXT.get(state, ("●  Sleeping", "#3a4570"))
        self.status_var.set(text)
        self.status_lbl.configure(fg=color, bg=BG)
        # Keep alpha at 1.0 — transparency handled by -transparentcolor

    # ── Update loop (runs every 50 ms in main thread) ─────────────────────────

    def _update_loop(self):
        # Drain state queue
        while not _state_queue.empty():
            self._apply_state(_state_queue.get_nowait())

        # Drain chat queue
        while not _chat_queue.empty():
            sender, text = _chat_queue.get_nowait()
            self._add_bubble(sender, text)

        # Animate
        self._t += 0.05
        self._draw_orb()

        self.root.after(50, self._update_loop)

    # ── Drag (click-drag the orb to reposition) ───────────────────────────────

    def _start_drag(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()