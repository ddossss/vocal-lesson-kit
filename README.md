English | [한국어](README.ko.md) | [日本語](README.ja.md)

# Vocal Lesson Kit

Tools for vocal lessons — a **pitch analyzer**, a **practice player** (key / tempo / A–B loop) and **MR Studio** for making backing tracks. The first two run in any browser, including iPhone Safari, with nothing to install.

**Open it:** https://ddossss.github.io/vocal-lesson-kit/ (English / 日本語 / 한국어 — switch in the top right)

## What's inside

| | Where it runs | What it does |
|---|---|---|
| 🎤 Pitch analyzer | Phone / PC browser | Live pitch, note and cents from the mic, range hold, judge mode for male & female voices, recording, metronome |
| 🎧 Practice player | Phone / PC browser | Open a song, change key (±12 semitones) and tempo (50–130%), loop a section with A–B repeat |
| 📖 Guide | Browser | Getting started, iPhone Home Screen, lesson ideas, troubleshooting, a ready-to-send message (Japanese) |
| 💻 MR Studio | Windows PC (GPU recommended) | Remove vocals from YouTube / your own audio, then set key, tempo and section → mp3 / wav |

Typical flow: make a backing track in MR Studio on the PC → send the file to your phone (AirDrop, iCloud, LINE Keep…) → open it in the practice player, shift the key, slow it down and loop the hard part.

## Phone / browser tools (no install)

The web pages live in [`docs/`](docs/) and are served by GitHub Pages (Settings → Pages → Branch `main`, folder `/docs`).
Audio is processed in the browser only and is never uploaded. On iPhone: open in Safari → Share → *Add to Home Screen*.

## Sending it to a teacher

Send the link above. The **Guide** page contains a short message in Japanese that you can copy into LINE or e-mail.


## MR Studio (PC)

YouTube URL or your own audio file → remove vocals · adjust key (-5 to +5 semitones) and tempo (50-125%) → export as an instrumental (MR) track.

### Run

Double-click `run.bat` → the app opens in your browser (http://127.0.0.1:7860)

### Features

Flow: ① load audio → ② set parts, key & tempo (→ optional section) → ③ **preview** → ④ **create (export)**  
Once audio is loaded, the preview auto-refreshes every time you change a part, the key or the tempo (only the first separation of a new song takes 1-2 minutes).

- **Import**: a YouTube URL, or your own audio file (mp3/wav/flac, etc.). If a file is provided, the file takes priority.
- **Parts to keep**: toggle main vocal / chorus / drums / bass / guitar / piano / wind instruments / other instruments on/off individually.
  - Default = main vocal off only → MR that keeps the chorus
  - All on → no separation, just pitch-shifts the original track
  - Wind instruments (for orchestral use): trumpet, horn, trombone, sax, flute, etc. are separated **as one group** — there's no model that isolates trumpet alone.
    The wind-instrument separation step only runs (adding tens of seconds on first processing) when wind or "other instruments" is turned off.
- **Key adjustment**: -5 to +5 semitones (tempo preserved, via rubberband)
- **Tempo**: 50-125% in 5% steps (key preserved)
- **Section**: optional start / end (e.g. `0:45` to `1:20`) to export only the part you want to practise. Press Preview after typing.
- **Language**: the screen can be switched between 한국어 / 日本語 / English (top right)
- **Create (export)**: exports exactly what you heard in the preview as mp3 (320k) or wav → also saved to the `output/` folder

Once a song has been separated, it's cached in `cache/`, so re-creating it with just different parts/key takes only a few seconds.

### Architecture

- Separation stage 1: Demucs `htdemucs_6s` → vocal / drums / bass / guitar / piano / other
- Separation stage 2: Mel-Roformer Karaoke → splits vocal into main vocal / chorus
- (when wind instruments are toggled) Separation stage 0: UVR `17_HP-Wind_Inst` → wind instruments / rest, then rest goes through stages 1-2
- Mix (numpy) → key shift + limiter + encode (ffmpeg)
- UI: Gradio (a v2.0 web version can extend the same app by hosting it on a server)

### Limitations

- **Amazon Music is not supported**: it's a DRM-protected stream and can't be extracted. Use a purchased/owned audio file via Import instead.
- Use YouTube-sourced audio for personal practice only (copyright).

### Setting up on a new PC

```bat
winget install --id Gyan.FFmpeg --exact
winget install --id yt-dlp.yt-dlp --exact
winget install --id DenoLand.Deno --exact
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

macOS (Apple Silicon):

```sh
brew install ffmpeg yt-dlp deno   # key shift: brew install ffmpeg-full
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements-mac.txt
```

Double-click `run.command`. Key shift needs ffmpeg's rubberband filter: Homebrew's plain `ffmpeg` lacks it, `ffmpeg-full` (keg-only) has it — `run.command` uses it when installed. PyTorch runs on CPU/MPS (Apple GPU).

An NVIDIA GPU is recommended (CPU-only takes several minutes per song). On first run, the separation models (~0.9GB) are auto-downloaded to `models/`.

### Test

`.venv\Scripts\python test_app.py` (macOS: `.venv/bin/python test_app.py`) → `OK` (checks mixing, key, tempo, section and that all three languages have the same texts)

## Repository layout

```
docs/                 web tools (GitHub Pages)
  index.html          home
  analyzer/           pitch analyzer
  player/             practice player (+ soundtouch.js)
  guide/              guide + message template
app.py  i18n.py       MR Studio (Gradio) and its ja / ko / en texts
test_app.py           logic tests (no models needed)
```

## Licenses

The practice player uses [SoundTouchJS](https://github.com/cutterbl/SoundTouchJS) (LGPL-2.1) — see `docs/player/LICENSE-soundtouchjs.txt`; it is included unmodified as `docs/player/soundtouch.js`.


## Made by

[Perch Creative](https://perch-creative.com) — websites · branding · custom tools
