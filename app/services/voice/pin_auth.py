import tkinter as tk
from loguru import logger
import threading
import math

CORRECT_PIN    = "6777"
_authenticated = False


def ask_pin_gui() -> bool:
    """
    Shows PIN dialog as a Toplevel of the existing overlay root (main thread).
    Blocks the calling (background) thread via threading.Event until done.
    Never creates a second tk.Tk() — that crashes tkinter.
    """
    from navix_tray import _overlay

    result     = {"success": False}
    done_event = threading.Event()

    def _show():
        root = _overlay.root

        W, H = 360, 560
        dlg  = tk.Toplevel(root)
        dlg.title("")
        dlg.geometry(f"{W}x{H}")
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        dlg.configure(bg="#08091a")
        dlg.overrideredirect(True)

        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth()  - W) // 2
        y = (dlg.winfo_screenheight() - H) // 2
        dlg.geometry(f"{W}x{H}+{x}+{y}")
        dlg.grab_set()           # modal — block interaction with overlay

        pin_digits: list[str] = []
        _anim_t = [0.0]
        _after_id = [None]

        # ── Animated orb canvas ───────────────────────────────────────────────
        orb_canvas = tk.Canvas(dlg, width=W, height=150,
                               bg="#08091a", highlightthickness=0)
        orb_canvas.pack()

        def draw_orb():
            orb_canvas.delete("w")
            t  = _anim_t[0]
            cx, cy = W // 2, 75
            pal = ["#8b21e8", "#ff2d78", "#c070ff", "#6010c0"]
            for i in range(6):
                ph  = i * (math.pi / 3)
                col = pal[i % len(pal)]
                pts = []
                for j in range(121):
                    θ   = (j / 120) * 2 * math.pi
                    a   = 44 + 12 * math.sin(2 * θ + t * 0.8 + ph)
                    b   = 26 + 9  * math.sin(3 * θ + t * 0.6 + ph)
                    rot = ph + t * 0.3
                    xr, yr = a * math.cos(θ), b * math.sin(θ)
                    px = cx + xr * math.cos(rot) - yr * math.sin(rot)
                    py = cy + xr * math.sin(rot) + yr * math.cos(rot)
                    pts.extend([px, py])
                if len(pts) >= 4:
                    orb_canvas.create_line(pts, fill=col, width=1.2,
                                           smooth=True, tags="w")
            _anim_t[0] += 0.05
            _after_id[0] = dlg.after(50, draw_orb)

        draw_orb()

        # ── Header ────────────────────────────────────────────────────────────
        tk.Label(dlg, text="NAVIX AI",
                 font=("Segoe UI", 20, "bold"),
                 fg="#00d4aa", bg="#08091a").pack(pady=(4, 2))
        tk.Label(dlg, text="Enter PIN to activate",
                 font=("Segoe UI", 10),
                 fg="#4a5580", bg="#08091a").pack()

        # ── PIN dots ──────────────────────────────────────────────────────────
        dots_frame = tk.Frame(dlg, bg="#08091a")
        dots_frame.pack(pady=12)
        dots = []
        for _ in range(4):
            d = tk.Label(dots_frame, text="○",
                         font=("Segoe UI", 22),
                         fg="#2a3a4a", bg="#08091a", width=2)
            d.pack(side="left", padx=10)
            dots.append(d)

        # ── Status ────────────────────────────────────────────────────────────
        status_var = tk.StringVar(value="")
        tk.Label(dlg, textvariable=status_var,
                 font=("Segoe UI", 9),
                 fg="#ff6b6b", bg="#08091a").pack(pady=(0, 4))

        def _close(success: bool):
            result["success"] = success
            if _after_id[0]:
                dlg.after_cancel(_after_id[0])
            dlg.grab_release()
            dlg.destroy()
            done_event.set()

        def update_dots():
            for i, d in enumerate(dots):
                if i < len(pin_digits):
                    d.config(text="●", fg="#00d4aa")
                else:
                    d.config(text="○", fg="#2a3a4a")

        def press(digit):
            if len(pin_digits) < 4:
                pin_digits.append(str(digit))
                update_dots()
                status_var.set("")
                if len(pin_digits) == 4:
                    check_pin()

        def backspace():
            if pin_digits:
                pin_digits.pop()
                update_dots()
                status_var.set("")

        def check_pin():
            if "".join(pin_digits) == CORRECT_PIN:
                _close(True)
            else:
                status_var.set("Wrong PIN. Try again.")
                pin_digits.clear()
                update_dots()

        # ── Numpad ────────────────────────────────────────────────────────────
        pad = tk.Frame(dlg, bg="#08091a")
        pad.pack(pady=4)

        layout = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["⌫", "0", "✓"],
        ]

        for row in layout:
            rf = tk.Frame(pad, bg="#08091a")
            rf.pack(pady=5)
            for val in row:
                if val == "⌫":
                    cmd, fg_c, bg_c = backspace,         "#ff6b6b", "#1a0f0f"
                elif val == "✓":
                    cmd, fg_c, bg_c = check_pin,         "#00d4aa", "#0a1f1a"
                else:
                    cmd  = lambda v=val: press(v)
                    fg_c = "#dde4f0"
                    bg_c = "#0f1220"

                btn = tk.Button(
                    rf, text=val,
                    font=("Segoe UI", 16, "bold"),
                    fg=fg_c, bg=bg_c,
                    activeforeground=fg_c,
                    activebackground="#1a2040",
                    relief="flat", bd=0,
                    width=4, height=2,
                    cursor="hand2",
                    command=cmd,
                )
                btn.pack(side="left", padx=7)

        # Cancel
        tk.Button(dlg, text="Cancel",
                  font=("Segoe UI", 9), fg="#4a5580", bg="#08091a",
                  relief="flat", bd=0, cursor="hand2",
                  activebackground="#08091a",
                  command=lambda: _close(False)
                  ).pack(pady=8)

    # Schedule dialog creation on the main (tkinter) thread
    from navix_tray import _overlay
    _overlay.root.after(0, _show)

    # Block calling thread until dialog closes (max 120 s)
    done_event.wait(timeout=120)
    return result["success"]


def authenticate() -> bool:
    global _authenticated
    logger.info("Requesting PIN authentication")
    success = ask_pin_gui()
    if success:
        _authenticated = True
        logger.info("PIN authentication successful")
    else:
        logger.warning("PIN authentication failed or timed out")
    return success


def is_authenticated() -> bool:
    return _authenticated


def lock():
    global _authenticated
    _authenticated = False
    logger.info("NAVIX locked")