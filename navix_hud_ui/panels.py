"""
panels.py — Stark-style side panels, topbar, bottombar
All-blue JARVIS aesthetic. Dense data grid.
"""
import tkinter as tk
import math, time, random
from datetime import datetime

BG   = "#000a14"
PAN  = "#000d1c"
CYAN = "#00f5ff"
BLUE = "#0080ff"
LGLO = "#00bfff"
DIM  = "#001428"
PALE = "#003a5c"

def _bc(h,a):
    h=h.lstrip("#")
    r=int(int(h[0:2],16)*a); g=int(int(h[2:4],16)*a); b=int(int(h[4:6],16)*a)
    return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"

LOG_MSGS=[
    "Voice OK","Graph traversal OK","Mem write: 3 nodes","LLM response ready",
    "API 200 OK","CPU spike 78%","Cache 94%","Embed updated","Task queued",
    "Net 12ms","Model loaded","OCR complete","Agent resumed","File indexed",
]
JOBS=[("DeepMind","ML Eng","INTERVIEW"),("OpenAI","AI Res","APPLIED"),
      ("Anthropic","Sys Eng","PENDING"),("Meta AI","LLM Sci","SCREENING")]
AGENTS=[("Planner","ACTIVE"),("Browser","IDLE"),
        ("Vision","ACTIVE"),("Coder","IDLE"),("Memory","ACTIVE")]
MODELS=[("Qwen","ACTIVE","★"),("Llama","IDLE","○"),
        ("DeepSeek","IDLE","○"),("Custom","IDLE","○")]

# ════════════════════════════════════════
class MiniCanvas:
    """Tiny animated waveform / bar chart"""
    def __init__(self, parent, W=None, H=40, kind="wave"):
        self.kind=kind
        pw=parent.winfo_reqwidth() if not W else W
        self.c=tk.Canvas(parent,width=pw,height=H,bg=_bc("00f5ff",0.03),
                         highlightthickness=1,
                         highlightbackground=_bc("00f5ff",0.18))
        self.c.pack(fill="x",pady=2)
        self.W=pw; self.H=H; self.ph=random.uniform(0,6.28)
        if kind=="wave":
            self.ln=self.c.create_line(0,H//2,1,H//2,fill=CYAN,width=1)
        elif kind=="bars":
            self.bars=[self.c.create_rectangle(i*8+1,H,i*8+7,H,
                        fill=_bc("0080ff",0.8),outline="")
                       for i in range(pw//8)]

    def tick(self, amp=None):
        H=self.H
        if self.kind=="wave":
            self.ph=(self.ph+0.18)%(2*math.pi)
            amp2=amp or (6+random.random()*6)
            pts=[]
            for x in range(self.W):
                y=H//2+math.sin(x/self.W*12+self.ph)*amp2+math.sin(x/self.W*5-self.ph*0.7)*3
                pts+=[x,y]
            if len(pts)>=4:
                self.c.coords(self.ln,*pts)
        elif self.kind=="bars":
            for i,b in enumerate(self.bars):
                h=random.randint(4,H-2)
                self.c.coords(b,i*8+1,H-h,i*8+7,H)

class SmallBar:
    def __init__(self, parent, label, W):
        f=tk.Frame(parent,bg=PAN); f.pack(fill="x",pady=1)
        tk.Label(f,text=label,fg=_bc("00f5ff",0.6),bg=PAN,
                 font=("Courier",6),width=5,anchor="w").pack(side="left")
        self.c=tk.Canvas(f,width=W-72,height=7,bg=_bc("00f5ff",0.06),
                         highlightthickness=0)
        self.c.pack(side="left",padx=2)
        self.bar=self.c.create_rectangle(0,0,0,7,fill=CYAN,outline="")
        self.cw=W-72
        self.vl=tk.Label(f,text="--",fg=CYAN,bg=PAN,font=("Courier",6),width=5)
        self.vl.pack(side="left")
    def set(self,v,suf="%"):
        w=int(self.cw*v/100)
        self.c.coords(self.bar,0,0,w,7)
        self.vl.config(text=f"{v}{suf}")

def _hdr(parent, text, col=CYAN):
    f=tk.Frame(parent,bg=_bc(col.lstrip("#"),0.07))
    f.pack(fill="x",pady=(4,0))
    tk.Canvas(f,height=1,bg=col,highlightthickness=0).pack(fill="x",side="top")
    tk.Label(f,text=f"  {text}",fg=col,bg=_bc(col.lstrip("#"),0.07),
             font=("Courier",7,"bold"),anchor="w",pady=3).pack(fill="x")
    return f

def _row(parent,k,v,vc=CYAN):
    f=tk.Frame(parent,bg=PAN); f.pack(fill="x",pady=1)
    tk.Label(f,text=f" {k}",fg=_bc("00f5ff",0.5),bg=PAN,
             font=("Courier",6),width=10,anchor="w").pack(side="left")
    tk.Label(f,text=v,fg=vc,bg=PAN,font=("Courier",6)).pack(side="left")

# ════════════════════════════════════════
#  TOP BAR
# ════════════════════════════════════════
class TopBar:
    def __init__(self, parent, W, H, on_min, on_restore, on_close):
        self.c=tk.Canvas(parent,width=W,height=H,bg=BG,highlightthickness=0)
        self.c.pack(fill="both",expand=True)
        c=self.c
        c.create_line(0,H-1,W,H-1,fill=CYAN,width=1)
        c.create_line(0,H-2,W,H-2,fill=_bc("00f5ff",0.2),width=1)
        # Logo
        c.create_text(18,H//2,text="⬡",anchor="w",font=("Courier",14,"bold"),fill=CYAN)
        c.create_text(36,H//2,text="NAVIX  OS",anchor="w",
                      font=("Courier",11,"bold"),fill=CYAN)
        c.create_text(200,H//2,text="ver 3.0",anchor="w",
                      font=("Courier",7),fill=_bc("00f5ff",0.45))
        # Center status dots
        for i,(col,lbl) in enumerate([(CYAN,"AI"),(BLUE,"NET"),(LGLO,"MEM"),(CYAN,"GPU")]):
            xp=W//2-80+i*50
            c.create_oval(xp-4,H//2-4,xp+4,H//2+4,fill=col,outline="")
            c.create_text(xp+10,H//2,text=lbl,anchor="w",
                          font=("Courier",6),fill=_bc(col.lstrip("#"),0.7))
        # Clock
        self.clk=c.create_text(W-180,H//2,text="",anchor="w",
                                font=("Courier",10,"bold"),fill=CYAN)
        # ── Window controls (right side) ──
        # Minimize  —
        mb=c.create_text(W-80,H//2,text="—",anchor="center",
                         font=("Courier",11,"bold"),fill=LGLO,
                         tags="btn_min")
        c.tag_bind("btn_min","<Button-1>",lambda e: on_min())
        c.tag_bind("btn_min","<Enter>",lambda e: c.itemconfig("btn_min",fill=CYAN))
        c.tag_bind("btn_min","<Leave>",lambda e: c.itemconfig("btn_min",fill=LGLO))
        # Restore  □
        rb=c.create_text(W-50,H//2,text="□",anchor="center",
                         font=("Courier",11,"bold"),fill=LGLO,
                         tags="btn_res")
        c.tag_bind("btn_res","<Button-1>",lambda e: on_restore())
        c.tag_bind("btn_res","<Enter>",lambda e: c.itemconfig("btn_res",fill=CYAN))
        c.tag_bind("btn_res","<Leave>",lambda e: c.itemconfig("btn_res",fill=LGLO))
        # Close  ✕
        cb=c.create_text(W-18,H//2,text="✕",anchor="center",
                         font=("Courier",11,"bold"),fill=_bc("ff3b3b",0.9),
                         tags="btn_cls")
        c.tag_bind("btn_cls","<Button-1>",lambda e: on_close())
        c.tag_bind("btn_cls","<Enter>",lambda e: c.itemconfig("btn_cls",fill="#ff3b3b"))
        c.tag_bind("btn_cls","<Leave>",lambda e: c.itemconfig("btn_cls",fill=_bc("ff3b3b",0.9)))
        # Separator before controls
        c.create_line(W-100,8,W-100,H-8,fill=_bc("00f5ff",0.2),width=1)
        # Drag
        self._dx=self._dy=0
        c.bind("<ButtonPress-1>",self._p)
        c.bind("<B1-Motion>",self._d)
        self._tick()

    def _p(self,e):
        root=self.c.winfo_toplevel()
        self._dx=e.x_root-root.winfo_x()
        self._dy=e.y_root-root.winfo_y()
    def _d(self,e):
        root=self.c.winfo_toplevel()
        root.geometry(f"+{e.x_root-self._dx}+{e.y_root-self._dy}")
    def _tick(self):
        self.c.itemconfig(self.clk,
                          text=datetime.now().strftime("%H:%M:%S"))
        self.c.after(1000,self._tick)

# ════════════════════════════════════════
#  BOTTOM BAR
# ════════════════════════════════════════
class BottomBar:
    def __init__(self, parent, W, H):
        c=tk.Canvas(parent,width=W,height=H,bg=BG,highlightthickness=0)
        c.pack(fill="both",expand=True)
        c.create_line(0,0,W,0,fill=CYAN,width=1)
        c.create_line(0,1,W,1,fill=_bc("00f5ff",0.2),width=1)
        # Branding
        c.create_text(W//2,H//2,text="◈  N A V I X  A G I  —  POWERED BY NAVEEN  ◈",
                      anchor="center",font=("Courier",9,"bold"),fill=_bc("00f5ff",0.5))
        # Left scroll text (simulated)
        self.scroll_lbl=c.create_text(10,H//2,text="",anchor="w",
                                       font=("Courier",7),fill=_bc("00f5ff",0.4))
        self._msgs=["VOICE ACTIVE","AI PROCESSING","MEMORY SYNCED","GRAPH OK","API 200","LLM READY"]
        self._idx=0
        self._c=c; self._W=W; self._H=H
        self._tick()

    def _tick(self):
        msg=" ⟩ ".join(self._msgs[self._idx:]+self._msgs[:self._idx])
        self._c.itemconfig(self.scroll_lbl,text=f"  {msg}")
        self._idx=(self._idx+1)%len(self._msgs)
        self._c.after(2000,self._tick)

# ════════════════════════════════════════
#  SIDE PANELS
# ════════════════════════════════════════
class SidePanels:
    def __init__(self, parent, W, H, side="left"):
        self.W=W; self.H=H; self.side=side
        self.frame=tk.Frame(parent,bg=BG)
        self.frame.pack(fill="both",expand=True,padx=3,pady=3)
        self.waves=[]; self.bars={}
        if side=="left":
            self._build_voice()
            self._build_agents()
            self._build_memory()
            self._build_log()
        else:
            self._build_sysmon()
            self._build_llm()
            self._build_tasks()
            self._build_jobs()
        self._animate()

    # ── LEFT PANELS ───────────────────────
    def _build_voice(self):
        _hdr(self.frame,"🎙  VOICE / AUDIO")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="x",padx=2)
        # Mic row
        mf=tk.Frame(b,bg=PAN); mf.pack(fill="x",pady=3)
        self.mic=tk.Label(mf,text="  ⬤  MIC ON",fg=CYAN,bg=_bc("00f5ff",0.07),
                          font=("Courier",8,"bold"),padx=6,pady=2)
        self.mic.pack(side="left")
        self.tts=tk.Label(mf,text="TTS: READY",fg=_bc("00f5ff",0.6),bg=PAN,
                          font=("Courier",6))
        self.tts.pack(side="right",padx=4)
        # Waveform
        wc=MiniCanvas(b,W=self.W-8,H=38,kind="wave")
        self.waves.append(wc)
        # Transcript
        self.tx=tk.Text(b,width=28,height=2,bg=_bc("00f5ff",0.03),
                        fg=_bc("00f5ff",0.85),font=("Courier",7),
                        highlightthickness=0,bd=0,wrap="word")
        self.tx.pack(fill="x",padx=2,pady=2)
        self.tx.insert("end","NAVIX: How can I assist?")
        self.tx.config(state="disabled")
        _row(b,"WAKE WORD","NAVIX",CYAN)
        _row(b,"LANG","EN-IN",LGLO)

    def _build_agents(self):
        _hdr(self.frame,"🤖  AGENT MANAGER")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="x",padx=2,pady=2)
        self.agt_dots={}
        for name,status in AGENTS:
            f=tk.Frame(b,bg=PAN); f.pack(fill="x",pady=1)
            active=status=="ACTIVE"
            col=CYAN if active else _bc("00f5ff",0.3)
            dot=tk.Label(f,text="●",fg=col,bg=PAN,font=("Courier",8))
            dot.pack(side="left")
            tk.Label(f,text=f" {name}",fg=_bc("00f5ff",0.8),bg=PAN,
                     font=("Courier",7),width=9,anchor="w").pack(side="left")
            st=tk.Label(f,text=status,fg=col,bg=PAN,font=("Courier",6))
            st.pack(side="right")
            tasks=tk.Label(f,text=f"{random.randint(0,5)}T",
                           fg=_bc("00f5ff",0.4),bg=PAN,font=("Courier",6))
            tasks.pack(side="right",padx=4)
            self.agt_dots[name]=(dot,st)

    def _build_memory(self):
        _hdr(self.frame,"🧠  MEMORY SYSTEM")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="x",padx=2,pady=2)
        _row(b,"User","Naveen K")
        _row(b,"Goal","AGI Dev",LGLO)
        for lbl in ["Episodic","Semantic","Working"]:
            bar=SmallBar(b,lbl[:3],self.W-10)
            self.bars[lbl]=bar
        wc=MiniCanvas(b,W=self.W-8,H=28,kind="bars")
        self.waves.append(wc)

    def _build_log(self):
        _hdr(self.frame,"📋  EVENT LOG")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="both",expand=True,padx=2)
        self.log=tk.Text(b,bg=_bc("00f5ff",0.02),fg=_bc("00f5ff",0.75),
                         font=("Courier",6),highlightthickness=0,bd=0,wrap="word")
        self.log.pack(fill="both",expand=True,pady=2)
        for m in ["19:43:01  Voice OK","19:43:04  Graph OK","19:43:08  Mem write"]:
            self.log.insert("end",f"◆ {m}\n")
        self.log.config(state="disabled")
        self._log_t=0

    # ── RIGHT PANELS ──────────────────────
    def _build_sysmon(self):
        _hdr(self.frame,"📊  SYSTEM MONITOR")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="x",padx=2,pady=2)
        for name in ["CPU","RAM","GPU","VRAM","DISK","NET"]:
            bar=SmallBar(b,name,self.W-10)
            self.bars[name]=bar
        # CPU graph
        wc=MiniCanvas(b,W=self.W-8,H=36,kind="wave")
        self.waves.append(wc)
        # Temps
        self.tmp=tk.Label(b,text="TEMP: CPU 72°C  |  GPU 61°C",
                          fg=_bc("00f5ff",0.6),bg=PAN,font=("Courier",6))
        self.tmp.pack(anchor="w",pady=2)

    def _build_llm(self):
        _hdr(self.frame,"🧬  LLM MANAGER")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="x",padx=2,pady=2)
        self.llm_labels={}
        for name,status,star in MODELS:
            f=tk.Frame(b,bg=_bc("00f5ff",0.04) if status=="ACTIVE" else PAN)
            f.pack(fill="x",pady=1)
            col=CYAN if status=="ACTIVE" else _bc("00f5ff",0.35)
            tk.Label(f,text=f"{star} {name}",fg=col,bg=f.cget("bg"),
                     font=("Courier",7,"bold" if status=="ACTIVE" else "normal"),
                     width=10,anchor="w").pack(side="left")
            sl=tk.Label(f,text=status,fg=col,bg=f.cget("bg"),font=("Courier",6))
            sl.pack(side="right")
            self.llm_labels[name]=sl
        self.tps_lbl=tk.Label(b,text="TOKENS/SEC: --",fg=CYAN,bg=PAN,
                               font=("Courier",7,"bold"))
        self.tps_lbl.pack(anchor="w",pady=3)
        _row(b,"CTX","8192 tok",LGLO)
        _row(b,"VRAM","6.2 GB",_bc("0080ff",0.9))

    def _build_tasks(self):
        _hdr(self.frame,"⚡  TASK QUEUE")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="x",padx=2,pady=2)
        tasks=[("Voice recog","RUNNING",CYAN),("Graph trav","DONE",LGLO),
               ("Mem write","DONE",LGLO),("LLM resp","PENDING",BLUE),
               ("File scan","FAILED",_bc("ff3b3b",0.8))]
        self.task_st=[]
        for name,status,col in tasks:
            f=tk.Frame(b,bg=PAN); f.pack(fill="x",pady=1)
            tk.Label(f,text="◆",fg=col,bg=PAN,font=("Courier",6)).pack(side="left")
            tk.Label(f,text=name,fg=_bc("00f5ff",0.8),bg=PAN,
                     font=("Courier",6),width=12,anchor="w").pack(side="left")
            sl=tk.Label(f,text=status,fg=col,bg=PAN,font=("Courier",6))
            sl.pack(side="right")
            self.task_st.append(sl)
        wc=MiniCanvas(b,W=self.W-8,H=28,kind="bars")
        self.waves.append(wc)

    def _build_jobs(self):
        _hdr(self.frame,"💼  JOB TRACKER")
        b=tk.Frame(self.frame,bg=PAN); b.pack(fill="both",expand=True,padx=2,pady=2)
        for company,role,status in JOBS:
            f=tk.Frame(b,bg=PAN); f.pack(fill="x",pady=1)
            col=CYAN if status=="INTERVIEW" else _bc("00f5ff",0.5)
            tk.Label(f,text=f"◆ {company}",fg=col,bg=PAN,
                     font=("Courier",6,"bold"),width=12,anchor="w").pack(side="left")
            tk.Label(f,text=status,fg=col,bg=PAN,font=("Courier",6)).pack(side="right")

    # ── ANIMATION ────────────────────────
    def _animate(self):
        t=time.time()
        for wc in self.waves:
            wc.tick()
        if int(t)%2==0:
            for k,bar in self.bars.items():
                vals={"CPU":random.randint(20,78),"RAM":random.randint(45,82),
                      "GPU":random.randint(15,65),"VRAM":random.randint(30,75),
                      "DISK":random.randint(3,20),"NET":random.randint(5,45),
                      "Episodic":random.randint(55,95),"Semantic":random.randint(40,80),
                      "Working":random.randint(60,99)}
                if k in vals: bar.set(vals[k])
            if hasattr(self,"tps_lbl"):
                self.tps_lbl.config(text=f"TOKENS/SEC: {random.randint(28,56)}")
            if hasattr(self,"tmp"):
                self.tmp.config(text=f"TEMP: CPU {random.randint(62,85)}°C  |  GPU {random.randint(55,72)}°C")
        # Mic blink
        if hasattr(self,"mic"):
            mc=CYAN if int(t*2)%2==0 else _bc("00f5ff",0.3)
            self.mic.config(fg=mc)
        # Log push every 4s
        if hasattr(self,"log") and int(t)%4==0 and int(t)!=self._log_t:
            self._log_t=int(t)
            now=datetime.now().strftime("%H:%M:%S")
            msg=random.choice(LOG_MSGS)
            self.log.config(state="normal")
            self.log.insert("end",f"◆ {now}  {msg}\n")
            self.log.see("end")
            self.log.config(state="disabled")
        self.frame.after(60,self._animate)
