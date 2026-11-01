[English](README.md) | 한국어 | [日本語](README.ja.md)

# 보컬 레슨 키트 (Vocal Lesson Kit)

보컬 레슨용 도구 모음 — **음정 분석기**, **연습 플레이어**(키·템포·A–B 반복), 반주를 만드는 **MR Studio**. 앞의 둘은 설치 없이 iPhone Safari를 포함한 어떤 브라우저에서도 열려요.

**열기:** https://ddossss.github.io/vocal-lesson-kit/ (한국어 / 日本語 / English — 오른쪽 위에서 전환)

## 구성

| | 실행 위치 | 하는 일 |
|---|---|---|
| 🎤 음정 분석기 | 폰·PC 브라우저 | 마이크로 실시간 음정·음이름·센트, 음역 기록, 남녀 목소리용 판정 모드, 녹음, 메트로놈 |
| 🎧 연습 플레이어 | 폰·PC 브라우저 | 음원 열기, 키(±12반음)·템포(50~130%) 변경, A–B 구간 반복 |
| 📖 가이드 | 브라우저 | 시작하기, iPhone 홈 화면 추가, 레슨 활용, 문제 해결, 바로 보낼 수 있는 안내 메시지(일본어) |
| 💻 MR Studio | Windows · Mac PC (GPU 권장) | 유튜브/내 음원에서 보컬 제거, 키·템포·구간 지정 → mp3 / wav |

전형적인 흐름: PC의 MR Studio로 반주를 만든다 → 폰으로 보낸다(AirDrop, iCloud, LINE Keep 등) → 연습 플레이어에서 열어 키를 바꾸고, 느리게 하고, 어려운 부분을 반복한다.

## 폰·브라우저 도구 (설치 불필요)

웹 페이지는 [`docs/`](docs/)에 있고 GitHub Pages로 제공됩니다 (Settings → Pages → Branch `main`, 폴더 `/docs`).
음성은 브라우저 안에서만 처리되고 업로드되지 않아요. iPhone: Safari로 열기 → 공유 → *홈 화면에 추가*.

## 선생님께 보내기

위 링크를 보내면 돼요. **가이드** 페이지에 LINE이나 메일에 붙여넣을 수 있는 일본어 안내 문구가 들어 있어요.


## MR Studio (PC)

유튜브 주소나 내 음원 → 보컬 제거 · 키 조절(-5~+5 반음) · 템포(50~125%) · 구간 지정 → MR로 내보내기.

### 실행

`run.bat`(Windows) 또는 `run.command`(Mac) 더블클릭 → 브라우저에 앱이 열림 (http://127.0.0.1:7860)

### 기능

순서: ① 음원 넣기 → ② 파트·키·템포 설정(→ 필요하면 구간) → ③ **미리듣기** → ④ **만들기(내보내기)**  
음원을 넣은 뒤에는 파트·키·템포를 바꿀 때마다 미리듣기가 자동 갱신됩니다 (새 곡의 첫 분리만 1~2분).

- **가져오기**: 유튜브 주소, 또는 내 음원 파일(mp3/wav/flac 등). 파일이 있으면 파일 우선.
- **남길 파트**: 메인 보컬 / 코러스 / 드럼 / 베이스 / 기타 / 피아노 / 관악기 / 그 외 악기를 각각 on/off.
  - 기본값 = 메인 보컬만 끔 → 코러스 포함 MR
  - 전부 켬 → 분리 없이 원곡 키만 조절
  - 관악기(오케스트라용): 트럼펫·호른·트롬본·색소폰·플루트 등을 **한꺼번에** 분리. 트럼펫만 따로 분리하는 모델은 없음.
    관악기나 그 외 악기를 끌 때만 관악기 분리 단계가 추가로 돌아감(첫 처리 +수십 초).
- **키 조절**: 반음 단위 -5~+5 (템포 유지, rubberband)
- **템포**: 5% 단위 50~125% (키 유지)
- **구간**: 시작/끝(예: `0:45` ~ `1:20`)을 넣으면 연습할 부분만 잘라서 내보내요. 입력 후 미리듣기를 누르세요.
- **언어**: 화면을 한국어 / 日本語 / English로 전환 (오른쪽 위)
- **만들기(내보내기)**: 미리듣기로 확인한 설정 그대로 mp3(320k) 또는 wav → `output/` 폴더에도 저장

한 번 분리한 곡은 `cache/`에 저장되어, 파트/키만 바꿔 다시 만들면 몇 초면 끝납니다.

### 구조

- 분리 1단계: Demucs `htdemucs_6s` → 보컬 / 드럼 / 베이스 / 기타 / 피아노 / 그 외
- 분리 2단계: Mel-Roformer Karaoke → 보컬을 메인 보컬 / 코러스로
- (관악기 on/off 시) 분리 0단계: UVR `17_HP-Wind_Inst` → 관악기 / 나머지, 나머지를 1·2단계로
- 믹스(numpy) → 키 조절 + 리미터 + 인코딩(ffmpeg)
- UI: Gradio (v2.0 웹 버전도 같은 앱을 서버에 올리는 방식으로 확장 가능)

### 제한

- **아마존 뮤직은 지원 안 함**: DRM 보호 스트림이라 추출 불가. 구매/보유한 음원 파일을 가져오기로 사용.
- 유튜브 음원은 개인 연습용으로만 사용하세요 (저작권).

### 새 PC에 설치

```bat
winget install --id Gyan.FFmpeg --exact
winget install --id yt-dlp.yt-dlp --exact
winget install --id DenoLand.Deno --exact
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

macOS(Apple Silicon):

```sh
brew install ffmpeg yt-dlp deno   # key shift: brew install ffmpeg-full
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements-mac.txt
```

`run.command` 더블클릭. 키 조절은 ffmpeg 의 rubberband 필터가 필요 — Homebrew 기본 `ffmpeg` 에는 없고 `ffmpeg-full`(keg-only)에 있음, 설치돼 있으면 `run.command` 가 그것을 씀. PyTorch 는 CPU/MPS(Apple GPU).

NVIDIA GPU 권장 (CPU만 있으면 곡당 수 분). 첫 실행 때 분리 모델(~0.9GB)을 `models/`에 자동 다운로드.

### 테스트

`.venv\Scripts\python test_app.py` (macOS: `.venv/bin/python test_app.py`) → `OK` (믹스·키·템포·구간, 세 언어 문구 일치를 검사)

## 저장소 구성

```
docs/                 웹 도구 (GitHub Pages)
  index.html          첫 화면
  analyzer/           음정 분석기
  player/             연습 플레이어 (+ soundtouch.js)
  guide/              가이드 + 보낼 메시지
app.py  i18n.py       MR Studio(Gradio)와 한/일/영 문구
test_app.py           로직 테스트 (모델 불필요)
```

## 라이선스

연습 플레이어는 [SoundTouchJS](https://github.com/cutterbl/SoundTouchJS)(LGPL-2.1)를 사용합니다 — `docs/player/LICENSE-soundtouchjs.txt` 참고. 수정 없이 `docs/player/soundtouch.js`로 포함했습니다.


## Made by

[Perch Creative](https://perch-creative.com) — 웹사이트 · 브랜딩 · 툴 제작
