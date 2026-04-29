#!/usr/bin/env python3
"""
TikCut v3.1 — GUI for splitting videos for TikTok
Run: python tiktok_splitter_gui.py
Requirements: ffmpeg (winget install ffmpeg / brew install ffmpeg)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess, threading, os, json, re, sys
from pathlib import Path

# ── Colors ───────────────────────────────────────────────────────────────────
BG    = "#0a0a0f"
SURF  = "#13131a"
SURF2 = "#1c1c26"
SURF3 = "#22222f"
BRD   = "#2a2a3a"
ACC   = "#5fefb0"
ACCD  = "#3dd49a"
TXT   = "#f0f0f5"
MUT   = "#7a7a90"
DNG   = "#ff6b6b"
WRN   = "#ffb347"
OK    = "#5fefb0"
PUR   = "#b08fff"

FM  = ("Segoe UI", 10)
FB  = ("Segoe UI", 10, "bold")
FT  = ("Segoe UI", 9)
FX  = ("Segoe UI", 8)
FMO = ("Consolas", 10)
FMB = ("Consolas", 10, "bold")
F12B= ("Segoe UI", 12, "bold")


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except:
        return False

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])

def fmt_sec(s):
    s = int(s); h = s // 3600; m = (s % 3600) // 60; sec = s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"

def sanitize(n):
    return re.sub(r'[<>:"/\\|?*]', '', n).strip() or "part"

def parse_time(s):
    s = s.strip()
    if not s: return -1.0
    if re.match(r'^\d+$', s): return float(s)
    p = s.split(":")
    try:
        if len(p) == 3: return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
        if len(p) == 2: return int(p[0]) * 60 + float(p[1])
    except: pass
    return -1.0

def name_from_path(path):
    """Auto-name from file path."""
    stem = Path(path).stem
    stem = re.sub(
        r'[._]?(1080p|720p|480p|2160p|HDRip|BluRay|WEB-DL|WEBRip|x264|x265|HEVC|AAC|H264).*',
        '', stem, flags=re.IGNORECASE)
    return stem.replace('.', ' ').replace('_', ' ').strip()


# ── Widget helpers ────────────────────────────────────────────────────────────

def mk_entry(parent, var, mono=False, ph="", w=None, fg_accent=False):
    kw = dict(width=w) if w else {}
    e = tk.Entry(parent, textvariable=var,
                 font=FMO if mono else FM,
                 bg=SURF2, fg=ACC if fg_accent else TXT,
                 insertbackground=TXT,
                 relief="flat", bd=0,
                 highlightthickness=1,
                 highlightbackground=BRD,
                 highlightcolor=ACC, **kw)
    if ph:
        if not var.get():
            e.insert(0, ph); e.config(fg=MUT)
        def fi(ev, _e=e, _ph=ph):
            if _e.get() == _ph: _e.delete(0, "end"); _e.config(fg=TXT)
        def fo(ev, _e=e, _ph=ph):
            if not _e.get(): _e.insert(0, _ph); _e.config(fg=MUT)
        e.bind("<FocusIn>", fi); e.bind("<FocusOut>", fo)
    return e

def mk_btn(parent, text, cmd, accent=False, danger=False, small=False):
    bg  = ACC  if accent else SURF2
    fg  = BG   if accent else (DNG if danger else TXT)
    abg = ACCD if accent else BRD
    afg = BG   if accent else TXT
    b = tk.Button(parent, text=text, command=cmd,
                  font=FT if small else FB,
                  bg=bg, fg=fg,
                  activebackground=abg, activeforeground=afg,
                  relief="flat", bd=0,
                  padx=10, pady=5 if small else 8,
                  cursor="hand2")
    if accent:
        b.bind("<Enter>", lambda e: b.config(bg=ACCD))
        b.bind("<Leave>", lambda e: b.config(bg=ACC))
    return b

def sec_title(parent, text, **pack_kw):
    f = tk.Frame(parent, bg=parent["bg"])
    f.pack(fill="x", pady=(16, 6), **pack_kw)
    tk.Label(f, text=text.upper(), font=("Segoe UI", 9, "bold"),
             fg=MUT, bg=parent["bg"]).pack(side="left")
    tk.Frame(f, bg=BRD, height=1).pack(side="left", fill="x", expand=True, padx=(10, 0))
    return f

def divider(parent):
    tk.Frame(parent, bg=BRD, height=1).pack(fill="x", pady=8)

def stat_card(parent, val, lbl):
    f = tk.Frame(parent, bg=SURF2, padx=6, pady=10)
    f.pack(side="left", expand=True, fill="x", padx=(0, 6))
    v = tk.Label(f, text=val, font=("Consolas", 15, "bold"), bg=SURF2, fg=ACC)
    v.pack()
    tk.Label(f, text=lbl, font=FX, bg=SURF2, fg=MUT).pack()
    return v

def scrolled_canvas(parent):
    """Returns (inner_frame, canvas) for scrollable content."""
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0, bd=0)
    vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=BG)
    wid = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    return inner, canvas


# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TikCut v3.1")
        self.configure(bg=BG)
        self.geometry("940x730")
        self.minsize(800, 640)

        # ── Cut tab variables ─────────────────────────────────────────────────
        self.v_path       = tk.StringVar()
        self.v_name       = tk.StringVar()
        self.v_out        = tk.StringVar(value="tiktok_parts")
        self.v_dur        = tk.IntVar(value=150)
        self.v_reencode   = tk.BooleanVar(value=False)
        self.v_skip       = tk.BooleanVar(value=False)
        self.v_imode      = tk.StringVar(value="manual")
        self.v_isecs      = tk.IntVar(value=30)
        self._name_locked = False   # True = user typed name manually

        # ── Split tab variables ───────────────────────────────────────────────
        self.sp_path     = tk.StringVar()
        self.sp_out      = tk.StringVar(value="series_parts")
        self.sp_do_split = tk.BooleanVar(value=True)
        self.sp_dur      = tk.IntVar(value=150)
        self.sp_skip     = tk.BooleanVar(value=False)
        self.sp_isecs    = tk.IntVar(value=30)
        self.sp_reencode = tk.BooleanVar(value=False)
        self.sp_rows     = []

        self.running    = False
        self.sp_running = False

        self._build()

    # ─── UI build ────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=SURF, pady=0); hdr.pack(fill="x")
        logo = tk.Frame(hdr, bg=SURF); logo.pack(side="left", padx=20, pady=12)
        ico = tk.Frame(logo, bg=ACC, width=34, height=34)
        ico.pack(side="left"); ico.pack_propagate(False)
        tk.Label(ico, text="✂", font=("Segoe UI", 16, "bold"), bg=ACC, fg=BG).pack(expand=True)
        tk.Label(logo, text=" Tik", font=("Segoe UI", 16, "bold"), bg=SURF, fg=TXT).pack(side="left")
        tk.Label(logo, text="Cut", font=("Segoe UI", 16, "bold"), bg=SURF, fg=ACC).pack(side="left")
        tk.Label(hdr, text="v3.1", font=("Consolas", 9),
                 bg=SURF2, fg=ACC, padx=8, pady=3).pack(side="right", padx=20, pady=16)
        tk.Frame(self, bg=BRD, height=1).pack(fill="x")

        # Notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab", background=SURF2, foreground=MUT,
                        font=FT, padding=[18, 9], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", SURF)],
                  foreground=[("selected", ACC)])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        t1 = tk.Frame(self.nb, bg=BG)
        t2 = tk.Frame(self.nb, bg=BG)
        self.nb.add(t1, text="  ✂  Cut Video  ")
        self.nb.add(t2, text="  🎬  Split Episodes  ")

        self._build_cut(t1)
        self._build_split(t2)

    # ══════════════════════════════════════════════════════════════════════════
    #  CUT TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_cut(self, root):
        outer = tk.Frame(root, bg=BG); outer.pack(fill="both", expand=True)

        # Left (scrollable)
        lw = tk.Frame(outer, bg=BG); lw.pack(side="left", fill="both", expand=True)
        left, _ = scrolled_canvas(lw)
        P = dict(padx=24)

        # ── File ──
        sec_title(left, "Video File", **P)

        file_row = tk.Frame(left, bg=BG); file_row.pack(fill="x", **P)
        self._path_entry = mk_entry(file_row, self.v_path, mono=True, ph="Path to video file...")
        self._path_entry.pack(side="left", fill="x", expand=True, ipady=9)
        mk_btn(file_row, "Browse...", self._pick_video, small=True).pack(side="left", padx=(10,0))
        self._file_info = tk.Label(left, text="", font=FX, fg=MUT, bg=BG)
        self._file_info.pack(anchor="w", **P, pady=(4,0))

        # ── Settings ──
        sec_title(left, "Settings", **P)

        tk.Label(left, text="Series / Movie title", font=FT, fg=MUT, bg=BG).pack(anchor="w", **P, pady=(0,3))
        self._name_entry = mk_entry(left, self.v_name, ph="e.g. The Office S01E01")
        self._name_entry.pack(fill="x", ipady=9, **P)
        self._name_entry.bind("<Key>", lambda e: setattr(self, "_name_locked", True))

        reset_row = tk.Frame(left, bg=BG); reset_row.pack(anchor="e", **P)
        tk.Label(reset_row, text="Auto-name from file:", font=FX, fg=MUT, bg=BG).pack(side="left")
        tk.Button(reset_row, text="↺ Reset",
                  font=FX, fg=ACC, bg=BG,
                  activebackground=BG, activeforeground=ACCD,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._reset_name).pack(side="left", padx=(6,0))

        r2 = tk.Frame(left, bg=BG); r2.pack(fill="x", **P, pady=(10,0))
        lf = tk.Frame(r2, bg=BG); lf.pack(side="left", fill="x", expand=True, padx=(0,8))
        rf = tk.Frame(r2, bg=BG); rf.pack(side="left", fill="x", expand=True)

        tk.Label(lf, text="Output folder", font=FT, fg=MUT, bg=BG).pack(anchor="w", pady=(0,3))
        mk_entry(lf, self.v_out).pack(fill="x", ipady=9)

        tk.Label(rf, text="Cut mode", font=FT, fg=MUT, bg=BG).pack(anchor="w", pady=(0,3))
        mr = tk.Frame(rf, bg=BG); mr.pack(anchor="w", pady=(6,0))
        for val, lbl in [(False,"⚡ Fast"), (True,"🎯 Precise")]:
            tk.Radiobutton(mr, text=lbl, variable=self.v_reencode, value=val,
                           font=FT, bg=BG, fg=TXT, selectcolor=SURF2,
                           activebackground=BG, activeforeground=ACC).pack(side="left", padx=(0,14))

        # Slider
        self._dur_lbl = tk.Label(left, text=f"Part length: {fmt_sec(self.v_dur.get())}",
                                  font=FT, fg=MUT, bg=BG)
        self._dur_lbl.pack(anchor="w", **P, pady=(14,4))
        tk.Scale(left, variable=self.v_dur, from_=60, to=180, resolution=10,
                 orient="horizontal", bg=BG, fg=TXT, troughcolor=SURF3,
                 activebackground=ACC, highlightthickness=0, bd=0, showvalue=False,
                 command=self._on_slider).pack(fill="x", **P)
        tr = tk.Frame(left, bg=BG); tr.pack(fill="x", **P)
        for t in ["1:00","1:30","2:00","2:30","3:00"]:
            tk.Label(tr, text=t, font=FX, fg=MUT, bg=BG).pack(side="left", expand=True)

        # ── Skip intro ──
        sec_title(left, "Skip Intro", **P)
        tk.Checkbutton(left, text="Skip intro / opening at the beginning",
                       variable=self.v_skip, font=FT,
                       bg=BG, fg=TXT, selectcolor=SURF2,
                       activebackground=BG, activeforeground=ACC,
                       command=self._toggle_skip).pack(anchor="w", **P)

        self._intro_card = tk.Frame(left, bg=SURF2, pady=14, padx=14)
        self._intro_card.pack(fill="x", **P, pady=(8,0))
        mode_r = tk.Frame(self._intro_card, bg=SURF2); mode_r.pack(fill="x")
        for val, lbl in [("manual","🕐 By duration"), ("auto","🤖 Auto-detect")]:
            tk.Radiobutton(mode_r, text=lbl, variable=self.v_imode, value=val,
                           font=FT, bg=SURF2, fg=TXT, selectcolor=SURF3,
                           activebackground=SURF2, activeforeground=ACC,
                           command=self._toggle_imode).pack(side="left", padx=(0,20))

        self._manual_row = tk.Frame(self._intro_card, bg=SURF2)
        self._manual_row.pack(fill="x", pady=(10,0))
        tk.Label(self._manual_row, text="Intro length:", font=FT, fg=MUT, bg=SURF2).pack(side="left")
        tk.Spinbox(self._manual_row, from_=1, to=600, textvariable=self.v_isecs, width=5,
                   font=FM, bg=SURF3, fg=TXT, buttonbackground=SURF3,
                   relief="flat", insertbackground=TXT,
                   highlightthickness=1, highlightbackground=BRD).pack(side="left", padx=(10,0))
        tk.Label(self._manual_row, text="seconds", font=FT, fg=MUT, bg=SURF2).pack(side="left", padx=(6,0))

        self._auto_row = tk.Frame(self._intro_card, bg=SURF2)
        tk.Label(self._auto_row,
                 text="Compares frames every 2 sec.\nFinds the moment when main content begins.",
                 font=FX, fg=MUT, bg=SURF2, justify="left").pack(anchor="w")

        self._toggle_skip()
        self._toggle_imode()
        tk.Frame(left, bg=BG, height=20).pack()

        # ── Right panel ──
        tk.Frame(outer, bg=BRD, width=1).pack(side="left", fill="y")
        right = tk.Frame(outer, bg=SURF, width=310); right.pack(side="left", fill="y")
        right.pack_propagate(False)
        rp = dict(padx=18)

        tk.Label(right, text="STATS", font=("Segoe UI",9,"bold"),
                 fg=MUT, bg=SURF).pack(anchor="w", pady=(20,10), **rp)
        sf = tk.Frame(right, bg=SURF); sf.pack(fill="x", **rp)
        self._s_dur   = stat_card(sf, fmt_sec(self.v_dur.get()), "part length")
        self._s_parts = stat_card(sf, "~12", "parts*")
        self._s_skip  = stat_card(sf, "—", "intro skip")
        tk.Label(right, text="* for a 30-min video", font=FX, fg=MUT, bg=SURF)\
            .pack(anchor="w", pady=(4,0), **rp)

        divider(right)

        tk.Label(right, text="CAPTION PREVIEW", font=("Segoe UI",9,"bold"),
                 fg=MUT, bg=SURF).pack(anchor="w", pady=(0,6), **rp)
        self._caption = tk.Text(right, height=5, font=("Consolas",9),
                                bg=SURF2, fg=MUT, relief="flat", bd=0,
                                wrap="word", state="disabled", padx=10, pady=8)
        self._caption.pack(fill="x", **rp)

        divider(right)

        self._run_btn = mk_btn(right, "▶  CUT VIDEO", self._start, accent=True)
        self._run_btn.pack(fill="x", **rp, pady=(0,8))
        self._stop_btn = mk_btn(right, "■  Stop", self._stop, danger=True)
        self._stop_btn.pack(fill="x", **rp)
        self._stop_btn.config(state="disabled")

        divider(right)

        tk.Label(right, text="LOG", font=("Segoe UI",9,"bold"),
                 fg=MUT, bg=SURF).pack(anchor="w", pady=(0,6), **rp)
        self._log_box = scrolledtext.ScrolledText(
            right, font=("Consolas",9), bg=SURF2, fg=TXT,
            relief="flat", bd=0, wrap="word", state="disabled", padx=10, pady=8)
        self._log_box.pack(fill="both", expand=True, **rp, pady=(0,20))
        for t, c in [("ok",OK),("err",DNG),("warn",WRN),("dim",MUT)]:
            self._log_box.tag_config(t, foreground=c)

        # Traces — only after all widgets are created
        for v in [self.v_name, self.v_out, self.v_dur, self.v_skip, self.v_isecs, self.v_reencode]:
            v.trace_add("write", lambda *_: self._preview())
        self._preview()

    # ── Cut tab logic ─────────────────────────────────────────────────────────

    def _pick_video(self):
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video","*.mp4 *.mkv *.avi *.mov *.webm"),("All files","*.*")])
        if path: self._set_video(path)

    def _update_file_info(self, path):
        if not path:
            self._file_info.config(text="")
            return
        try:
            mb = os.path.getsize(path) / 1_048_576
            dur = get_duration(path)
            self._file_info.config(
                text=f"📹  {Path(path).name}   {mb:.1f} MB  ·  {fmt_sec(dur)}", fg=ACC)
        except:
            self._file_info.config(text=f"📹  {Path(path).name}", fg=MUT)

    def _set_video(self, path):
        self.v_path.set(path)
        self._update_file_info(path)
        if not self._name_locked:
            nm = name_from_path(path)
            self.v_name.set(nm)
            self._name_entry.config(fg=TXT)
        self._preview()

    def _reset_name(self):
        """Reset title from current file."""
        path = self.v_path.get()
        if path:
            self._name_locked = False
            nm = name_from_path(path)
            self.v_name.set(nm)
            self._name_entry.config(fg=TXT)
        else:
            self.v_name.set("")
            self._name_locked = False

    def _clear_video(self):
        self.v_path.set("")
        self.v_name.set("")
        self._name_locked = False
        self._update_file_info("")
        self._preview()

    def _on_slider(self, val):
        self._dur_lbl.config(text=f"Part length: {fmt_sec(float(val))}")
        self._preview()

    def _toggle_skip(self):
        state = "normal" if self.v_skip.get() else "disabled"
        def _s(w, st):
            try: w.config(state=st)
            except: pass
            for c in w.winfo_children(): _s(c, st)
        if hasattr(self, "_intro_card"): _s(self._intro_card, state)
        self._preview()

    def _toggle_imode(self):
        if not hasattr(self, "_manual_row"): return
        if self.v_imode.get() == "manual":
            self._auto_row.pack_forget()
            self._manual_row.pack(fill="x", pady=(10,0))
        else:
            self._manual_row.pack_forget()
            self._auto_row.pack(fill="x", pady=(10,0))

    def _preview(self):
        if not hasattr(self, "_s_dur"): return
        dur   = self.v_dur.get()
        name  = self.v_name.get().strip() or "Video"
        parts = max(1, round(1800/dur))
        self._s_dur.config(text=fmt_sec(dur))
        self._s_parts.config(text=f"~{parts}")
        if self.v_skip.get():
            if self.v_imode.get() == "manual":
                self._s_skip.config(text=f"{self.v_isecs.get()}s", fg=WRN)
            else:
                self._s_skip.config(text="auto", fg=PUR)
        else:
            self._s_skip.config(text="—", fg=MUT)
        cap = f"{name} | Part 1/{parts} 🎬\nWatch all parts on my page 👆\n\n#series #fyp #tiktok"
        self._caption.config(state="normal")
        self._caption.delete("1.0","end")
        self._caption.insert("1.0", cap)
        self._caption.config(state="disabled")

    def _log(self, msg, tag=""):
        self._log_box.config(state="normal")
        self._log_box.insert("end", msg+"\n", tag)
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _start(self):
        path = self.v_path.get().strip()
        if not path: messagebox.showwarning("No file","Please select a video file!"); return
        if not os.path.isfile(path): messagebox.showerror("File not found", path); return
        if not check_ffmpeg():
            messagebox.showerror("ffmpeg not found",
                "Windows: winget install ffmpeg\nMac: brew install ffmpeg"); return
        self.running = True
        self._run_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._log_box.config(state="normal"); self._log_box.delete("1.0","end"); self._log_box.config(state="disabled")
        threading.Thread(target=self._cut_worker, daemon=True).start()

    def _stop(self):
        self.running = False
        self._log("⚠ Stopped", "warn")

    def _cut_worker(self):
        try:
            vpath    = self.v_path.get().strip()
            name     = sanitize(self.v_name.get().strip() or name_from_path(vpath))
            out      = self.v_out.get().strip() or "tiktok_parts"
            dur      = self.v_dur.get()
            reencode = self.v_reencode.get()
            skip     = self.v_skip.get()
            mode     = self.v_imode.get()
            codec    = ["-c","copy"] if not reencode else ["-c:v","libx264","-crf","18","-c:a","aac"]

            os.makedirs(out, exist_ok=True)
            self._log(f"📹 {Path(vpath).name}", "dim")
            total = get_duration(vpath)
            self._log(f"⏱  {fmt_sec(total)}", "dim")

            cs = 0.0
            if skip:
                if mode == "manual":
                    cs = float(self.v_isecs.get())
                    self._log(f"✂ Skipping intro: first {int(cs)}s", "warn")
                else:
                    cs = self._detect_intro(vpath)
                    self._log(f"✂ Intro ends at {fmt_sec(cs)}" if cs else "⚠ Intro not detected", "warn" if cs else "dim")

            segs=[]; s=cs; n=1
            while s < total:
                e = min(s+dur, total)
                if (e-s)<30 and segs: ps,_,pn=segs[-1]; segs[-1]=(ps,e,pn)
                else: segs.append((s,e,n)); n+=1
                s=e

            tp=len(segs)
            self._log(f"✂  Parts: {tp}\n", "dim")

            for i,(ss,ee,num) in enumerate(segs,1):
                if not self.running: break
                fname = f"{name} - Part {num} of {tp}.mp4"
                op = os.path.join(out, fname)
                cmd=["ffmpeg","-y","-ss",str(ss),"-i",vpath,
                     "-t",str(ee-ss),*codec,"-avoid_negative_ts","make_zero",op]
                self._log(f"🔪 [{i}/{tp}] {fname}")
                r=subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode!=0: self._log(f"   ❌ {r.stderr[-120:]}", "err")
                else:
                    mb=os.path.getsize(op)/1_048_576
                    self._log(f"   ✅ {mb:.1f} MB", "ok")

            if self.running:
                self._log(f"\n🎉 Done! → {os.path.abspath(out)}", "ok")
        except Exception as ex:
            self._log(f"❌ {ex}", "err")
        finally:
            self.running=False
            self.after(0, lambda:(self._run_btn.config(state="normal"),
                                   self._stop_btn.config(state="disabled")))

    def _detect_intro(self, vpath):
        tmp = os.path.join(os.path.dirname(os.path.abspath(vpath)), "_tc_frames")
        os.makedirs(tmp, exist_ok=True)
        try:
            subprocess.run(["ffmpeg","-y","-i",vpath,"-vf","fps=0.5,scale=64:36",
                            "-t","120","-f","image2","-q:v","5",
                            os.path.join(tmp,"f_%04d.jpg")],
                           capture_output=True, check=True)
            frames=sorted([os.path.join(tmp,f) for f in os.listdir(tmp) if f.endswith(".jpg")])
            if len(frames)<3: return 0.0
            bs=[]
            for fp in frames:
                r=subprocess.run(["ffprobe","-v","quiet","-f","lavfi",
                                   "-i",f"movie={fp},signalstats",
                                   "-show_entries","frame_tags=lavfi.signalstats.YAVG",
                                   "-of","csv=p=0"],capture_output=True,text=True)
                try: bs.append(float(r.stdout.strip()))
                except: bs.append(0.0)
            ref=bs[0]
            for i,b in enumerate(bs[1:],1):
                if abs(b-ref)/(ref+1)>0.08: return i*2.0
            return 0.0
        except: return 0.0
        finally:
            for f in os.listdir(tmp):
                try: os.remove(os.path.join(tmp,f))
                except: pass
            try: os.rmdir(tmp)
            except: pass

    # ══════════════════════════════════════════════════════════════════════════
    #  SPLIT EPISODES TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_split(self, root):
        outer = tk.Frame(root, bg=BG); outer.pack(fill="both", expand=True)

        lw = tk.Frame(outer, bg=BG); lw.pack(side="left", fill="both", expand=True)
        left, _ = scrolled_canvas(lw)
        P = dict(padx=24)

        # File
        sec_title(left, "Video File", **P)
        fr = tk.Frame(left, bg=BG); fr.pack(fill="x", **P)
        e = mk_entry(fr, self.sp_path, mono=True, ph="Path to video file...")
        e.pack(side="left", fill="x", expand=True, ipady=9)
        mk_btn(fr, "Browse...", self._sp_pick, small=True).pack(side="left", padx=(10,0))
        self._sp_info = tk.Label(left, text="", font=FX, fg=MUT, bg=BG)
        self._sp_info.pack(anchor="w", **P, pady=(4,0))

        # Episode timestamps
        sec_title(left, "Episode Timestamps", **P)
        hint = tk.Frame(left, bg=SURF2, pady=10, padx=12); hint.pack(fill="x", **P, pady=(0,10))
        tk.Label(hint,
            text="💡  Enter when each episode ends in the file.\n"
                 "Format: HH:MM:SS  or  MM:SS  or  seconds (e.g. 2700).\n"
                 "The last episode runs to the end of the file — no timestamp needed.",
            font=FX, fg=MUT, bg=SURF2, justify="left").pack(anchor="w")

        # Table header
        hr = tk.Frame(left, bg=BG); hr.pack(fill="x", **P, pady=(0,4))
        for txt, wd in [("#",3),("Episode name",18),("Ends at",12),("",8)]:
            tk.Label(hr, text=txt, font=("Segoe UI",8,"bold"), fg=MUT, bg=BG,
                     width=wd, anchor="w").pack(side="left", padx=(0,8))

        self._sp_rows_frame = tk.Frame(left, bg=BG); self._sp_rows_frame.pack(fill="x", **P)
        self.sp_rows = []
        for _ in range(2): self._sp_add_row()

        br = tk.Frame(left, bg=BG); br.pack(fill="x", **P, pady=(8,0))
        mk_btn(br, "+ Add episode", self._sp_add_row, small=True).pack(side="left")
        mk_btn(br, "− Remove last", self._sp_remove_row, small=True).pack(side="left", padx=(8,0))

        # Cut settings
        sec_title(left, "Cut into TikTok Parts", **P)
        opt = tk.Frame(left, bg=SURF2, pady=14, padx=14); opt.pack(fill="x", **P)
        tk.Checkbutton(opt, text="Cut each episode into TikTok parts",
                       variable=self.sp_do_split, font=FT,
                       bg=SURF2, fg=TXT, selectcolor=SURF3,
                       activebackground=SURF2, activeforeground=ACC,
                       command=self._sp_toggle_opts).pack(anchor="w")

        self._sp_opt = tk.Frame(opt, bg=SURF2); self._sp_opt.pack(fill="x", pady=(12,0))
        self._sp_dur_lbl = tk.Label(self._sp_opt,
            text=f"Part length: {fmt_sec(self.sp_dur.get())}",
            font=FT, fg=MUT, bg=SURF2)
        self._sp_dur_lbl.pack(anchor="w", pady=(0,4))
        tk.Scale(self._sp_opt, variable=self.sp_dur, from_=60, to=180, resolution=10,
                 orient="horizontal", bg=SURF2, fg=TXT, troughcolor=SURF3,
                 activebackground=ACC, highlightthickness=0, bd=0, showvalue=False,
                 command=lambda v: self._sp_dur_lbl.config(
                     text=f"Part length: {fmt_sec(float(v))}")
                 ).pack(fill="x")

        cr = tk.Frame(self._sp_opt, bg=SURF2); cr.pack(fill="x", pady=(10,0))
        tk.Checkbutton(cr, text="Skip intro",
                       variable=self.sp_skip, font=FT,
                       bg=SURF2, fg=TXT, selectcolor=SURF3,
                       activebackground=SURF2, activeforeground=ACC).pack(side="left")
        tk.Spinbox(cr, from_=1, to=600, textvariable=self.sp_isecs, width=5,
                   font=FM, bg=SURF3, fg=TXT, buttonbackground=SURF3,
                   relief="flat", insertbackground=TXT,
                   highlightthickness=1, highlightbackground=BRD).pack(side="left", padx=(10,0))
        tk.Label(cr, text="sec", font=FT, fg=MUT, bg=SURF2).pack(side="left", padx=(6,0))

        er = tk.Frame(self._sp_opt, bg=SURF2); er.pack(fill="x", pady=(8,0))
        tk.Label(er, text="Mode:", font=FT, fg=MUT, bg=SURF2).pack(side="left")
        for val, lbl in [(False,"⚡ Fast"),(True,"🎯 Precise")]:
            tk.Radiobutton(er, text=lbl, variable=self.sp_reencode, value=val,
                           font=FT, bg=SURF2, fg=TXT, selectcolor=SURF3,
                           activebackground=SURF2, activeforeground=ACC).pack(side="left", padx=(12,0))

        outr = tk.Frame(left, bg=BG); outr.pack(fill="x", **P, pady=(12,0))
        tk.Label(outr, text="Output folder:", font=FT, fg=MUT, bg=BG).pack(side="left")
        mk_entry(outr, self.sp_out).pack(side="left", fill="x", expand=True, padx=(10,0), ipady=8)
        tk.Frame(left, bg=BG, height=20).pack()

        self._sp_toggle_opts()

        # Right panel
        tk.Frame(outer, bg=BRD, width=1).pack(side="left", fill="y")
        right = tk.Frame(outer, bg=SURF, width=310); right.pack(side="left", fill="y")
        right.pack_propagate(False)
        rp = dict(padx=18)

        tk.Label(right, text="SPLIT PLAN", font=("Segoe UI",9,"bold"),
                 fg=MUT, bg=SURF).pack(anchor="w", pady=(20,8), **rp)
        self._sp_preview = tk.Text(right, height=10, font=("Consolas",9),
                                    bg=SURF2, fg=MUT, relief="flat", bd=0,
                                    wrap="word", state="disabled", padx=10, pady=8)
        self._sp_preview.pack(fill="x", **rp)

        divider(right)

        self._sp_run_btn = mk_btn(right, "▶  SPLIT & CUT", self._sp_start, accent=True)
        self._sp_run_btn.pack(fill="x", **rp, pady=(0,8))
        self._sp_stop_btn = mk_btn(right, "■  Stop", self._sp_stop, danger=True)
        self._sp_stop_btn.pack(fill="x", **rp)
        self._sp_stop_btn.config(state="disabled")

        divider(right)

        tk.Label(right, text="LOG", font=("Segoe UI",9,"bold"),
                 fg=MUT, bg=SURF).pack(anchor="w", pady=(0,6), **rp)
        self._sp_log_box = scrolledtext.ScrolledText(
            right, font=("Consolas",9), bg=SURF2, fg=TXT,
            relief="flat", bd=0, wrap="word", state="disabled", padx=10, pady=8)
        self._sp_log_box.pack(fill="both", expand=True, **rp, pady=(0,20))
        for t, c in [("ok",OK),("err",DNG),("warn",WRN),("dim",MUT)]:
            self._sp_log_box.tag_config(t, foreground=c)

    # ── Split tab logic ───────────────────────────────────────────────────────

    def _sp_add_row(self):
        idx = len(self.sp_rows)+1
        rf = tk.Frame(self._sp_rows_frame, bg=SURF2, pady=8, padx=10)
        rf.pack(fill="x", pady=(0,6))
        num_lbl = tk.Label(rf, text=str(idx), font=FMB, fg=ACC, bg=SURF2, width=3)
        num_lbl.pack(side="left")
        name_v = tk.StringVar(value=f"Episode {idx}")
        ne = mk_entry(rf, name_v, w=18); ne.pack(side="left", ipady=6, padx=(6,12))
        tk.Label(rf, text="ends at:", font=FT, fg=MUT, bg=SURF2).pack(side="left")
        end_v = tk.StringVar(value="00:00:00")
        ee = mk_entry(rf, end_v, mono=True, fg_accent=True, w=10)
        ee.pack(side="left", padx=(6,0), ipady=6)
        hint_lbl = tk.Label(rf, text="", font=FX, fg="#444460", bg=SURF2)
        hint_lbl.pack(side="left", padx=(10,0))
        for v in [name_v, end_v]:
            v.trace_add("write", lambda *_: self._sp_update_preview())
        self.sp_rows.append({
            "frame":rf,"num_lbl":num_lbl,
            "name_v":name_v,"end_v":end_v,
            "end_entry":ee,"hint":hint_lbl
        })
        self._sp_relabel()
        self._sp_update_preview()

    def _sp_remove_row(self):
        if len(self.sp_rows)<=1: return
        self.sp_rows.pop()["frame"].destroy()
        self._sp_relabel(); self._sp_update_preview()

    def _sp_relabel(self):
        for i, row in enumerate(self.sp_rows):
            row["num_lbl"].config(text=str(i+1))
            is_last = (i==len(self.sp_rows)-1)
            if is_last:
                row["hint"].config(text="← to end of file")
                row["end_entry"].config(state="disabled",
                                        disabledforeground="#444460",
                                        disabledbackground=SURF3)
            else:
                row["hint"].config(text="")
                row["end_entry"].config(state="normal")

    def _sp_pick(self):
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video","*.mp4 *.mkv *.avi *.mov *.webm"),("All files","*.*")])
        if not path: return
        self.sp_path.set(path)
        try:
            d = get_duration(path)
            self._sp_info.config(text=f"⏱  {fmt_sec(d)}  ({d:.0f} sec)", fg=ACC)
        except:
            self._sp_info.config(text="⚠ Could not read file duration", fg=WRN)
        self._sp_update_preview()

    def _sp_toggle_opts(self):
        state = "normal" if self.sp_do_split.get() else "disabled"
        def _s(w, st):
            try: w.config(state=st)
            except: pass
            for c in w.winfo_children(): _s(c, st)
        if hasattr(self, "_sp_opt"): _s(self._sp_opt, state)

    def _sp_update_preview(self):
        if not hasattr(self, "_sp_preview"): return
        lines=[]; prev=0.0
        for i, row in enumerate(self.sp_rows):
            name = row["name_v"].get().strip() or f"Episode {i+1}"
            is_last = (i==len(self.sp_rows)-1)
            if is_last:
                lines += [f"🎬 {name}", f"   {fmt_sec(prev)} → end of file"]
            else:
                t = parse_time(row["end_v"].get())
                if t>0:
                    lines += [f"🎬 {name}", f"   {fmt_sec(prev)} → {fmt_sec(t)}  ({fmt_sec(t-prev)})"]
                    prev=t
                else:
                    lines.append(f"🎬 {name}  ⚠ enter end time")
        if self.sp_do_split.get():
            lines += ["", f"✂ parts of {fmt_sec(self.sp_dur.get())}"]
        txt = "\n".join(lines)
        self._sp_preview.config(state="normal")
        self._sp_preview.delete("1.0","end")
        self._sp_preview.insert("1.0", txt)
        self._sp_preview.config(state="disabled")

    def _sp_log(self, msg, tag=""):
        self._sp_log_box.config(state="normal")
        self._sp_log_box.insert("end", msg+"\n", tag)
        self._sp_log_box.see("end")
        self._sp_log_box.config(state="disabled")

    def _sp_stop(self):
        self.sp_running=False; self._sp_log("⚠ Stopped","warn")

    def _sp_start(self):
        vpath=self.sp_path.get().strip()
        if not vpath: messagebox.showwarning("No file","Please select a video file!"); return
        if not os.path.isfile(vpath): messagebox.showerror("File not found",vpath); return
        if not check_ffmpeg():
            messagebox.showerror("ffmpeg not found",
                "Windows: winget install ffmpeg\nMac: brew install ffmpeg"); return
        series=[]; prev=0.0
        for i, row in enumerate(self.sp_rows):
            name = row["name_v"].get().strip() or f"Episode {i+1}"
            is_last = (i==len(self.sp_rows)-1)
            if is_last: series.append((name,prev,None)); break
            t=parse_time(row["end_v"].get())
            if t<=0:
                messagebox.showerror("Invalid time",
                    f"Episode {i+1}: invalid time format.\nUse HH:MM:SS, MM:SS or seconds."); return
            if t<=prev:
                messagebox.showerror("Invalid time",
                    f"Episode {i+1}: {fmt_sec(t)} must be greater than {fmt_sec(prev)}"); return
            series.append((name,prev,t)); prev=t

        self.sp_running=True
        self._sp_run_btn.config(state="disabled")
        self._sp_stop_btn.config(state="normal")
        self._sp_log_box.config(state="normal"); self._sp_log_box.delete("1.0","end"); self._sp_log_box.config(state="disabled")
        threading.Thread(target=self._sp_worker,args=(vpath,series),daemon=True).start()

    def _sp_worker(self, vpath, series):
        try:
            out      = self.sp_out.get().strip() or "series_parts"
            do_split = self.sp_do_split.get()
            tik_dur  = self.sp_dur.get()
            skip_int = self.sp_skip.get()
            int_secs = self.sp_isecs.get()
            reencode = self.sp_reencode.get()
            codec    = ["-c","copy"] if not reencode else ["-c:v","libx264","-crf","18","-c:a","aac"]
            os.makedirs(out, exist_ok=True)
            total = get_duration(vpath)
            self._sp_log(f"📹 {Path(vpath).name}", "dim")
            self._sp_log(f"⏱  {fmt_sec(total)}  ·  episodes: {len(series)}\n", "dim")
            sdir = os.path.join(out,"01_episodes"); os.makedirs(sdir,exist_ok=True)
            ep_files=[]

            self._sp_log("═══ Step 1: Extracting episodes ═══","dim")
            for i,(name,start,end) in enumerate(series,1):
                if not self.sp_running: return
                ep_end = end if end is not None else total
                dur    = ep_end - start
                safe   = sanitize(name)
                fname  = f"{i:02d}. {safe}.mp4"
                fpath  = os.path.join(sdir,fname)
                self._sp_log(f"\n🔪 [{i}/{len(series)}] {name}")
                self._sp_log(f"   {fmt_sec(start)} → {fmt_sec(ep_end)}  ({fmt_sec(dur)})","dim")
                cmd=["ffmpeg","-y","-ss",str(start),"-i",vpath,
                     "-t",str(dur),*codec,"-avoid_negative_ts","make_zero",fpath]
                r=subprocess.run(cmd,capture_output=True,text=True)
                if r.returncode!=0: self._sp_log(f"   ❌ {r.stderr[-150:]}","err")
                else:
                    mb=os.path.getsize(fpath)/1_048_576
                    self._sp_log(f"   ✅ {fname}  ({mb:.1f} MB)","ok")
                    ep_files.append((name,fpath))

            if do_split and ep_files:
                tdir=os.path.join(out,"02_tiktok_parts"); os.makedirs(tdir,exist_ok=True)
                self._sp_log("\n═══ Step 2: Cutting TikTok parts ═══","dim")
                for ep_name,ep_path in ep_files:
                    if not self.sp_running: return
                    self._sp_log(f"\n📺 {ep_name}","dim")
                    etotal=get_duration(ep_path)
                    cs=float(int_secs) if skip_int else 0.0
                    if skip_int: self._sp_log(f"   ✂ Skipping intro: {int_secs}s","warn")
                    segs=[]; s=cs; n=1
                    while s<etotal:
                        e=min(s+tik_dur,etotal)
                        if (e-s)<30 and segs: ps,_,pn=segs[-1]; segs[-1]=(ps,e,pn)
                        else: segs.append((s,e,n)); n+=1
                        s=e
                    tp=len(segs); self._sp_log(f"   Parts: {tp}","dim")
                    ep_out=os.path.join(tdir,sanitize(ep_name)); os.makedirs(ep_out,exist_ok=True)
                    for ss,ee,num in segs:
                        if not self.sp_running: return
                        pname=f"{sanitize(ep_name)} - Part {num} of {tp}.mp4"
                        pp=os.path.join(ep_out,pname)
                        cmd=["ffmpeg","-y","-ss",str(ss),"-i",ep_path,
                             "-t",str(ee-ss),*codec,"-avoid_negative_ts","make_zero",pp]
                        r=subprocess.run(cmd,capture_output=True,text=True)
                        if r.returncode!=0: self._sp_log(f"   ❌ Part {num}","err")
                        else:
                            mb=os.path.getsize(pp)/1_048_576
                            self._sp_log(f"   ✅ Part {num}/{tp}  {mb:.1f} MB","ok")

            if self.sp_running:
                self._sp_log(f"\n🎉 Done! → {os.path.abspath(out)}","ok")
                self._sp_log(f"   📁 Episodes: {sdir}","dim")
                if do_split: self._sp_log(f"   📁 TikTok parts: {os.path.join(out,'02_tiktok_parts')}","dim")
        except Exception as ex:
            import traceback
            self._sp_log(f"❌ {ex}\n{traceback.format_exc()}","err")
        finally:
            self.sp_running=False
            self.after(0,lambda:(self._sp_run_btn.config(state="normal"),
                                  self._sp_stop_btn.config(state="disabled")))


if __name__ == "__main__":
    app = App()
    app.mainloop()
