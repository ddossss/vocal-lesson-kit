"""MR Studio v2 — 유튜브 주소나 내 음원 → 보컬 제거 MR + 키(-5~+5) · 템포(50~125%) · 구간 지정 → mp3/wav 내보내기.
화면은 한국어 / 日本語 / English."""
import functools
import hashlib
import math
import re
import shutil
import subprocess
from pathlib import Path

import gradio as gr
import numpy as np
import soundfile as sf
from audio_separator.separator import Separator

from i18n import LANGS, tr

ROOT = Path(__file__).parent
MODELS = ROOT / "models"  # 분리 모델(첫 실행 때 자동 다운로드)
CACHE = ROOT / "cache"    # 곡별 분리 결과 — 같은 곡은 다시 분리하지 않음
OUT = ROOT / "output"

# 파트 id (stem 파일명이기도 함). 화면에 보이는 이름은 i18n.TEXT[언어]["stems"]
STEMS = ["lead", "backing", "drums", "bass", "guitar", "piano", "wind", "other"]
DEMUCS = "htdemucs_6s.yaml"
KARAOKE = "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt"
WIND = "17_HP-Wind_Inst-UVR.pth"  # 트럼펫·호른·색소폰·플루트 등 관악기 전체 (트럼펫 단독 모델은 없음)
TEMPO_MIN, TEMPO_MAX, TEMPO_STEP = 50, 125, 5  # %


def stem_choices(lang):
    return [(tr(lang, "stems")[s], s) for s in STEMS]


@functools.lru_cache  # 미리듣기 갱신마다 유튜브에 다시 접속하지 않게
def download(url, lang="ko"):
    if not re.search(r"(youtube\.com|youtu\.be)/", url):
        raise gr.Error(tr(lang, "e_yt"))
    r = subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "wav", "--no-playlist", "--encoding", "utf-8",
         "-o", str(CACHE / "dl" / "%(title)s [%(id)s].%(ext)s"), "--print", "after_move:filepath", url],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise gr.Error(tr(lang, "e_dl", msg=(r.stderr.strip().splitlines() or [tr(lang, "e_unknown")])[-1]))
    return Path(r.stdout.strip().splitlines()[-1])


def separate(src, progress, wind, lang="ko"):
    d = CACHE / (hashlib.sha1(src.read_bytes()).hexdigest()[:16] + ("-wind" if wind else ""))
    if (d / "done").exists():  # 완료 표시가 있을 때만 캐시 사용 (중간에 꺼져 반쯤 쓴 파일 방지)
        return d
    d.mkdir(parents=True, exist_ok=True)
    # normalization_threshold=1.0: stem별 음량 보정을 끄고 원래 밸런스 그대로 믹스
    sep = Separator(model_file_dir=str(MODELS), output_dir=str(d), normalization_threshold=1.0)
    stages = [("st_inst", DEMUCS, None, {"Vocals": "vocals", "Drums": "drums", "Bass": "bass",
                                        "Guitar": "guitar", "Piano": "piano", "Other": "other"}),
              ("st_vocal", KARAOKE, d / "vocals.wav", {"Vocals": "lead", "Instrumental": "backing"})]
    if wind:  # 관악기를 먼저 떼어내고, 나머지를 파트별로 분리
        stages.insert(0, ("st_wind", WIND, src, {"Woodwinds": "wind", "No Woodwinds": "nowind"}))
        src = d / "nowind.wav"
    tq = progress.tqdm
    for i, (name, model, path, names) in enumerate(stages, 1):
        desc = tr(lang, "p_stage", i=i, n=len(stages), name=tr(lang, name))
        progress(0, desc=desc)
        # 모델 내부 tqdm(이름 없음)은 track_tqdm으로 progress.tqdm에 전달됨 → 여기서 단계 이름을 붙여 한 줄로 표시
        progress.tqdm = lambda it=None, _desc=None, *a, desc=desc, **k: tq(it, _desc or desc, *a, **k)
        sep.load_model(model)
        sep.separate(str(path or src), names)
    progress.tqdm = tq
    (d / "done").touch()
    return d


def mix(d, keep):
    tracks = [sf.read(d / f"{k}.wav", dtype="float32") for k in keep]
    n = min(len(a) for a, _ in tracks)
    audio = sum(a[:n] for a, _ in tracks)
    return audio / max(1.0, float(np.abs(audio).max())), tracks[0][1]  # 클리핑 방지


def parse_time(text, lang="ko"):
    """'', '75', '1:15', '1:15.5', '0:01:15' → 초(float). 비어 있으면 None."""
    text = (text or "").strip().replace("：", ":")
    if not text:
        return None
    try:
        secs = 0.0
        for part in text.split(":"):
            secs = secs * 60 + float(part)
        if not math.isfinite(secs) or secs < 0 or text.count(":") > 2:
            raise ValueError
        return secs
    except ValueError:
        raise gr.Error(tr(lang, "e_time", v=text)) from None


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def encode(inp, semitones, out, tempo=1.0, start=None, end=None):
    """키(semitones)·템포(배속, 1.0=원래)·구간(start~end 초)을 적용해 out으로 저장."""
    chain = []
    if start is not None or end is not None:  # 구간은 템포 변경 '전'의 원본 시간 기준
        trim = [f"start={start}" if start is not None else None, f"end={end}" if end is not None else None]
        chain.append("atrim=" + ":".join(x for x in trim if x))
        chain.append("asetpts=PTS-STARTPTS")
    rb = ([f"pitch={2 ** (semitones / 12)}"] if semitones else []) + ([f"tempo={tempo}"] if abs(tempo - 1) > 1e-6 else [])
    if rb:
        # 키를 바꾸면 피크가 최대 ~30% 커져 풀스케일 음원이 클리핑됨 → 리미터로 피크만 잡음(자동 음량 보정 off)
        chain.append("rubberband=" + ":".join(rb + ["pitchq=quality"]))
        chain.append("alimiter=limit=0.97:level=0:latency=1")
    af = ["-af", ",".join(chain)] if chain else []
    br = ["-b:a", "320k"] if out.suffix == ".mp3" else []
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(inp), "-vn", *af, *br, str(out)], check=True)
    return out


def fmt_time(s):
    return f"{int(s // 60)}m{int(s % 60):02d}"


def fmt_dur(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def render(url, file, keep, semitones, tempo, start, end, fmt, out_dir, progress, lang="ko"):
    if not shutil.which("ffmpeg"):
        raise gr.Error(tr(lang, "e_ffmpeg"))
    if not keep:
        raise gr.Error(tr(lang, "e_part"))
    if file:
        src = Path(file)
    elif url.strip():
        progress(0, desc=tr(lang, "p_dl"))
        src = download(url.strip(), lang)
    else:
        raise gr.Error(tr(lang, "e_src"))

    semitones, tempo = int(semitones), int(tempo)
    t0, t1 = parse_time(start, lang), parse_time(end, lang)
    if t0 is not None and t1 is not None and t1 <= t0:
        raise gr.Error(tr(lang, "e_range"))
    if t0 is not None:
        total = duration(src)
        if total is not None and t0 >= total:
            raise gr.Error(tr(lang, "e_beyond", dur=fmt_dur(total)))

    if set(keep) == set(STEMS):  # 전부 남김 = 키·템포만 조절, 분리 불필요
        inp, label = src, "key"
    else:
        # 관악기는 분리 전엔 주로 '그 외 악기'에 섞여 있음 → 둘 중 하나라도 빼면 관악기 분리를 먼저 돌림
        wind = not {"wind", "other"} <= set(keep)
        d = separate(src, progress, wind, lang)
        audio, sr = mix(d, [k for k in keep if wind or k != "wind"])
        inp = d / "mix.wav"
        sf.write(inp, audio, sr, subtype="FLOAT")  # PCM_16은 정확히 1.0에서 넘쳐 부호가 뒤집힘
        # 파일명에 조합을 드러내 서로 덮어쓰지 않게: MR / no-wind / only-wind …
        kept = [k for k in STEMS if k in keep]
        cut = [k for k in STEMS if k not in keep]
        label = "MR" if cut == ["lead"] else "only-" + "-".join(kept) if len(kept) < len(cut) else "no-" + "-".join(cut)

    progress(0.9, desc=tr(lang, "p_adjust"))
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{src.stem}_{label}_key{semitones:+d}"
    if tempo != 100:
        name += f"_tempo{tempo}"
    if t0 is not None or t1 is not None:
        name += f"_{fmt_time(t0 or 0)}-{fmt_time(t1) if t1 is not None else 'end'}"
    return str(encode(inp, semitones, out_dir / f"{name}.{fmt}", tempo / 100, t0, t1))


def preview(url, file, keep, semitones, tempo, start, end, lang, progress=gr.Progress(track_tqdm=True)):
    return render(url, file, keep, semitones, tempo, start, end, "mp3", CACHE / "preview", progress, lang)


def auto_preview(url, file, keep, semitones, tempo, start, end, lang, progress=gr.Progress(track_tqdm=True)):
    # 파트/키/템포를 바꾸면 미리듣기에 바로 반영 (음원이 아직 없으면 조용히 건너뜀)
    if not keep or not (file or url.strip()):
        return gr.skip()
    return preview(url, file, keep, semitones, tempo, start, end, lang, progress)


def export(url, file, keep, semitones, tempo, start, end, lang, fmt, progress=gr.Progress(track_tqdm=True)):
    return render(url, file, keep, semitones, tempo, start, end, fmt, OUT, progress, lang)


def key_view(v, lang="ko"):
    val = tr(lang, "key_orig") if v == 0 else f"{v:+d}"
    return f'<div class="key-lbl">{tr(lang, "key")}</div><div class="key-val{" txt" if v == 0 else ""}">{val}</div><div class="key-sub">{tr(lang, "key_unit")}</div>'


def tempo_view(p, lang="ko"):
    val = tr(lang, "tempo_orig") if p == 100 else f"{p}%"
    return f'<div class="key-lbl">{tr(lang, "tempo")}</div><div class="key-val{" txt" if p == 100 else ""}">{val}</div><div class="key-sub">{tr(lang, "tempo_unit")}</div>'


def step(n, title, hint=""):
    return f'<p class="step"><span class="step-number">{n}</span><b>{title}</b></p>' + (f'<p class="hint">{hint}</p>' if hint else "")


def hero(lang):
    return f'<div id="hero"><a class="kit-link" href="https://ddossss.github.io/vocal-lesson-kit/">Vocal Lesson Kit</a><h1>MR Studio</h1><p>{tr(lang, "sub")}</p></div>'


THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue, neutral_hue=gr.themes.colors.slate, radius_size="lg",
    font=[gr.themes.GoogleFont("Noto Sans KR"), gr.themes.GoogleFont("Noto Sans JP"), "Malgun Gothic", "Yu Gothic UI", "sans-serif"],
).set(body_background_fill="#f5f7fb", body_text_color="#18243c")
CSS = """
:root, .dark { --accent: #3158d5; --panel: #fff; --line: #dce2ec; --muted: #5e6b82; }
html, body { background: #f5f7fb !important; }
.gradio-container, .gradio-container .main, .gradio-container .wrap.contain { background: transparent !important; }
.gradio-container { max-width: 1180px !important; margin: 0 auto !important; padding: 24px !important; }
footer { display: none !important; }
#hero { padding: 0 0 24px; }
#studio-language { flex: 0 0 170px !important; align-self: flex-start; }
@media (min-width: 900px) { #preview-sidebar { position: sticky; top: 24px; align-self: flex-start; } }
.kit-link { display: inline-block; color: #3158d5 !important; font-size: 13px; font-weight: 650; text-decoration: none; margin-bottom: 24px; }
#hero h1 { font-size: 42px; font-weight: 750; letter-spacing: -1.5px; margin: 0; color: #18243c; }
#hero p { color: var(--muted); margin: 10px 0 0; font-size: 15px; line-height: 1.8; }
.card { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 18px !important; padding: 24px !important; gap: 14px !important; }
.step { display: flex; align-items: center; gap: 10px; margin: 0 0 4px; }
.step-number { display: inline-grid; place-items: center; width: 25px; height: 25px; border-radius: 8px; background: #edf1fc; color: var(--accent); font-size: 12px; font-weight: 700; }
.step b { color: #18243c; font-size: 16px; font-weight: 650; }
.hint { color: var(--muted); font-size: 13px; margin: 0; line-height: 1.7; }
#parts .wrap { gap: 8px !important; }
#parts label { border: 1px solid var(--line) !important; background: #f7f9fc !important; border-radius: 10px !important; padding: 10px 14px !important; color: var(--muted) !important; cursor: pointer; min-height: 44px; }
#parts label:has(input:checked) { background: #edf1fc !important; border-color: #98ace8 !important; color: #2548bc !important; }
#parts label input { accent-color: var(--accent); }
#parts label:focus-within { outline: 3px solid #3158d5; outline-offset: 3px; }
.keyrow { align-items: center !important; justify-content: center !important; gap: 16px !important; padding: 10px 0; }
.keyrow button { font-size: 26px !important; font-weight: 500; height: 54px; width: 54px !important; min-width: 54px !important; flex: 0 0 54px !important; border-radius: 50% !important; background: #f2f5fb !important; border: 1px solid var(--line) !important; color: #3158d5 !important; }
.keyrow button:hover { background: #e6ecfc !important; border-color: var(--accent) !important; }
.keyval { text-align: center; flex: 0 1 160px !important; min-width: 100px !important; }
.key-val { font-size: 40px; font-weight: 650; color: #18243c; line-height: 1.25; font-variant-numeric: tabular-nums; letter-spacing: -1px; }
.key-val.txt { font-size: 22px; line-height: 1.5; font-weight: 650; letter-spacing: -.5px; }
.key-sub { font-size: 12px; color: var(--muted); }
.key-lbl { font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 4px; }
#listen { background: #edf1fc !important; border: 1px solid #c9d5f4 !important; color: var(--accent) !important; font-size: 15px !important; font-weight: 650; height: 52px; border-radius: 10px !important; }
#listen:hover { background: #dfe7fb !important; }
#make { background: var(--accent) !important; border: 0 !important; color: #fff !important; font-size: 15px !important; font-weight: 650; height: 52px; border-radius: 10px !important; }
#make:hover { background: #2447bb !important; }
#player { min-height: 160px; border: 1px dashed #b9c7e1 !important; border-radius: 12px !important; background: #f5f7fc !important; }
.progress-level-inner, .progress-text { color: #384d76 !important; font-size: 13px !important; }
.progress-bar-wrap { width: 85% !important; height: 8px !important; border: none !important; border-radius: 8px !important; background: #e2e8f3 !important; }
.progress-bar { background: var(--accent) !important; border-radius: 8px !important; }
.eta-bar { background: #edf1fc !important; }
button:focus-visible, a:focus-visible { outline: 3px solid #3158d5 !important; outline-offset: 3px !important; }
@media (max-width: 600px) { .gradio-container { padding: 16px !important; } .card { padding: 18px !important; } #hero h1 { font-size: 34px; } .keyrow { gap: 10px !important; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
"""
LIGHT = "() => { const u = new URL(location); if (u.searchParams.get('__theme') !== 'light') { u.searchParams.set('__theme', 'light'); location.replace(u); } }"

with gr.Blocks(title="MR Studio") as demo:
    L = "ko"
    with gr.Row(equal_height=False):
        hero_html = gr.HTML(hero(L), scale=5)
        lang = gr.Dropdown([(n, c) for c, n in LANGS.items()], value=L, label=tr(L, "lang"), interactive=True, scale=1, min_width=150, elem_id="studio-language")
    with gr.Row(equal_height=False):
        with gr.Column(scale=3):
            with gr.Column(elem_classes="card"):
                h1 = gr.HTML(step(1, tr(L, "s1")))
                url = gr.Textbox(label=tr(L, "url_label"), placeholder=tr(L, "url_ph"))
                file = gr.Audio(label=tr(L, "file_label"), type="filepath", sources=["upload"])
            with gr.Column(elem_classes="card"):
                h2 = gr.HTML(step(2, tr(L, "s2"), tr(L, "s2_hint")))
                keep = gr.CheckboxGroup(stem_choices(L), value=[k for k in STEMS if k != "lead"], show_label=False, elem_id="parts")
            with gr.Column(elem_classes="card"):
                h3 = gr.HTML(step(3, tr(L, "s3")))
                semitones = gr.State(0)
                tempo = gr.State(100)
                with gr.Row(elem_classes="keyrow"):
                    down = gr.Button("−", scale=0, min_width=72)
                    view = gr.HTML(key_view(0, L), elem_classes="keyval")
                    up = gr.Button("+", scale=0, min_width=72)
                with gr.Row(elem_classes="keyrow"):
                    tdown = gr.Button("−", scale=0, min_width=72)
                    tview = gr.HTML(tempo_view(100, L), elem_classes="keyval")
                    tup = gr.Button("+", scale=0, min_width=72)
            with gr.Column(elem_classes="card"):
                h4 = gr.HTML(step(4, tr(L, "s4"), tr(L, "s4_hint")))
                with gr.Row():
                    start = gr.Textbox(label=tr(L, "start"), placeholder=tr(L, "ph_start"), max_lines=1)
                    end = gr.Textbox(label=tr(L, "end"), placeholder=tr(L, "ph_end"), max_lines=1)
        with gr.Column(scale=2, elem_id="preview-sidebar"):
            with gr.Column(elem_classes="card"):
                h5 = gr.HTML(step(5, tr(L, "s5"), tr(L, "s5_hint")))
                listen = gr.Button(tr(L, "listen"), elem_id="listen")
                player = gr.Audio(show_label=False, type="filepath", interactive=False, elem_id="player")
            with gr.Column(elem_classes="card"):
                h6 = gr.HTML(step(6, tr(L, "s6")))
                fmt = gr.Radio(["mp3", "wav"], value="mp3", label=tr(L, "fmt"))
                make = gr.Button(tr(L, "make"), elem_id="make")
                dl = gr.File(label=tr(L, "dl"), visible=False)

    args = [url, file, keep, semitones, tempo, start, end, lang]
    # 분리·렌더링은 GPU 하나를 쓰므로 모든 작업을 한 줄로 세움 (같은 곡을 동시에 분리하지 않게)
    job = dict(concurrency_id="render", concurrency_limit=1)
    listen.click(preview, args, player, **job)
    keep.change(auto_preview, args, player, trigger_mode="always_last", **job)
    for btn, d in ((down, -1), (up, 1)):
        btn.click(lambda v, d=d: max(-5, min(5, v + d)), semitones, semitones)
    for btn, d in ((tdown, -TEMPO_STEP), (tup, TEMPO_STEP)):
        btn.click(lambda v, d=d: max(TEMPO_MIN, min(TEMPO_MAX, v + d)), tempo, tempo)
    semitones.change(key_view, [semitones, lang], view).then(auto_preview, args, player, trigger_mode="always_last", **job)
    tempo.change(tempo_view, [tempo, lang], tview).then(auto_preview, args, player, trigger_mode="always_last", **job)
    make.click(export, [*args, fmt], dl, **job).success(lambda: gr.File(visible=True), None, dl)

    # 언어 전환: 라벨·문구만 바꿈 (선택한 파트·키·템포는 그대로)
    def set_lang(lg, s, t):
        return (hero(lg), step(1, tr(lg, "s1")), gr.update(label=tr(lg, "url_label"), placeholder=tr(lg, "url_ph")),
                gr.update(label=tr(lg, "file_label")), step(2, tr(lg, "s2"), tr(lg, "s2_hint")),
                gr.update(choices=stem_choices(lg)), step(3, tr(lg, "s3")), key_view(s, lg), tempo_view(t, lg),
                step(4, tr(lg, "s4"), tr(lg, "s4_hint")),
                gr.update(label=tr(lg, "start"), placeholder=tr(lg, "ph_start")), gr.update(label=tr(lg, "end"), placeholder=tr(lg, "ph_end")),
                step(5, tr(lg, "s5"), tr(lg, "s5_hint")), gr.update(value=tr(lg, "listen")), step(6, tr(lg, "s6")),
                gr.update(label=tr(lg, "fmt")), gr.update(value=tr(lg, "make")), gr.update(label=tr(lg, "dl")),
                gr.update(label=tr(lg, "lang")))
    lang_targets = [hero_html, h1, url, file, h2, keep, h3, view, tview, h4, start, end, h5, listen, h6, fmt, make, dl, lang]
    lang.change(set_lang, [lang, semitones, tempo], lang_targets, show_progress="hidden").then(
        None, lang, None, js="(l) => { try { localStorage.setItem('mr_lang', l) } catch (e) {} }")
    demo.load(None, None, lang, js="""() => {
        let s = null; try { s = localStorage.getItem('mr_lang') } catch (e) {}
        const n = (navigator.language || 'en').slice(0, 2);
        return ['ko', 'ja', 'en'].includes(s) ? s : (['ko', 'ja'].includes(n) ? n : 'en');
    }""")

if __name__ == "__main__":
    demo.launch(inbrowser=True, theme=THEME, css=CSS, js=LIGHT)
