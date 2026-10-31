#!/bin/sh
# macOS version of run.bat: double-click in Finder → the app opens in your browser (http://127.0.0.1:7860)
cd -- "$(dirname -- "$0")" || exit 1
# Key shift uses ffmpeg's rubberband filter: Homebrew's ffmpeg-full has it (keg-only, so add it to PATH if installed)
[ -x /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg ] && PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH" && export PATH
if [ ! -x .venv/bin/python ]; then
  echo "[error] .venv is missing. See README (macOS setup)."
  exit 1
fi
.venv/bin/python app.py
