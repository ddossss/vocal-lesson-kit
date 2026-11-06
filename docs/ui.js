/* Shared navigation and copy. Audio processing stays in each tool. */
(() => {
  const page = document.body.dataset.page;
  const root = page === 'home' ? './' : '../';
  const copy = {
    ko: {exercise:'음정 연습 패턴', beats:'박자', sensitivity:'마이크 감도', bpm:'분당 박자 수', slower:'템포 낮추기', faster:'템포 높이기', lower:'키 낮추기', higher:'키 높이기', home:'홈', analyzer:'음정 분석기', player:'연습 플레이어', guide:'사용 가이드', skip:'본문으로 건너뛰기', nav:'도구 메뉴',
      analyzerIntro:'목소리를 눈으로 확인하고, 나에게 편한 음역을 찾아보세요.', playerIntro:'내 음역에 맞추고, 어려운 구간은 천천히 반복하세요.',
      livePitch:'지금 부르는 음', micHelp:'마이크를 시작하고 편안하게 한 음을 내보세요.',
      audioSource:'연습할 음원', playback:'듣고 연습하기', waveEmpty:'음원을 열면 파형이 여기에 표시됩니다.', fileHelp:'MP3, M4A, WAV 등 오디오 파일',
      privacy:'음성은 기기 안에서만 처리됩니다.', local:'설치 없이, 내 기기에서', quickGuide:'도구 사용법', language:'언어', seek:'재생 위치', tempo:'템포', volume:'볼륨'},
    ja: {exercise:'音程練習パターン', beats:'拍子', sensitivity:'マイク感度', bpm:'1分あたりの拍数', slower:'テンポを下げる', faster:'テンポを上げる', lower:'キーを下げる', higher:'キーを上げる', home:'ホーム', analyzer:'音程アナライザー', player:'練習プレーヤー', guide:'使い方', skip:'本文へスキップ', nav:'ツールメニュー',
      analyzerIntro:'声の高さを目で確かめて、心地よく歌える音域を見つけましょう。', playerIntro:'自分のキーに合わせて、難しいフレーズをゆっくり繰り返しましょう。',
      livePitch:'今、歌っている音', micHelp:'マイクを開始して、楽に出せる音を歌ってみましょう。',
      audioSource:'練習する音源', playback:'聴いて、練習する', waveEmpty:'音源を開くと、ここに波形が表示されます。', fileHelp:'MP3、M4A、WAVなどの音声ファイル',
      privacy:'音声は端末の中だけで処理されます。', local:'インストール不要、端末内で処理', quickGuide:'ツールの使い方', language:'言語', seek:'再生位置', tempo:'テンポ', volume:'音量'},
    en: {exercise:'Pitch exercise', beats:'Time signature', sensitivity:'Microphone sensitivity', bpm:'Beats per minute', slower:'Decrease tempo', faster:'Increase tempo', lower:'Lower key', higher:'Raise key', home:'Home', analyzer:'Pitch analyzer', player:'Practice player', guide:'Guide', skip:'Skip to content', nav:'Tool navigation',
      analyzerIntro:'See your voice in real time. Find the range that feels like you.', playerIntro:'Find your key. Slow down a phrase. Make it your own.',
      livePitch:'Your live pitch', micHelp:'Start the microphone, then sing a comfortable note.',
      audioSource:'Your practice track', playback:'Listen & practice', waveEmpty:'Open a track to see its waveform here.', fileHelp:'MP3, M4A, WAV and other audio files',
      privacy:'Your audio stays on your device.', local:'No install. On your device.', quickGuide:'How to use the tools', language:'Language', seek:'Playback position', tempo:'Tempo', volume:'Volume'}
  };
  const mark = '<svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M5 13v6m6-12v18m5-21v24m5-18v12m6-9v6" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>';
  const header = document.createElement('header');
  header.className = 'site-header';
  header.innerHTML = `<a class="site-brand" href="${root}"><span class="brand-mark">${mark}</span><span>Vocal Lesson Kit</span></a><nav class="site-nav" data-ui-label="nav">${['home','analyzer','player','guide'].map(key => `<a href="${root}${key==='home'?'':key+'/'}" ${page===key?'aria-current="page"':''} data-ui="${key}"></a>`).join('')}</nav><div class="site-language"></div>`;
  const langSelect = document.getElementById('lang');
  if (langSelect) header.querySelector('.site-language').append(langSelect);
  document.body.prepend(header);
  const skip = document.createElement('a');
  skip.href = '#main'; skip.className = 'skip-link'; skip.dataset.ui = 'skip';
  document.body.prepend(skip);
  const footer = document.querySelector('.site-footer');
  if (footer) footer.innerHTML = `<span class="privacy-note"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="5" y="10" width="14" height="11" rx="3" stroke="currentColor" stroke-width="1.5"/><path d="M8 10V7a4 4 0 018 0v3" stroke="currentColor" stroke-width="1.5"/></svg><span data-ui="privacy"></span></span><a href="https://perch-creative.com">Perch Creative</a>`;
  function translate() {
    const t = copy[document.documentElement.lang] || copy.en;
    document.querySelectorAll('[data-ui]').forEach(el => {el.textContent=t[el.dataset.ui] || el.dataset.ui});
    document.querySelectorAll('[data-ui-label]').forEach(el => el.setAttribute('aria-label', t[el.dataset.uiLabel]));
    if (langSelect) langSelect.setAttribute('aria-label', t.language);
  }
  translate();
  new MutationObserver(translate).observe(document.documentElement, {attributes:true, attributeFilter:['lang']});
})();
