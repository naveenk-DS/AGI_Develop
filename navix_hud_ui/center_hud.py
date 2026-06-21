"""
center_hud.py — Arc Reactor HUD (JARVIS / Stark style)
All canvas items PRE-CREATED → no memory leak
"""
import tkinter as tk
import math, time, random

BG   = "#000a14"
CYAN = "#00f5ff"
BLUE = "#0080ff"
LGLO = "#00bfff"
DIM  = "#001830"
PALE = "#003a5c"

def _bc(h, a):
    h = h.lstrip("#")
    r=int(int(h[0:2],16)*a); g=int(int(h[2:4],16)*a); b=int(int(h[4:6],16)*a)
    return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"

STATUSES = ["ONLINE","LISTENING","PROCESSING","ANALYZING","ACTIVE","IDLE"]

class CenterHUD:
    def __init__(self, parent, W, H):
        self.W=W; self.H=H
        self.cx=W//2; self.cy=H//2
        self.R = min(W,H)//2 - 16

        self.cv = tk.Canvas(parent, width=W, height=H, bg=BG,
                            highlightthickness=0)
        self.cv.pack(fill="both", expand=True)

        # Animation state
        self.gear_a   = 0.0
        self.ring_a   = [0.0]*8
        self.sweep_a  = 0.0
        self.glow_a   = 0.0
        self.tri_a    = 0.0
        self.status_i = 0
        self._last_s  = -1
        self.wave_ph  = 0.0

        self._draw_bg()
        self._make_rings()
        self._make_gear()
        self._make_reactor()
        self._make_sweep()
        self._make_labels()
        self._animate()

    # ── STATIC BACKGROUND ─────────────────
    def _draw_bg(self):
        cv=self.cv; cx=self.cx; cy=self.cy; R=self.R
        # Radial background glow gradient
        for i in range(12):
            r = int(R*(1.2 - i*0.05))
            a = 0.02 + i*0.005
            col = _bc("001828", min(a,0.15))
            cv.create_oval(cx-r,cy-r,cx+r,cy+r, fill=col, outline="")
        # Outer circle border
        cv.create_oval(cx-R,cy-R,cx+R,cy+R,
                       outline=_bc("00f5ff",0.5), width=2)
        # Inner guide circle
        r2 = int(R*0.52)
        cv.create_oval(cx-r2,cy-r2,cx+r2,cy+r2,
                       outline=_bc("00f5ff",0.15), width=1)
        # Cross hairs
        for ang_d in [0,90,180,270]:
            a = math.radians(ang_d)
            x1=cx+math.cos(a)*(R+8); y1=cy+math.sin(a)*(R+8)
            x2=cx+math.cos(a)*(R+22); y2=cy+math.sin(a)*(R+22)
            cv.create_line(x1,y1,x2,y2,fill=CYAN,width=2)
            # Label
            lx=cx+math.cos(a)*(R+34); ly=cy+math.sin(a)*(R+34)
            lbl=["E","S","W","N"][ang_d//90]
            cv.create_text(lx,ly,text=lbl,fill=_bc("00f5ff",0.6),
                          font=("Courier",8,"bold"))

    # ── PRE-CREATE RINGS ──────────────────
    def _make_rings(self):
        cv=self.cv; cx=self.cx; cy=self.cy; R=self.R
        # (radius_factor, speed, n_dashes, color, width)
        RDEFS = [
            (0.90,  0.010, 60, CYAN,  1),
            (0.83, -0.016, 48, LGLO,  2),
            (0.76,  0.022, 36, CYAN,  1),
            (0.69, -0.028, 24, BLUE,  2),
            (0.62,  0.034,  0, CYAN,  1),
            (0.55, -0.040, 18, LGLO,  2),
            (0.47,  0.050,  0, CYAN,  2),
            (0.40, -0.060, 12, BLUE,  3),
        ]
        self.rings = []
        for i,(rf,spd,nd,col,lw) in enumerate(RDEFS):
            r=int(R*rf)
            data={"rf":rf,"spd":spd,"nd":nd,"col":col,"lw":lw,"ang":i*0.4,"arcs":[],"solid":nd==0}
            if nd==0:
                item=cv.create_oval(cx-r,cy-r,cx+r,cy+r,outline=col,width=lw)
                data["arcs"]=[item]
            else:
                step=360/nd; ext=step*0.50
                data["step"]=step; data["ext"]=ext
                for j in range(nd):
                    a=cv.create_arc(cx-r,cy-r,cx+r,cy+r,
                                    start=j*step,extent=ext,
                                    style="arc",outline=col,width=lw)
                    data["arcs"].append(a)
            self.rings.append(data)

    # ── GEAR TEETH ───────────────────────
    def _make_gear(self):
        cv=self.cv; cx=self.cx; cy=self.cy; R=self.R
        N=72
        self.teeth=[]
        for i in range(N):
            ln=cv.create_line(0,0,1,1,
                              fill=CYAN if i%2==0 else _bc("00f5ff",0.4),
                              width=2 if i%6==0 else 1)
            self.teeth.append(ln)
        self.gear_N=N
        self.gear_R_in=R-20
        self.gear_R_out=R-2

    # ── REACTOR CORE ─────────────────────
    def _make_reactor(self):
        cv=self.cv; cx=self.cx; cy=self.cy; R=self.R
        r = int(R*0.32)

        # Outer reactor ring
        cv.create_oval(cx-r,cy-r,cx+r,cy+r,
                       outline=CYAN, width=3)

        # Inner glow layers (animated)
        self.glow_layers=[]
        for i,(radius,alpha) in enumerate([(r-4,0.12),(r-12,0.20),(r-20,0.30),(r-28,0.40),(r-36,0.50)]):
            if radius>0:
                col=_bc("0090ff",alpha)
                item=cv.create_oval(cx-radius,cy-radius,cx+radius,cy+radius,
                                    fill=col, outline="")
                self.glow_layers.append((item, radius))

        # Triangle (arc reactor symbol) — pointing UP
        tr = int(r*0.72)
        pts = self._tri_pts(cx, cy, tr, -90)
        self.tri_outer = cv.create_polygon(*pts,
            fill=_bc("0060ff",0.25), outline=CYAN, width=2)

        # Inner triangle
        tr2 = int(r*0.44)
        pts2 = self._tri_pts(cx, cy, tr2, -90)
        self.tri_inner = cv.create_polygon(*pts2,
            fill=_bc("00a0ff",0.5), outline=LGLO, width=2)

        # Center dot
        self.center_dot = cv.create_oval(cx-6,cy-6,cx+6,cy+6,
                                          fill=CYAN, outline=CYAN)

        # Triangle glow text
        self.tri_lbl = cv.create_text(cx,cy,text="AI",
                                       font=("Courier",9,"bold"),fill=BG)

    @staticmethod
    def _tri_pts(cx, cy, r, offset_deg):
        pts=[]
        for i in range(3):
            ang=math.radians(offset_deg + i*120)
            pts+=[cx+math.cos(ang)*r, cy+math.sin(ang)*r]
        return pts

    # ── SWEEP ARM ────────────────────────
    def _make_sweep(self):
        cv=self.cv; cx=self.cx; cy=self.cy; R=self.R
        SR=int(R*0.88)
        self.sweep=[cv.create_line(cx,cy,cx,cy,
                                    fill=_bc("00f5ff",a),width=w)
                    for a,w in [(0.8,2),(0.4,1),(0.15,1)]]
        self.sweep_R=SR

    # ── LABELS ───────────────────────────
    def _make_labels(self):
        cv=self.cv; cx=self.cx; cy=self.cy; R=self.R
        # Top: NAVIX OS
        self.lbl_title=cv.create_text(cx,cy-R+30,
                                       text="N A V I X  O S",
                                       font=("Courier",11,"bold"),fill=CYAN)
        # Status
        self.lbl_status=cv.create_text(cx,cy+R-30,
                                        text="● ONLINE",
                                        font=("Courier",9,"bold"),fill=CYAN)
        # Model
        self.lbl_model=cv.create_text(cx,cy+R-14,
                                       text="MODEL: NAVIX-v3  |  TASK: ACTIVE",
                                       font=("Courier",7),fill=_bc("00f5ff",0.55))
        # Side readouts
        self.lbl_L=cv.create_text(cx-R+10,cy,text="",
                                   anchor="w",font=("Courier",7),
                                   fill=_bc("00f5ff",0.7))
        self.lbl_R=cv.create_text(cx+R-10,cy,text="",
                                   anchor="e",font=("Courier",7),
                                   fill=_bc("00f5ff",0.7))
        # Wave readout strip
        self.wave_c=cv.create_rectangle(cx-R//2,cy+R-58,cx+R//2,cy+R-38,
                                         outline=_bc("00f5ff",0.2),
                                         fill=_bc("001020",0.9))

    # ── ANIMATE ──────────────────────────
    def _animate(self):
        self._frame()
        self.cv.after(30, self._animate)

    def _frame(self):
        cx=self.cx; cy=self.cy; R=self.R; t=time.time()

        # ── Gear teeth ──
        self.gear_a=(self.gear_a+0.006)%(2*math.pi)
        for i,ln in enumerate(self.teeth):
            ang=(i/self.gear_N*2*math.pi)+self.gear_a
            r_in=self.gear_R_in; r_out=self.gear_R_out
            if i%2==0: r_out=R-2
            else: r_out=R-10
            x1=cx+math.cos(ang)*r_in; y1=cy+math.sin(ang)*r_in
            x2=cx+math.cos(ang)*r_out; y2=cy+math.sin(ang)*r_out
            self.cv.coords(ln,x1,y1,x2,y2)

        # ── Rings ──
        for ring in self.rings:
            ring["ang"]=(ring["ang"]+ring["spd"])%(2*math.pi)
            if not ring["solid"]:
                deg=math.degrees(ring["ang"])
                for j,arc_id in enumerate(ring["arcs"]):
                    ns=(j*ring["step"]+deg)%360
                    self.cv.itemconfig(arc_id,start=ns)

        # ── Sweep ──
        self.sweep_a=(self.sweep_a+0.05)%(2*math.pi)
        SR=self.sweep_R
        for k,(ln,off) in enumerate(zip(self.sweep,
                                         [0,-0.08,-0.16])):
            a=self.sweep_a+off
            ex=cx+math.cos(a)*SR; ey=cy+math.sin(a)*SR
            self.cv.coords(ln,cx,cy,ex,ey)

        # ── Reactor glow pulse ──
        self.glow_a=(self.glow_a+0.07)%(2*math.pi)
        pulse=math.sin(self.glow_a)
        for item,base_r in self.glow_layers:
            rr=base_r+pulse*4
            self.cv.coords(item,cx-rr,cy-rr,cx+rr,cy+rr)

        # ── Triangle glow ──
        self.tri_a=(self.tri_a+0.04)%(2*math.pi)
        gv=0.3+0.25*math.sin(self.tri_a)
        self.cv.itemconfig(self.tri_inner,fill=_bc("0090ff",gv))

        # ── Center dot blink ──
        dot_col=CYAN if int(t*3)%2==0 else _bc("00f5ff",0.3)
        self.cv.itemconfig(self.center_dot,fill=dot_col,outline=dot_col)

        # ── Status ──
        blink=CYAN if int(t*2)%2==0 else _bc("00f5ff",0.2)
        self.cv.itemconfig(self.lbl_status,fill=blink)

        # ── Cycle readouts every 2s ──
        sec=int(t)
        if sec!=self._last_s and sec%2==0:
            self._last_s=sec
            self.status_i=(self.status_i+1)%len(STATUSES)
            self.cv.itemconfig(self.lbl_status,
                               text=f"● {STATUSES[self.status_i]}")
            self.cv.itemconfig(self.lbl_L,
                text=f"CPU {random.randint(20,75)}%\nRAM {random.randint(40,80)}%\nGPU {random.randint(10,60)}%")
            self.cv.itemconfig(self.lbl_R,
                text=f"TPS {random.randint(28,54)}\nLAT {random.randint(8,25)}ms\nPKT {random.randint(100,999)}")
