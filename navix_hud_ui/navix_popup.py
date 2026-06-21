"""
NAVIX OS — JARVIS-Style Fullscreen Dashboard
Run: uv run python navix_hud_ui/navix_popup.py
ESC = close  |  — = minimize
"""
import tkinter as tk, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from center_hud import CenterHUD
from panels     import SidePanels, TopBar, BottomBar

BG   = "#000a14"
CYAN = "#00f5ff"

class NavixApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NAVIX OS")
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        SW = self.root.winfo_screenwidth()
        SH = self.root.winfo_screenheight()
        self.root.geometry(f"{SW}x{SH}+0+0")
        self.SW, self.SH = SW, SH
        self._build(SW, SH)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Map>", self._on_restore)

    def _build(self, W, H):
        TOP  = 38
        BOT  = 36
        SIDE = max(260, int(W * 0.185))
        CW   = W - 2*SIDE
        CH   = H - TOP - BOT

        # Top bar
        tf = tk.Frame(self.root, bg=BG)
        tf.place(x=0, y=0, width=W, height=TOP)
        self.topbar = TopBar(tf, W, TOP, self._minimize, self._restore, self.root.destroy)

        # Left panels
        lf = tk.Frame(self.root, bg=BG)
        lf.place(x=0, y=TOP, width=SIDE, height=CH)
        self.left = SidePanels(lf, SIDE, CH, side="left")

        # Center HUD
        cf = tk.Frame(self.root, bg=BG)
        cf.place(x=SIDE, y=TOP, width=CW, height=CH)
        self.center = CenterHUD(cf, CW, CH)

        # Right panels
        rf = tk.Frame(self.root, bg=BG)
        rf.place(x=SIDE+CW, y=TOP, width=SIDE, height=CH)
        self.right = SidePanels(rf, SIDE, CH, side="right")

        # Bottom bar
        bf = tk.Frame(self.root, bg=BG)
        bf.place(x=0, y=TOP+CH, width=W, height=BOT)
        self.bottom = BottomBar(bf, W, BOT)

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def _restore(self):
        """Restore to fullscreen."""
        self.root.deiconify()
        self.root.overrideredirect(True)
        SW = self.root.winfo_screenwidth()
        SH = self.root.winfo_screenheight()
        self.root.geometry(f"{SW}x{SH}+0+0")
        self.root.lift()
        self.root.attributes("-topmost", True)

    def _on_restore(self, e):
        self.root.overrideredirect(True)
        self.root.lift()
        self.root.attributes("-topmost", True)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    NavixApp().run()
