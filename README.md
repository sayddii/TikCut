<div align="center">

<br/>

# ✂ TikCut

**Split any video into TikTok-ready parts in seconds.**  
No browser, no cloud, no subscription — runs 100% locally.

[![Python](https://img.shields.io/badge/Python-3.7%2B-5fefb0?style=flat-square&logo=python&logoColor=white&labelColor=13131a)](https://python.org)
[![ffmpeg](https://img.shields.io/badge/ffmpeg-required-5fefb0?style=flat-square&logo=ffmpeg&logoColor=white&labelColor=13131a)](https://ffmpeg.org)
[![Platform](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-5fefb0?style=flat-square&labelColor=13131a)](.)
[![License](https://img.shields.io/badge/License-MIT-5fefb0?style=flat-square&labelColor=13131a)](LICENSE)

<br/>

> Drop a movie or TV episode → set part length → hit Cut → done.  
> Files come out named `The Office S01E01 - Part 1 of 6.mp4` and ready to upload.

<br/>

</div>

---

## What it does

TikCut is a desktop GUI app that chops up long videos into short clips for TikTok. You pick the file, tweak a few settings, and the app does the rest — no command line needed.

Everything runs on your machine through [ffmpeg](https://ffmpeg.org). Nothing is uploaded anywhere.

---

## Features

| | |
|---|---|
| **✂ Smart splitting** | Cuts video into 1–3 min parts. Clean filenames like `Show S01E01 - Part 3 of 8.mp4` |
| **🎬 Episode separator** | One file, two episodes? Enter a timestamp — TikCut splits them first, then cuts each into parts |
| **🕐 Skip intro** | Strip the opening by time (e.g. first 30 sec) or auto-detect it by analyzing frames |
| **⚡ Fast mode** | Stream copy, no re-encoding. A 1-hour file cuts in under 10 seconds |
| **🎯 Precise mode** | Full x264 re-encode. Frame-accurate cuts |
| **📋 Caption preview** | Live TikTok caption preview as you type the title |
| **↺ Auto-title** | Filename is cleaned and used as the series title automatically |

---

## Installation

### 1 — Install Python

Download from [python.org/downloads](https://python.org/downloads).

> ⚠️ **Windows:** check **"Add Python to PATH"** during installation.

### 2 — Install ffmpeg

**Windows**
```bash
winget install ffmpeg
```

**macOS**
```bash
brew install ffmpeg
```

**Ubuntu / Debian**
```bash
sudo apt install ffmpeg
```

### 3 — Get TikCut

```bash
git clone https://github.com/sayddii/TikCut.git
cd tikcut
```

Or just download `TikCut.py` directly — that's the whole app.

### 4 — Run

```bash
python TikCut.py.py
```

macOS / Linux:
```bash
python3 TikCut.py.py
```

No extra Python packages required.

---

## Usage

### Cutting a single video

1. Open the **✂ Cut Video** tab
2. Click **Browse...** and pick your file
3. Title is filled in automatically — edit if needed
4. Set part length with the slider (1:00 – 3:00)
5. Optionally enable **Skip intro** and set the length in seconds
6. Click **▶ CUT VIDEO**

### Splitting two episodes from one file

1. Open the **🎬 Split Episodes** tab
2. Select the file — app shows total duration
3. Enter episode names and the **end timestamp** of each
4. Supported formats: `01:22:45` · `82:45` · `4965` (seconds)
5. Last episode always runs to the end — no timestamp needed
6. Click **▶ SPLIT & CUT**

Output structure:
```
series_parts/
├── 01_episodes/
│   ├── 01. Episode 1.mp4
│   └── 02. Episode 2.mp4
└── 02_tiktok_parts/
    ├── Episode 1/
    │   ├── Episode 1 - Part 1 of 5.mp4
    │   └── Episode 1 - Part 2 of 5.mp4
    └── Episode 2/
        └── ...
```

---

## FAQ

**Fast vs Precise mode?**

- **Fast** — stream copy, no re-encoding. Splits in seconds. Cuts snap to the nearest keyframe, may be off by 1–5 sec. Fine for TikTok.
- **Precise** — full x264 re-encode. 10–50× slower. Frame-accurate cuts. Use when exact timing matters.

**"ffmpeg not found" error?**

After installing ffmpeg, restart your terminal — PATH changes apply only to new sessions.

**Auto-detect intro doesn't work?**

It analyzes frame brightness every 2 sec. Works well for static intros (black screen, logo). For complex animated intros use **By duration** and type the length manually.

**Can I post directly to TikTok?**

No — TikTok doesn't provide a public upload API for regular users.

---

## Tech stack

- **Python 3.7+** — logic and UI
- **tkinter** — standard GUI library, ships with Python
- **ffmpeg / ffprobe** — all video processing

---

## License

MIT — do whatever you want with it.

---

<div align="center">

Made for people who post TV shows on TikTok and don't want to cut each episode by hand.

**[⬇ Download TikCut.py.py](TikCut.py.py)**

</div>
