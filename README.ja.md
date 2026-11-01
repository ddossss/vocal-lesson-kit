[English](README.md) | [한국어](README.ko.md) | 日本語

# ボーカルレッスンキット (Vocal Lesson Kit)

ボーカルレッスン用ツール集 — **音程アナライザー**、**練習プレーヤー**(キー・テンポ・A–Bリピート)、伴奏を作る **MR Studio**。前の2つはインストール不要で、iPhoneのSafariを含むどのブラウザでも開けます。

**開く:** https://ddossss.github.io/vocal-lesson-kit/ (日本語 / 한국어 / English — 右上で切り替え)

## 内容

| | 動く場所 | できること |
|---|---|---|
| 🎤 音程アナライザー | スマホ・PCのブラウザ | マイクでリアルタイムの音程・音名・セント、音域の記録、男女の声に使える判定モード、録音、メトロノーム |
| 🎧 練習プレーヤー | スマホ・PCのブラウザ | 音源を開き、キー(±12半音)・テンポ(50〜130%)を変更、A–B区間リピート |
| 📖 ガイド | ブラウザ | 使い始め、iPhoneのホーム画面追加、レッスン活用、困ったとき、そのまま送れる案内メッセージ(日本語) |
| 💻 MR Studio | Windows · Mac PC(GPU推奨) | YouTube/手持ちの音源からボーカルを除去し、キー・テンポ・区間を指定 → mp3 / wav |

基本の流れ: PCのMR Studioで伴奏を作る → スマホへ送る(AirDrop、iCloud、LINE Keepなど) → 練習プレーヤーで開き、キーを変え、ゆっくりにして、難しい所を繰り返す。

## スマホ・ブラウザのツール(インストール不要)

Webページは [`docs/`](docs/) にあり、GitHub Pagesで公開します(Settings → Pages → Branch `main`、フォルダ `/docs`)。
音声はブラウザの中だけで処理され、アップロードされません。iPhone: Safariで開く → 共有 → *ホーム画面に追加*。

## 先生に送る

上のリンクを送ってください。**ガイド**ページに、LINEやメールにそのまま貼れる日本語の案内文があります。


## MR Studio (PC)

YouTube のURL、または自分の音源ファイル → ボーカル除去・キー調整(-5~+5半音)・テンポ(50~125%)・区間指定 → MRとして書き出し。

### 実行

`run.bat`(Windows)または `run.command`(Mac)をダブルクリック → ブラウザでアプリが開く (http://127.0.0.1:7860)

### 機能

手順: ①音源を入れる → ②パート・キー・テンポを設定(→ 必要なら区間) → ③**プレビュー** → ④**作成（書き出し）**  
音源を入れた後は、パート・キー・テンポを変更するたびにプレビューが自動更新されます（新しい曲の初回分離のみ1~2分）。

- **読み込み**: YouTube のURL、または自分の音源ファイル(mp3/wav/flacなど)。ファイルがある場合はファイルが優先されます。
- **残すパート**: メインボーカル / コーラス / ドラム / ベース / ギター / ピアノ / 管楽器 / その他楽器をそれぞれON/OFF。
  - デフォルト = メインボーカルのみOFF → コーラスを含むMR
  - 全てON → 分離せず原曲のキーのみ調整
  - 管楽器（オーケストラ用）: トランペット・ホルン・トロンボーン・サックス・フルートなどを**一括で**分離。トランペットだけを個別に分離するモデルはありません。
    管楽器やその他楽器をOFFにした場合のみ、管楽器分離のステップが追加で実行されます（初回処理+数十秒）。
- **キー調整**: 半音単位で-5~+5（テンポ維持、rubberband使用）
- **テンポ**: 5%刻みで50~125%（キー維持）
- **区間**: 開始/終了（例: `0:45` 〜 `1:20`）を入れると、練習したい部分だけを切り出して書き出します。入力後にプレビューを押してください。
- **言語**: 画面を 한국어 / 日本語 / English に切り替え（右上）
- **作成（書き出し）**: プレビューで確認した設定のままmp3(320k)またはwavで書き出し → `output/`フォルダにも保存

一度分離した曲は`cache/`に保存されるため、パート/キーだけを変えて再作成すれば数秒で完了します。

### 構成

- 分離1段階: Demucs `htdemucs_6s` → ボーカル / ドラム / ベース / ギター / ピアノ / その他
- 分離2段階: Mel-Roformer Karaoke → ボーカルをメインボーカル / コーラスに分離
- (管楽器ON/OFF時) 分離0段階: UVR `17_HP-Wind_Inst` → 管楽器 / それ以外、残りを1・2段階へ
- ミックス(numpy) → キー調整 + リミッター + エンコード(ffmpeg)
- UI: Gradio (v2.0のWeb版も同じアプリをサーバーに載せる方式で拡張可能)

### 制限

- **Amazon Musicは非対応**: DRM保護されたストリームのため抽出不可。購入・所持している音源ファイルを読み込みでご利用ください。
- YouTubeの音源は個人練習用としてのみ使用してください（著作権にご注意）。

### 新しいPCへのインストール

```bat
winget install --id Gyan.FFmpeg --exact
winget install --id yt-dlp.yt-dlp --exact
winget install --id DenoLand.Deno --exact
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

macOS（Apple Silicon）:

```sh
brew install ffmpeg yt-dlp deno   # key shift: brew install ffmpeg-full
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements-mac.txt
```

`run.command` をダブルクリック。キー変更には ffmpeg の rubberband フィルターが必要 — Homebrew の通常の `ffmpeg` にはなく `ffmpeg-full`（keg-only）にある。インストール済みなら `run.command` が使う。PyTorch は CPU/MPS（Apple GPU）。

NVIDIA GPU推奨（CPUのみの場合、1曲あたり数分）。初回実行時に分離モデル(~0.9GB)を`models/`へ自動ダウンロード。

### テスト

`.venv\Scripts\python test_app.py` (macOS: `.venv/bin/python test_app.py`) → `OK`（ミックス・キー・テンポ・区間、3言語の文言の一致を検査）

## リポジトリの構成

```
docs/                 Webツール(GitHub Pages)
  index.html          トップ
  analyzer/           音程アナライザー
  player/             練習プレーヤー(+ soundtouch.js)
  guide/              ガイド + 送るメッセージ
app.py  i18n.py       MR Studio(Gradio)と日/韓/英の文言
test_app.py           ロジックテスト(モデル不要)
```

## ライセンス

練習プレーヤーは [SoundTouchJS](https://github.com/cutterbl/SoundTouchJS)(LGPL-2.1)を使用しています — `docs/player/LICENSE-soundtouchjs.txt` を参照。無改変のまま `docs/player/soundtouch.js` として同梱しています。


## Made by

[Perch Creative](https://perch-creative.com) — Webサイト制作・ブランディング・ツール開発
