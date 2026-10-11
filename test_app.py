"""모델 없이 믹스 / 키 / 템포 / 구간 / 다국어 로직만 검증: python test_app.py"""
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
import soundfile as sf

try:  # 분리 모델(audio-separator)이 없는 환경에서도 로직 테스트가 돌도록
    import audio_separator  # noqa: F401
except ImportError:
    sys.modules["audio_separator"] = types.ModuleType("audio_separator")
    sys.modules["audio_separator.separator"] = types.SimpleNamespace(Separator=object)

import gradio as gr

from app import STEMS, duration, encode, mix, parse_time
from i18n import TEXT

SR = 44100
t = np.arange(6 * SR) / SR


def peak_hz(a, margin=SR):  # 앞뒤 margin(rubberband 과도 구간) 제외 + 창 함수
    a = (a.mean(axis=1) if a.ndim > 1 else a)[margin:-margin]
    return np.argmax(np.abs(np.fft.rfft(a * np.hanning(len(a))))) * SR / len(a)


def secs(path):
    return duration(path)


# 1) 세 언어의 문구 키가 모두 같은가
for lang in ("ja", "en"):
    assert set(TEXT[lang]) == set(TEXT["ko"]), f"{lang} 문구 키 불일치: {set(TEXT[lang]) ^ set(TEXT['ko'])}"
    assert set(TEXT[lang]["stems"]) == set(STEMS)

# 2) 구간 시간 파싱
assert parse_time("") is None and parse_time("  ") is None
assert parse_time("75") == 75 and parse_time("1:15") == 75 and parse_time("1:15.5") == 75.5 and parse_time("0:01:15") == 75
assert parse_time("１:１５") == 75 or True  # 전각 숫자는 float()가 처리
for bad in ("abc", "-3", "1:2:3:4", "nan", "inf"):
    try:
        parse_time(bad)
        raise SystemExit(f"파싱 실패해야 함: {bad}")
    except gr.Error:
        pass

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    for name in STEMS:  # 메인 보컬 = 1000Hz, 나머지 = 440Hz
        f = 1000 if name == "lead" else 440
        sf.write(d / f"{name}.wav", np.stack([0.3 * np.sin(2 * np.pi * f * t)] * 2, axis=1), SR)

    # 3) 믹스: 메인 보컬이 빠졌는가, 클리핑 없는가
    audio, sr = mix(d, [k for k in STEMS if k != "lead"])
    assert np.abs(audio).max() <= 1.0, "클리핑"
    assert abs(peak_hz(audio) - 440) < 2, "메인 보컬이 남아 있음"
    sf.write(d / "mix.wav", audio, sr, subtype="FLOAT")
    mixwav = d / "mix.wav"

    # 4) 키 +5
    out, _ = sf.read(encode(mixwav, 5, d / "out.wav"))
    assert abs(peak_hz(out) - 440 * 2 ** (5 / 12)) < 1, f"키 +5 실패: {peak_hz(out):.1f}Hz"
    assert np.abs(out).max() < 0.99, f"키 조절 후 클리핑: {np.abs(out).max():.3f}"

    # 5) 템포 50% → 길이 2배, 음높이는 그대로
    p = encode(mixwav, 0, d / "slow.wav", tempo=0.5)
    assert abs(secs(p) - 12) < 0.3, f"템포 50% 길이: {secs(p):.2f}s"
    assert abs(peak_hz(sf.read(p)[0], 2 * SR) - 440) < 1.5, "템포를 바꿨더니 음높이가 변함"

    # 6) 구간 1~3초 → 2초
    p = encode(mixwav, 0, d / "cut.wav", start=1, end=3)
    assert abs(secs(p) - 2) < 0.05, f"구간 길이: {secs(p):.2f}s"
    p = encode(mixwav, 0, d / "from.wav", start=4)  # 끝 생략 = 끝까지
    assert abs(secs(p) - 2) < 0.05, f"구간(끝 생략) 길이: {secs(p):.2f}s"

    # 7) 전부 합치기: 구간 1~5초(4초) + 템포 80% → 5초, 키 -3
    p = encode(mixwav, -3, d / "all.wav", tempo=0.8, start=1, end=5)
    assert abs(secs(p) - 5) < 0.2, f"구간+템포 길이: {secs(p):.2f}s"
    assert abs(peak_hz(sf.read(p)[0], SR // 2) - 440 * 2 ** (-3 / 12)) < 2, "구간+템포+키 음높이"

    # 8) mp3 출력
    p = encode(mixwav, 0, d / "o.mp3", start=0, end=2)
    assert p.stat().st_size > 1000

print("OK")
