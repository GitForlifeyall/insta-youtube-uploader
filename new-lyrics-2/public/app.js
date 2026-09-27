// State Management
const state = {
  currentEventSource: null,
  isGenerating: false,
  activeVideoUrl: null,
  activeMetadata: null,
  syncedLines: [],
  currentLineIndex: -1,
  currentBackdrop: 'black',
  template: 'master_lyrics',
  fontFamily: 'Impact',
  fontSize: 72,
  blur: 3.2,
  spacing: -1,
  wordSpacing: 0,
  language: 'auto',
  placement: 'center',
  ypos: 50,
  xpos: 50,
  bratTheme: 'green',
  bratCasing: 'upper',
  bratBold: false,
  nokiaScreenColor: '#b40000',
  nokiaStickersEnabled: false,
  nokiaSticker: 'random',
  topHeader: '',
  introHeader: '',
  testStart: 0,
  testEnd: '',
  previewQuality: 'final',
  masterVariant: 'default',
  ytHindiVariant: 'standard',
  availableBgFolders: [],
  selectedBgFolders: [],
  lastQuery: 'The Weeknd - Blinding Lights',
  isIgLoggedIn: false,
  availableHooks: [],
  selectedHook: null
};


// DOM Elements
const generatorForm = document.getElementById('generator-form');
const songQueryInput = document.getElementById('song-query-input');
const generateBtn = document.getElementById('generate-btn');
const btnText = document.getElementById('btn-text');
const templatePills = document.querySelectorAll('#template-group .template-pill');
const fontBtns = document.querySelectorAll('#font-group .font-pill');
const customFontInput = document.getElementById('custom-font-input');
const langBtns = document.querySelectorAll('#lang-group .lang-pill');
const customLangInput = document.getElementById('custom-lang-input');
const masterLyricsVariantRow = document.getElementById('master-lyrics-variant-row');
const masterLyricsVariantSelect = document.getElementById('master-lyrics-variant-select');
const ytHindiVariantRow = document.getElementById('yt-hindi-variant-row');
const ytHindiVariantSelect = document.getElementById('yt-hindi-variant-select');

// Keep the legacy backend templates available, but remove obsolete controls
// from the public Studio UI.
document.querySelectorAll('#template-group [data-template="template1"], #template-group [data-template="template2"], #template-group [data-template="template3"], #template-group [data-template="yt_hindi_intro"]').forEach((el) => { el.style.display = 'none'; });
['font-group', 'lang-group', 'placement-group', 'xpos-slider', 'ypos-slider', 'fontsize-slider', 'blur-slider', 'spacing-slider', 'word-spacing-slider'].forEach((id) => {
  const el = document.getElementById(id);
  if (el) (el.closest('.control-row') || el.parentElement).style.display = 'none';
});
document.querySelectorAll('.backdrop-switcher').forEach((el) => { el.style.display = 'none'; });
const defaultMasterTemplate = document.querySelector('#template-group [data-template="master_lyrics"]');
templatePills.forEach((pill) => pill.classList.remove('active'));
if (defaultMasterTemplate) defaultMasterTemplate.classList.add('active');
if (masterLyricsVariantRow) masterLyricsVariantRow.style.display = 'flex';

// Brat controls & live sandbox
const bratOptionsRow = document.getElementById('brat-options-row');
const bratPalettes = document.querySelectorAll('#brat-palettes-group .brat-swatch-btn');
const bratLiveSandbox = document.getElementById('brat-live-sandbox');
const bratLiveContainer = document.getElementById('brat-live-container');
const bratLiveText = document.getElementById('brat-live-text');
const bratSandboxInput = document.getElementById('brat-sandbox-input');
const bratCasingToggleBtn = document.getElementById('brat-casing-toggle-btn');
const bratBoldToggleBtn = document.getElementById('brat-bold-toggle-btn');
const bratChipBtns = document.querySelectorAll('.brat-chip-btn');

// YT Hindi Type controls
const ytHindiOptionsRow = document.getElementById('yt-hindi-options-row');
const ytHindiTopHeaderInput = document.getElementById('yt-hindi-top-header-input');
const ytHindiIntroOptionsRow = document.getElementById('yt-hindi-intro-options-row');
const ytHindiIntroTextInput = document.getElementById('yt-hindi-intro-text-input');
const bgFoldersOptionsRow = document.getElementById('bg-folders-options-row');
const bgFoldersGroup = document.getElementById('bg-folders-group');
const bgFoldersCountLabel = document.getElementById('bg-folders-count-label');
const bgFoldersToggleAllBtn = document.getElementById('bg-folders-toggle-all-btn');
const bgFoldersClearBtn = document.getElementById('bg-folders-clear-btn');
const nokiaOptionsRow = document.getElementById('nokia-options-row');
const nokiaStickersRow = document.getElementById('nokia-stickers-row');
const nokiaPalettes = document.querySelectorAll('.nokia-swatch-btn');
const nokiaCustomColor = document.getElementById('nokia-custom-color');
const nokiaStickersToggle = document.getElementById('nokia-stickers-toggle');
const nokiaStickerSelect = document.getElementById('nokia-sticker-select');
const nokiaStickerSelectGroup = document.getElementById('nokia-sticker-select-group');
const testStartInput = document.getElementById('test-start-input');
const testEndInput = document.getElementById('test-end-input');
const previewQualityInput = document.getElementById('preview-quality-input');

// Spotify Lyrics Card Elements (LyricPost Pipeline)
const spotifyCardStudio = document.getElementById('spotify-card-studio');
const spotifyCardFetchBtn = document.getElementById('spotify-card-fetch-btn');
const spotifyCardDownloadBtn = document.getElementById('spotify-card-download-btn');
const spotifyCardStatus = document.getElementById('spotify-card-status');
const additionalBgPreview = document.getElementById('additional-bg-preview');
const songImageWrap = document.getElementById('song-image-wrap');
const songImage = document.getElementById('song-image');
const songImageCover = document.getElementById('song-image-cover');
const songImageName = document.getElementById('song-image-name');
const songImageAuthors = document.getElementById('song-image-authors');
const songImageLyrics = document.getElementById('song-image-lyrics');
const spotifyCardTextWhiteBtn = document.getElementById('spotify-card-text-white-btn');
const spotifyCardTextBlackBtn = document.getElementById('spotify-card-text-black-btn');
const spotifyCardSwatches = document.querySelectorAll('#spotify-card-swatches .spotify-swatch-btn');
const spotifyCardCustomColor = document.getElementById('spotify-card-custom-color');
const spotifyCardSecondaryColor = document.getElementById('spotify-card-secondary-color');
const spotifyCardSecondaryVal = document.getElementById('spotify-card-secondary-val');
const spotifyCardBlurSlider = document.getElementById('spotify-card-blur-slider');
const spotifyCardBlurVal = document.getElementById('spotify-card-blur-val');
const spotifyCardOpacitySlider = document.getElementById('spotify-card-opacity-slider');
const spotifyCardOpacityVal = document.getElementById('spotify-card-opacity-val');
const spotifyCardRadiusSlider = document.getElementById('spotify-card-radius-slider');
const spotifyCardRadiusVal = document.getElementById('spotify-card-radius-val');
const spotifyCardFontsizeSlider = document.getElementById('spotify-card-fontsize-slider');
const spotifyCardFontsizeVal = document.getElementById('spotify-card-fontsize-val');
const spotifyCardWidthSlider = document.getElementById('spotify-card-width-slider');
const spotifyCardWidthVal = document.getElementById('spotify-card-width-val');
const spotifyCardBackdropToggle = document.getElementById('spotify-card-backdrop-toggle');
const spotifyCardBackdropOptions = document.getElementById('spotify-card-backdrop-options');
const spotifyCardBackdropStyle = document.getElementById('spotify-card-backdrop-style');
const spotifyCardFrameRatio = document.getElementById('spotify-card-frame-ratio');
const spotifyCardLinesList = document.getElementById('spotify-card-lines-list');
const spotifyCardClearLyricsBtn = document.getElementById('spotify-card-clear-lyrics-btn');
const spotifyCardSampleLyricsBtn = document.getElementById('spotify-card-sample-lyrics-btn');

// Instagram Viral Hook & Login Elements
const viralHookSelect = document.getElementById('viral-hook-select');
const fetchHooksBtn = document.getElementById('fetch-hooks-btn');
const igLoginBtn = document.getElementById('ig-login-btn');
const igStatusBadge = document.getElementById('ig-status-badge');
const hookModal = document.getElementById('hook-modal');
const hookModalList = document.getElementById('hook-modal-list');
const closeHookModalBtn = document.getElementById('close-hook-modal-btn');
const hookModalCancelBtn = document.getElementById('hook-modal-cancel-btn');
const hookModalConfirmBtn = document.getElementById('hook-modal-confirm-btn');

// Placement & Size controls
const placementPills = document.querySelectorAll('#placement-group .placement-pill');
const xposSlider = document.getElementById('xpos-slider');
const xposVal = document.getElementById('xpos-val');
const yposSlider = document.getElementById('ypos-slider');
const yposVal = document.getElementById('ypos-val');
const fontsizeSlider = document.getElementById('fontsize-slider');
const fontsizeVal = document.getElementById('fontsize-val');
const blurSlider = document.getElementById('blur-slider');
const blurVal = document.getElementById('blur-val');
const spacingSlider = document.getElementById('spacing-slider');
const spacingVal = document.getElementById('spacing-val');
const wordSpacingSlider = document.getElementById('word-spacing-slider');
const wordSpacingVal = document.getElementById('word-spacing-val');

// Pipeline elements
const pipelineSection = document.getElementById('pipeline-section');
const pipelineStatusText = document.getElementById('pipeline-status-text');
const pipelinePercentBadge = document.getElementById('pipeline-percent-badge');
const progressBarFill = document.getElementById('progress-bar-fill');

const stepAudio = document.getElementById('step-audio');
const stepAudioDetail = document.getElementById('step-audio-detail');
const stepAudioStatus = document.getElementById('step-audio-status');

const stepLyrics = document.getElementById('step-lyrics');
const stepLyricsDetail = document.getElementById('step-lyrics-detail');
const stepLyricsStatus = document.getElementById('step-lyrics-status');

const stepAss = document.getElementById('step-ass');
const stepAssDetail = document.getElementById('step-ass-detail');
const stepAssStatus = document.getElementById('step-ass-status');

const stepFfmpeg = document.getElementById('step-ffmpeg');
const stepFfmpegDetail = document.getElementById('step-ffmpeg-detail');
const stepFfmpegStatus = document.getElementById('step-ffmpeg-status');
const generationMetrics = document.getElementById('generation-metrics');
const generationMetricsGrid = document.getElementById('generation-metrics-grid');

const consoleStream = document.getElementById('console-stream');
const consoleLineCount = document.getElementById('console-line-count');

// Studio Stage
const studioStage = document.getElementById('studio-stage');
const stageSongTitle = document.getElementById('stage-song-title');
const stageSongMeta = document.getElementById('stage-song-meta');
const videoPreviewWrapper = document.getElementById('video-preview-wrapper');
const videoBackdrop = document.getElementById('video-backdrop');
const outputVideoPlayer = document.getElementById('output-video-player');
const videoSource = document.getElementById('video-source');
const backdropBtns = document.querySelectorAll('.backdrop-btn');

const dlVideoBtn = document.getElementById('dl-video-btn');
const dlAssBtn = document.getElementById('dl-ass-btn');
const dlLrcBtn = document.getElementById('dl-lrc-btn');

const teleprompterStream = document.getElementById('teleprompter-stream');
const teleprompterCount = document.getElementById('teleprompter-count');

// Gallery
const videosGalleryGrid = document.getElementById('videos-gallery-grid');
const refreshGalleryBtn = document.getElementById('refresh-gallery-btn');

const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toast-message');

let logCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadVideosGallery();
  applyRealtimePlacementAndSize();
  checkInstagramStatus();
  initSpotifyCard();
});

function setupEventListeners() {
  // Form submission: Launch video generation directly with active inputs & timestamps
  generatorForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = songQueryInput.value.trim();
    if (!query) return;

    state.lastQuery = query;

    // Direct fetch for Spotify, YouTube Music, Genius & Apple Music Lyrics Card templates
    if (state.template === 'spotify_card' || state.template === 'yt_music_card' || state.template === 'genius_card' || state.template === 'apple_music_card') {
      fetchSpotifyCardLyrics(query);
      return;
    }

    // If user picked a specific viral hook in the dropdown, sync its timing
    if (viralHookSelect && viralHookSelect.value !== 'full' && viralHookSelect.value !== 'custom') {
      const selected = state.availableHooks.find(h => String(h.start_ms) === viralHookSelect.value);
      if (selected) {
        state.testStart = selected.start_seconds;
        state.testEnd = selected.end_seconds;
        if (testStartInput) testStartInput.value = selected.start_seconds;
        if (testEndInput) testEndInput.value = selected.end_seconds;
      }
    }

    startGenerationPipeline(query);
  });

  // Template Selection
  templatePills.forEach((pill) => {
    pill.addEventListener('click', () => {
      templatePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.template = pill.dataset.template;

      // Keep the legacy Film Burn entry point aligned with the YT Hindi
      // variation selector.
      if (state.template === 'yt_hindi_intro') {
        state.ytHindiVariant = 'film_burn';
        if (ytHindiVariantSelect) ytHindiVariantSelect.value = 'film_burn';
      }

      const isBrat = ['template4_brat', 'template_4_brat', 'brat'].includes(state.template);
      const isYtHindi = ['yt_hindi_type', 'yt_hindi_intro'].includes(state.template);
      const isNokia = ['c19_nokia', 'nokia', 'c19 nokia'].includes(state.template);
      const isSpotifyCard = state.template === 'spotify_card';
      const isYtMusicCard = state.template === 'yt_music_card';
      const isGeniusCard = state.template === 'genius_card';
      const isAppleMusicCard = state.template === 'apple_music_card';

      // Hide all template-specific option rows first
      if (bratOptionsRow) bratOptionsRow.style.display = 'none';
      if (bratLiveSandbox) bratLiveSandbox.style.display = 'none';
      if (ytHindiOptionsRow) ytHindiOptionsRow.style.display = 'none';
      if (ytHindiIntroOptionsRow) ytHindiIntroOptionsRow.style.display = 'none';
      if (bgFoldersOptionsRow) bgFoldersOptionsRow.style.display = 'none';
      if (masterLyricsVariantRow) masterLyricsVariantRow.style.display = 'none';
      if (ytHindiVariantRow) ytHindiVariantRow.style.display = 'none';
      if (nokiaOptionsRow) nokiaOptionsRow.style.display = 'none';
      if (nokiaStickersRow) nokiaStickersRow.style.display = 'none';
      if (spotifyCardStudio) spotifyCardStudio.style.display = 'none';

      if (isSpotifyCard || isYtMusicCard || isGeniusCard || isAppleMusicCard) {
        if (spotifyCardStudio) {
          spotifyCardStudio.style.display = 'block';
          if (isAppleMusicCard && spotifyCardState.cardType !== 'apple_music') {
            applyCardPreset(APPLE_MUSIC_PRESET);
          } else if (isGeniusCard && spotifyCardState.cardType !== 'genius') {
            applyCardPreset(GENIUS_PRESET);
          } else if (isYtMusicCard && spotifyCardState.cardType !== 'yt_music') {
            applyCardPreset(YT_MUSIC_PRESET);
          } else if (isSpotifyCard && spotifyCardState.cardType !== 'spotify') {
            applyCardPreset(SPOTIFY_PRESET);
          } else {
            updateSpotifyCardPreview();
          }
        }
        showToast(
          isAppleMusicCard ? '🍎 Apple Music Lyrics Card Studio activated' :
          isGeniusCard ? '🟡 Genius Lyrics Card Studio activated' :
          isYtMusicCard ? '🔴 YouTube Music Lyrics Card Studio activated' :
          '🎴 Spotify Lyrics Card Studio activated'
        );
        return;
      }

      if (isBrat) {
        if (bratOptionsRow) bratOptionsRow.style.display = 'flex';
        if (bratLiveSandbox) bratLiveSandbox.style.display = 'flex';
        state.fontFamily = 'Arial Narrow';
        state.fontSize = 72;
        state.blur = 1.5;
        state.spacing = -1;
        state.wordSpacing = 0;
        state.bratCasing = 'upper';
        if (bratCasingToggleBtn) {
          bratCasingToggleBtn.classList.add('active');
          bratCasingToggleBtn.textContent = 'UPPERCASE';
        }
        syncBratContainerClasses();
        if (bratSandboxInput && (!bratSandboxInput.value || bratSandboxInput.value.toLowerCase() === '365 partygirl')) {
          bratSandboxInput.value = '365 PARTYGIRL';
        }
        fontBtns.forEach(b => b.classList.toggle('active', b.dataset.font === 'Arial Narrow'));
        applyRealtimePlacementAndSize();
        updateBratText(bratSandboxInput ? bratSandboxInput.value : '365 PARTYGIRL');
        showToast('Activated 🟩 Brat Minimal Template (Charli XCX)');
      } else if (isYtHindi) {
        if (ytHindiOptionsRow) ytHindiOptionsRow.style.display = (state.template === 'yt_hindi_type') ? 'flex' : 'none';
        if (ytHindiIntroOptionsRow) ytHindiIntroOptionsRow.style.display = (state.template === 'yt_hindi_intro') ? 'flex' : 'none';
        if (bgFoldersOptionsRow) bgFoldersOptionsRow.style.display = 'flex';
        if (ytHindiVariantRow) ytHindiVariantRow.style.display = 'flex';
        state.fontFamily = 'EB Garamond';
        state.fontSize = 68;
        state.blur = 0;
        fontBtns.forEach(b => b.classList.toggle('active', b.dataset.font === 'EB Garamond'));
        state.topHeader = ytHindiTopHeaderInput ? ytHindiTopHeaderInput.value : '(When Lyrics feel Too Personal...)';
        applyRealtimePlacementAndSize();
        if (state.template === 'yt_hindi_intro') {
          showToast('🔥 YT Hindi (Film Burn Intro) activated — custom intro text with vintage film burn!');
        } else {
          showToast('🎬 YT Hindi Type activated — drop your background videos in videos/input!');
        }
      } else if (state.template === 'master_lyrics') {
        if (masterLyricsVariantRow) masterLyricsVariantRow.style.display = 'flex';
        state.masterVariant = masterLyricsVariantSelect ? masterLyricsVariantSelect.value : 'default';
        state.fontFamily = state.masterVariant === 'zmusic' ? 'Roboto' : 'Arial';
        state.fontSize = 44;
        state.blur = 0;
        fontBtns.forEach(b => b.classList.toggle('active', b.dataset.font === state.fontFamily));
        applyRealtimePlacementAndSize();
        showToast('📜 Master Lyric Template activated (Aesthetic verse card with black pill highlight)');
      } else if (isNokia) {
        if (nokiaOptionsRow) nokiaOptionsRow.style.display = 'flex';
        if (nokiaStickersRow) nokiaStickersRow.style.display = 'flex';
        state.fontFamily = 'Nokia Cellphone FC';
        state.fontSize = 115;
        state.blur = 0;
        applyRealtimePlacementAndSize();
        showToast('📱 C19 Nokia Template activated (1:1 Retro monochrome screen)');
      } else {
        showToast(`Selected ${pill.querySelector('.template-num').textContent.trim()}`);
      }
    });
  });

  if (masterLyricsVariantSelect) {
    masterLyricsVariantSelect.addEventListener('change', () => {
      state.masterVariant = masterLyricsVariantSelect.value;
      if (state.template === 'master_lyrics') {
        state.fontFamily = state.masterVariant === 'zmusic' ? 'Roboto' : 'Arial';
        showToast(`Master Lyrics ${state.masterVariant === 'zmusic' ? 'Z Music' : 'Current'} variation selected`);
      }
    });
  }

  if (ytHindiVariantSelect) {
    ytHindiVariantSelect.addEventListener('change', () => {
      state.ytHindiVariant = ytHindiVariantSelect.value;
      if (state.template === 'yt_hindi_type') {
        showToast(`YT Hindi ${state.ytHindiVariant === 'film_burn' ? 'Film Burn' : 'Standard'} variation selected`);
      }
    });
  }

  if (testStartInput) testStartInput.addEventListener('input', (e) => {
    state.testStart = e.target.value;
    if (viralHookSelect && viralHookSelect.value !== 'custom') {
      viralHookSelect.value = 'custom';
    }
  });
  if (testEndInput) testEndInput.addEventListener('input', (e) => {
    state.testEnd = e.target.value;
    if (viralHookSelect && viralHookSelect.value !== 'custom') {
      viralHookSelect.value = 'custom';
    }
  });
  if (previewQualityInput) previewQualityInput.addEventListener('change', (e) => { state.previewQuality = e.target.value; });

  // Instagram Viral Hook Dropdown Change
  if (viralHookSelect) {
    viralHookSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === 'full') {
        state.testStart = 0;
        state.testEnd = '';
        if (testStartInput) testStartInput.value = 0;
        if (testEndInput) testEndInput.value = '';
        showToast('Selected: Full Song 🎵');
      } else if (val === 'custom') {
        showToast('Enter your custom Start & End seconds below ⏱️');
      } else {
        const hook = state.availableHooks.find(h => String(h.start_ms) === val);
        if (hook) {
          state.selectedHook = hook;
          state.testStart = hook.start_seconds;
          state.testEnd = hook.end_seconds;
          if (testStartInput) testStartInput.value = hook.start_seconds;
          if (testEndInput) testEndInput.value = hook.end_seconds;
          showToast(`Selected: ${hook.label} (${hook.start_formatted} - ${hook.end_formatted}) ⚡`);
        }
      }
    });
  }

  // Instagram Manual Fetch Button
  if (fetchHooksBtn) {
    fetchHooksBtn.addEventListener('click', () => {
      const query = songQueryInput.value.trim();
      if (!query) {
        showToast('Please enter a song name or Spotify link first.');
        return;
      }
      fetchViralHooks(query, false);
    });
  }

  // Instagram Chrome Login Button
  if (igLoginBtn) {
    igLoginBtn.addEventListener('click', () => {
      triggerInstagramLogin();
    });
  }

  // Hook Modal Buttons
  if (closeHookModalBtn) {
    closeHookModalBtn.addEventListener('click', () => hideHookModal());
  }
  if (hookModalCancelBtn) {
    hookModalCancelBtn.addEventListener('click', () => hideHookModal());
  }
  if (hookModalConfirmBtn) {
    hookModalConfirmBtn.addEventListener('click', () => {
      hideHookModal();
      const query = songQueryInput.value.trim() || state.lastQuery;
      startGenerationPipeline(query);
    });
  }

  // YT Hindi Top Header input live sync
  if (ytHindiTopHeaderInput) {
    ytHindiTopHeaderInput.addEventListener('input', (e) => {
      state.topHeader = e.target.value;
    });
  }

  // YT Hindi Intro Text input live sync
  if (ytHindiIntroTextInput) {
    ytHindiIntroTextInput.addEventListener('input', (e) => {
      state.introHeader = e.target.value;
    });
  }

  // Load Available Nokia Stickers dynamically
  async function loadNokiaStickers() {
    try {
      const res = await fetch('/api/nokia-stickers');
      const data = await res.json();
      if (data.stickers && Array.isArray(data.stickers) && nokiaStickerSelect) {
        nokiaStickerSelect.innerHTML = '<option value="random">🎲 Random</option>';
        data.stickers.forEach(stk => {
          const opt = document.createElement('option');
          opt.value = stk;
          let label = stk.replace(/\.(png|webp|jpe?g)$/i, '').replace(/[_-]/g, ' ');
          label = label.charAt(0).toUpperCase() + label.slice(1);
          if (stk.includes('moon')) label = '🌙 ' + label;
          else if (stk.includes('star')) label = '⭐ ' + label;
          else label = '✨ ' + label;
          opt.textContent = label;
          nokiaStickerSelect.appendChild(opt);
        });
      }
    } catch (err) {
      console.warn('Could not load nokia stickers:', err);
    }
  }
  loadNokiaStickers();

  // Load Available Background Video Folders
  async function loadBackgroundFolders() {
    if (!bgFoldersGroup) return;
    try {
      const res = await fetch('/api/background-folders');
      const data = await res.json();
      if (!data || !data.folders) return;
      state.availableBgFolders = data.folders;

      bgFoldersGroup.innerHTML = '';
      if (state.availableBgFolders.length === 0) {
        bgFoldersGroup.innerHTML = '<span style="font-size: 0.74rem; color: var(--text-muted);">No video folders found in <code>videos/input/</code></span>';
        return;
      }

      // Default: select subfolders that contain videos
      const subFoldersWithDirectVideos = state.availableBgFolders.filter(f => f.directCount > 0);
      const initialSelection = subFoldersWithDirectVideos.length > 0 ? subFoldersWithDirectVideos : state.availableBgFolders;

      state.availableBgFolders.forEach(folder => {
        const pill = document.createElement('button');
        pill.type = 'button';
        const isDefaultActive = initialSelection.some(sf => sf.path === folder.path);
        pill.className = `bg-folder-pill${isDefaultActive ? ' active' : ''}`;
        pill.dataset.path = folder.path;
        pill.dataset.count = folder.count;

        const cleanLabel = folder.path.replace(/\\/g, ' / ');
        pill.innerHTML = `<span>📁 ${cleanLabel}</span><span class="folder-count-badge">${folder.count}</span>`;

        pill.addEventListener('click', () => {
          pill.classList.toggle('active');
          updateSelectedBgFoldersFromUI();
        });

        bgFoldersGroup.appendChild(pill);
      });

      updateSelectedBgFoldersFromUI();
    } catch (err) {
      console.warn('Could not load background video folders:', err);
    }
  }

  function updateSelectedBgFoldersFromUI() {
    if (!bgFoldersGroup) return;
    const activePills = bgFoldersGroup.querySelectorAll('.bg-folder-pill.active');
    const selected = [];
    let totalClips = 0;

    activePills.forEach(p => {
      selected.push(p.dataset.path);
      totalClips += parseInt(p.dataset.count || '0', 10);
    });

    state.selectedBgFolders = selected;
    if (bgFoldersCountLabel) {
      if (selected.length === 0) {
        bgFoldersCountLabel.textContent = 'No folders selected (will use black background)';
        bgFoldersCountLabel.style.color = 'var(--text-muted)';
      } else if (state.availableBgFolders && selected.length === state.availableBgFolders.length) {
        bgFoldersCountLabel.textContent = `All folders selected (${totalClips} video clips pooled)`;
        bgFoldersCountLabel.style.color = '#c0ea68';
      } else {
        bgFoldersCountLabel.textContent = `${selected.length} folder${selected.length > 1 ? 's' : ''} selected (${totalClips} video clips pooled)`;
        bgFoldersCountLabel.style.color = '#c0ea68';
      }
    }
  }

  if (bgFoldersToggleAllBtn) {
    bgFoldersToggleAllBtn.addEventListener('click', () => {
      if (!bgFoldersGroup) return;
      const pills = bgFoldersGroup.querySelectorAll('.bg-folder-pill');
      pills.forEach(p => p.classList.add('active'));
      updateSelectedBgFoldersFromUI();
      showToast('Selected all background video folders');
    });
  }

  if (bgFoldersClearBtn) {
    bgFoldersClearBtn.addEventListener('click', () => {
      if (!bgFoldersGroup) return;
      const pills = bgFoldersGroup.querySelectorAll('.bg-folder-pill');
      pills.forEach(p => p.classList.remove('active'));
      updateSelectedBgFoldersFromUI();
      showToast('Cleared video folder selection');
    });
  }

  loadBackgroundFolders();

  // Nokia Screen Color Palettes
  if (nokiaPalettes) {
    nokiaPalettes.forEach(btn => {
      btn.addEventListener('click', () => {
        nokiaPalettes.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.nokiaScreenColor = btn.dataset.color;
        if (nokiaCustomColor) nokiaCustomColor.value = state.nokiaScreenColor;
        showToast(`Nokia Screen: ${btn.title}`);
      });
    });
  }
  if (nokiaCustomColor) {
    nokiaCustomColor.addEventListener('input', (e) => {
      state.nokiaScreenColor = e.target.value;
      nokiaPalettes.forEach(b => b.classList.remove('active'));
    });
  }

  // Nokia Stickers Toggle & Select
  if (nokiaStickersToggle) {
    nokiaStickersToggle.addEventListener('change', () => {
      state.nokiaStickersEnabled = nokiaStickersToggle.checked;
      if (nokiaStickerSelectGroup) {
        nokiaStickerSelectGroup.style.opacity = state.nokiaStickersEnabled ? '1' : '0.55';
      }
      showToast(state.nokiaStickersEnabled ? '✨ Nokia Stickers enabled' : 'Nokia Stickers disabled');
    });
  }
  if (nokiaStickerSelect) {
    nokiaStickerSelect.addEventListener('change', () => {
      state.nokiaSticker = nokiaStickerSelect.value;
      if (!state.nokiaStickersEnabled && nokiaStickersToggle) {
        nokiaStickersToggle.checked = true;
        state.nokiaStickersEnabled = true;
        if (nokiaStickerSelectGroup) nokiaStickerSelectGroup.style.opacity = '1';
      }
      showToast(`Selected sticker: ${nokiaStickerSelect.options[nokiaStickerSelect.selectedIndex]?.text || state.nokiaSticker}`);
    });
  }

  // Brat Container Classes Synchronizer
  const syncBratContainerClasses = () => {
    if (!bratLiveContainer) return;
    bratLiveContainer.className = `brat-box-container brat-container theme-brat-${state.bratTheme} ${state.bratCasing === 'upper' ? 'casing-upper' : 'casing-lower'}${state.bratBold ? ' is-bold' : ''}`;
  };

  // Brat Palette Swatches
  bratPalettes.forEach((btn) => {
    btn.addEventListener('click', () => {
      bratPalettes.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.bratTheme = btn.dataset.theme;
      syncBratContainerClasses();
      // Un-highlight active preset chip if custom palette chosen
      bratChipBtns.forEach(c => {
        if (c.dataset.theme !== state.bratTheme) c.classList.remove('active');
      });
      showToast(`Brat Theme: ${btn.querySelector('.swatch-name')?.textContent.trim() || state.bratTheme}`);
    });
  });

  // Brat Live Reflow Sandbox Input
  if (bratSandboxInput) {
    bratSandboxInput.addEventListener('input', (e) => {
      updateBratText(e.target.value);
    });
  }

  // Brat Casing Toggle (100% Lowercase default vs Uppercase)
  if (bratCasingToggleBtn) {
    bratCasingToggleBtn.addEventListener('click', () => {
      state.bratCasing = state.bratCasing === 'lower' ? 'upper' : 'lower';
      bratCasingToggleBtn.classList.toggle('active', state.bratCasing === 'upper');
      bratCasingToggleBtn.textContent = state.bratCasing === 'upper' ? 'UPPERCASE' : 'lowercase';
      syncBratContainerClasses();
      updateBratText(bratSandboxInput ? bratSandboxInput.value : '365 PARTYGIRL');
      showToast(`Brat casing: ${state.bratCasing.toUpperCase()}`);
    });
  }

  // Brat Bold Weight Toggle
  if (bratBoldToggleBtn) {
    bratBoldToggleBtn.addEventListener('click', () => {
      state.bratBold = !state.bratBold;
      bratBoldToggleBtn.classList.toggle('active', state.bratBold);
      syncBratContainerClasses();
      autoFitBratText(
        document.getElementById('brat-live-text') || document.getElementById('bratTextBox') || bratLiveText,
        document.querySelector('.brat-box-container') || bratLiveContainer
      );
      showToast(`Brat weight: ${state.bratBold ? 'BOLD' : 'REGULAR'}`);
    });
  }

  // Brat Preset Chips
  bratChipBtns.forEach((chip) => {
    chip.addEventListener('click', () => {
      bratChipBtns.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const presetText = chip.dataset.preset || chip.textContent.trim();
      const chipTheme = chip.dataset.theme || 'green';
      const chipCasing = chip.dataset.casing || 'upper';
      const chipBold = chip.dataset.bold === 'true';
      const chipSong = chip.dataset.song || '';

      // 1. Update text input
      if (bratSandboxInput) bratSandboxInput.value = presetText;

      // 2. Update song query bar
      if (chipSong && songQueryInput) {
        songQueryInput.value = chipSong;
        state.lastQuery = chipSong;
      }

      // 3. Update theme palette
      state.bratTheme = chipTheme;
      bratPalettes.forEach(b => {
        b.classList.toggle('active', b.dataset.theme === chipTheme);
      });

      // 4. Update casing state & toggle button
      state.bratCasing = chipCasing;
      if (bratCasingToggleBtn) {
        bratCasingToggleBtn.classList.toggle('active', state.bratCasing === 'upper');
        bratCasingToggleBtn.textContent = state.bratCasing === 'upper' ? 'UPPERCASE' : 'lowercase';
      }

      // 5. Update bold state & toggle button
      state.bratBold = chipBold;
      if (bratBoldToggleBtn) {
        bratBoldToggleBtn.classList.toggle('active', state.bratBold);
      }

      // 6. Update container classes
      syncBratContainerClasses();

      // 7. Update text display with dynamic wrap and reflow
      updateBratText(presetText, true);
      showToast(`Preset: "${chip.textContent.trim()}"`);
    });
  });

  // Font Selection
  fontBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      fontBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.fontFamily = btn.dataset.font;
      if (customFontInput) customFontInput.value = '';
      showToast(`Font set to ${btn.dataset.font}`);
    });
  });

  // Custom Font Input
  if (customFontInput) {
    customFontInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (val) {
        fontBtns.forEach(b => b.classList.remove('active'));
        state.fontFamily = val;
      }
    });
  }

  // Language Selection
  langBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      langBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.language = btn.dataset.lang;
      if (customLangInput) customLangInput.value = '';
      showToast(`Language set to ${btn.textContent.trim()}`);
    });
  });

  // Custom Language Input
  if (customLangInput) {
    customLangInput.addEventListener('input', (e) => {
      const val = e.target.value.trim().toLowerCase();
      if (val) {
        langBtns.forEach(b => b.classList.remove('active'));
        state.language = val;
      }
    });
  }

  // Search Bar Placement Pills
  placementPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      placementPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.placement = pill.dataset.placement;
      state.ypos = parseInt(pill.dataset.ypos) || 50;
      if (pill.dataset.xpos) state.xpos = parseInt(pill.dataset.xpos) || 50;
      applyRealtimePlacementAndSize(true);
    });
  });

  // Search Bar Horizontal (X) Placement Range Slider (Realtime)
  if (xposSlider) {
    xposSlider.addEventListener('input', (e) => {
      state.xpos = parseInt(e.target.value);
      applyRealtimePlacementAndSize(true);
    });
  }

  // Search Bar Vertical (Y) Placement Range Slider (Realtime)
  if (yposSlider) {
    yposSlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      state.ypos = val;
      state.placement = val <= 25 ? 'top' : (val >= 75 ? 'bottom' : 'center');
      applyRealtimePlacementAndSize(true);
    });
  }

  // Search Bar Font Size Range Slider (Realtime)
  if (fontsizeSlider) {
    fontsizeSlider.addEventListener('input', (e) => {
      state.fontSize = parseInt(e.target.value);
      applyRealtimePlacementAndSize(true);
    });
  }

  // Search Bar Blur Meter Range Slider (Realtime)
  if (blurSlider) {
    blurSlider.addEventListener('input', (e) => {
      state.blur = parseFloat(e.target.value);
      applyRealtimePlacementAndSize(true);
    });
  }

  // Search Bar Spacing Range Slider (Realtime)
  if (spacingSlider) {
    spacingSlider.addEventListener('input', (e) => {
      state.spacing = parseInt(e.target.value);
      applyRealtimePlacementAndSize(true);
    });
  }

  // Search Bar Word Spacing Range Slider (Realtime)
  if (wordSpacingSlider) {
    wordSpacingSlider.addEventListener('input', (e) => {
      state.wordSpacing = parseInt(e.target.value);
      applyRealtimePlacementAndSize(true);
    });
  }

  // YT Hindi Top Header Input
  if (ytHindiTopHeaderInput) {
    ytHindiTopHeaderInput.addEventListener('input', (e) => {
      state.topHeader = e.target.value.trim();
    });
  }

  // Test Range & Preview Quality Inputs
  if (testStartInput) {
    testStartInput.addEventListener('input', (e) => {
      state.testStart = e.target.value.trim();
    });
  }
  if (testEndInput) {
    testEndInput.addEventListener('input', (e) => {
      state.testEnd = e.target.value.trim();
    });
  }
  if (previewQualityInput) {
    previewQualityInput.addEventListener('change', (e) => {
      state.previewQuality = e.target.value;
    });
  }

  // Backdrop Switcher
  backdropBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      setBackdrop(btn.dataset.bg);
    });
  });

  // Refresh Gallery
  refreshGalleryBtn.addEventListener('click', loadVideosGallery);

  // Video Time Update for Synchronized Teleprompter
  outputVideoPlayer.addEventListener('timeupdate', () => {
    syncTeleprompter(outputVideoPlayer.currentTime);
  });
}

// Brat Word-by-Word Accumulation & Auto-Fit Engine
let bratAccumulationTimer = null;

// Dynamic Auto-Fit Resizing Algorithm: iteratively shrinks font size to fit container limits
function autoFitBratText(box, container) {
  if (!box || !container) return;

  const text = box.textContent.trim();
  if (!text) return;

  const scale = 0.68;
  const cWidth = container.clientWidth || 320;
  const cHeight = container.clientHeight || 320;
  const maxSafeW = cWidth * 0.88;
  const maxSafeH = cHeight * 0.85;

  let fontSize = Math.min(state.fontSize || 72, 85);
  box.style.fontSize = `${fontSize}px`;

  // Reduce font size iteratively until visual content fits safely inside bounding box
  while (fontSize > 16) {
    const visualW = (box.scrollWidth || box.offsetWidth) * scale;
    const visualH = box.scrollHeight || box.offsetHeight;
    if (visualW <= maxSafeW && visualH <= maxSafeH) {
      break;
    }
    fontSize -= 2;
    box.style.fontSize = `${fontSize}px`;
  }
}

// Render cumulative words step with dynamic font-sizing and reflow
function renderWordStep(wordsArray, currentIndex) {
  const container = document.querySelector(".brat-box-container") || bratLiveContainer;
  const box = document.getElementById("brat-live-text") || document.getElementById("bratTextBox") || bratLiveText;
  if (!box || !container) return;
  if (!wordsArray || wordsArray.length === 0) {
    box.textContent = '';
    return;
  }

  const boundedIndex = Math.min(wordsArray.length - 1, Math.max(0, currentIndex));
  const rawText = wordsArray.slice(0, boundedIndex + 1).join(" ");
  const currentText = state.bratCasing === 'lower' ? rawText.toLowerCase() : rawText.toUpperCase();

  box.textContent = currentText;

  // Trigger Crisp Word Entry Pop
  box.classList.remove("motion-blur-active");
  void box.offsetWidth; // Force DOM reflow
  box.classList.add("motion-blur-active");

  // Dynamic iterative auto-fit calculation
  autoFitBratText(box, container);
}

function animateBratWordAccumulation(text) {
  if (bratAccumulationTimer) {
    clearInterval(bratAccumulationTimer);
    bratAccumulationTimer = null;
  }

  const raw = text !== undefined ? text : (bratSandboxInput ? bratSandboxInput.value : '365 PARTYGIRL');
  const words = (raw || '365 PARTYGIRL').trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return;

  let currentIdx = 0;
  renderWordStep(words, 0);

  if (words.length > 1) {
    bratAccumulationTimer = setInterval(() => {
      currentIdx++;
      if (currentIdx < words.length) {
        renderWordStep(words, currentIdx);
      } else {
        clearInterval(bratAccumulationTimer);
        bratAccumulationTimer = null;
      }
    }, 120);
  }
}

function updateBratText(input, animate = false) {
  if (animate) {
    animateBratWordAccumulation(input);
    return;
  }

  if (bratAccumulationTimer) {
    clearInterval(bratAccumulationTimer);
    bratAccumulationTimer = null;
  }

  const container = document.querySelector(".brat-box-container") || bratLiveContainer;
  const box = document.getElementById("brat-live-text") || document.getElementById("bratTextBox") || bratLiveText;
  if (!box || !container) return;

  const raw = input !== undefined ? String(input) : (bratSandboxInput ? bratSandboxInput.value : '365 PARTYGIRL');
  const currentText = state.bratCasing === 'lower' ? raw.toLowerCase() : raw.toUpperCase();
  box.textContent = currentText;

  // Auto-scale font size dynamically to fit bounding box
  autoFitBratText(box, container);
}

function updatePlacementPills(place) {
  placementPills.forEach(p => p.classList.toggle('active', p.dataset.placement === place));
}

function applyRealtimePlacementAndSize() {
  // 1. Move Brat Live Canvas text in realtime (X, Y translation, dynamic blur filter, letter-spacing, and word-spacing)
  const bratText = document.getElementById("brat-live-text") || document.getElementById("bratTextBox") || bratLiveText;
  const bratContainer = document.querySelector(".brat-box-container") || bratLiveContainer;
  if (bratText && bratContainer) {
    const offsetX = ((state.xpos - 50) * 0.75);
    const offsetY = ((state.ypos - 50) * 0.75);
    bratText.style.transform = `scaleX(0.68) translate(${offsetX}%, ${offsetY}%)`;
    const effContrast = Math.round(140 + (state.blur * 4.5));
    bratText.style.filter = `blur(${state.blur}px) contrast(${effContrast}%)`;
    bratText.style.letterSpacing = `${state.spacing}px`;
    bratText.style.wordSpacing = `${state.wordSpacing}px`;
    autoFitBratText(bratText, bratContainer);
  }

  // 2. Keep Badges and Slider Inputs in Sync
  if (xposSlider) xposSlider.value = state.xpos;
  const xDesc = state.xpos === 50 ? ' (Center)' : (state.xpos < 50 ? ' (Left)' : ' (Right)');
  if (xposVal) xposVal.textContent = `${state.xpos}%${xDesc}`;

  if (yposSlider) yposSlider.value = state.ypos;
  if (yposVal) yposVal.textContent = `${state.ypos}% (${state.placement.toUpperCase()})`;

  if (fontsizeSlider) fontsizeSlider.value = state.fontSize;
  if (fontsizeVal) fontsizeVal.textContent = `${state.fontSize}px${state.fontSize === 72 ? ' (Default)' : ''}`;

  if (blurSlider) blurSlider.value = state.blur;
  if (blurVal) blurVal.textContent = `${state.blur}px`;

  if (spacingSlider) spacingSlider.value = state.spacing;
  if (spacingVal) spacingVal.textContent = `${state.spacing}px${state.spacing === -1 ? ' (Default)' : ''}`;

  if (wordSpacingSlider) wordSpacingSlider.value = state.wordSpacing;
  if (wordSpacingVal) wordSpacingVal.textContent = `${state.wordSpacing}px${state.wordSpacing === 0 ? ' (Default)' : ''}`;

  updatePlacementPills(state.placement);
}

function parseTimeString(val) {
  if (val === null || val === undefined) return NaN;
  const str = String(val).trim();
  if (!str) return NaN;
  if (str.includes(':')) {
    const parts = str.split(':').map(Number);
    if (parts.some(isNaN)) return NaN;
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
  }
  const num = Number(str);
  return isNaN(num) ? NaN : num;
}

// 1. Start Server-Sent Events (SSE) Video Generation
function startGenerationPipeline(query) {
  state.lastQuery = query;
  if (state.isGenerating && state.currentEventSource) {
    state.currentEventSource.close();
  }

  state.isGenerating = true;
  generateBtn.disabled = true;
  btnText.textContent = 'Generating 1080p MP4...';
  generateBtn.classList.add('loading');

  // Reset & show pipeline UI
  resetPipelineUI(query);
  pipelineSection.style.display = 'block';
  pipelineSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Connect to SSE Endpoint
  const isYtHindi = ['yt_hindi_type', 'yt_hindi_intro'].includes(state.template);
  const isYtHindiIntro = state.template === 'yt_hindi_intro' || (isYtHindi && state.ytHindiVariant === 'film_burn');
  const topHeaderParam = isYtHindi ? `&top_header=${encodeURIComponent(state.topHeader || '')}` : '';
  const introHeaderParam = isYtHindiIntro ? `&intro_header=${encodeURIComponent(state.introHeader || '')}` : '';
  const rawStart = (testStartInput && testStartInput.value.trim() !== '') ? testStartInput.value.trim() : (state.testStart !== '' && state.testStart !== null && state.testStart !== undefined && state.testStart !== 0 ? String(state.testStart) : '');
  const rawEnd = (testEndInput && testEndInput.value.trim() !== '') ? testEndInput.value.trim() : (state.testEnd !== '' && state.testEnd !== null && state.testEnd !== undefined ? String(state.testEnd) : '');
  const numStart = parseTimeString(rawStart);
  const numEnd = parseTimeString(rawEnd);
  const hasStart = rawStart !== '' && !isNaN(numStart) && numStart >= 0;
  const hasEnd = rawEnd !== '' && !isNaN(numEnd) && numEnd > 0;
  const hasTimingWindow = (hasStart && numStart > 0) || hasEnd;
  const testStartParam = (hasTimingWindow && hasStart) ? `&start_seconds=${encodeURIComponent(numStart)}` : '';
  const testEndParam = (hasTimingWindow && hasEnd) ? `&end_seconds=${encodeURIComponent(numEnd)}` : '';
  const qualityParam = `&preview_quality=${encodeURIComponent(state.previewQuality || 'final')}`;
  const masterVariantParam = state.template === 'master_lyrics' ? `&master_variant=${encodeURIComponent(state.masterVariant || 'default')}` : '';
  const ytHindiVariantParam = ['yt_hindi_type', 'yt_hindi_intro'].includes(state.template) ? `&yt_hindi_variant=${encodeURIComponent(state.ytHindiVariant || 'standard')}` : '';
  const nokiaScreenColorParam = state.template === 'c19_nokia' ? `&nokia_screen_color=${encodeURIComponent(state.nokiaScreenColor || '#b40000')}` : '';
  const nokiaStickerParam = (state.template === 'c19_nokia' && state.nokiaStickersEnabled) ? `&nokia_sticker=${encodeURIComponent(state.nokiaSticker || 'random')}` : '';
  const bratBoldParam = ['template4_brat', 'template_4_brat', 'brat'].includes(state.template) ? `&brat_bold=${encodeURIComponent(state.bratBold ? 'true' : 'false')}` : '';
  const bratCasingParam = ['template4_brat', 'template_4_brat', 'brat'].includes(state.template) ? `&brat_casing=${encodeURIComponent(state.bratCasing || 'upper')}` : '';
  let bgFoldersParam = '';
  if (isYtHindi) {
    if (state.selectedBgFolders && state.selectedBgFolders.length === 0) {
      bgFoldersParam = '&bg_folders=none';
    } else if (state.selectedBgFolders && state.selectedBgFolders.length > 0) {
      bgFoldersParam = `&bg_folders=${encodeURIComponent(state.selectedBgFolders.join(','))}`;
    }
  }
  const sseUrl = `/api/generate-video-stream?q=${encodeURIComponent(query)}&template=${encodeURIComponent(state.template)}&font=${encodeURIComponent(state.fontFamily)}&fontsize=${encodeURIComponent(state.fontSize)}&blur=${encodeURIComponent(state.blur)}&spacing=${encodeURIComponent(state.spacing)}&word_spacing=${encodeURIComponent(state.wordSpacing)}&lang=${encodeURIComponent(state.language)}&placement=${encodeURIComponent(state.placement)}&ypos=${encodeURIComponent(state.ypos)}&xpos=${encodeURIComponent(state.xpos)}&brat_theme=${encodeURIComponent(state.bratTheme)}${bratBoldParam}${bratCasingParam}${bgFoldersParam}${topHeaderParam}${introHeaderParam}${testStartParam}${testEndParam}${qualityParam}${masterVariantParam}${ytHindiVariantParam}${nokiaScreenColorParam}${nokiaStickerParam}`;
  const eventSource = new EventSource(sseUrl);
  state.currentEventSource = eventSource;
  state.generationErrorHandled = false;

  eventSource.addEventListener('start', (e) => {
    const data = JSON.parse(e.data);
    appendConsoleLog(`[START] ${data.message}`);
  });

  eventSource.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data);
    handleProgressUpdate(data);
  });

  eventSource.addEventListener('log', (e) => {
    const data = JSON.parse(e.data);
    appendConsoleLog(data.message);
  });

  eventSource.addEventListener('complete', (e) => {
    try {
      const data = JSON.parse(e.data);
      handleGenerationComplete(data);
    } finally {
      eventSource.close();
      state.currentEventSource = null;
      state.isGenerating = false;
      generateBtn.disabled = false;
      btnText.textContent = 'Generate Video Overlay';
      generateBtn.classList.remove('loading');
    }
  });

  const handleError = (e) => {
    if (state.generationErrorHandled) return;
    state.generationErrorHandled = true;
    console.error('SSE Error:', e);
    appendConsoleLog('[ERROR] Video generation pipeline failed or connection closed.');
    pipelineStatusText.textContent = 'Generation Failed (Check console output)';
    eventSource.close();
    state.currentEventSource = null;
    state.isGenerating = false;
    generateBtn.disabled = false;
    btnText.textContent = 'Generate Video Overlay';
    generateBtn.classList.remove('loading');
    showToast('Generation finished or disconnected.');
  };

  eventSource.addEventListener('error', handleError);
  eventSource.onerror = handleError;
}

window.addEventListener('beforeunload', () => {
  if (state.currentEventSource) {
    state.currentEventSource.close();
    state.currentEventSource = null;
  }
});

// 2. Handle Progress Updates from Python Generator
function handleProgressUpdate(data) {
  const { step, percent, message, details } = data;

  // Update progress bar
  progressBarFill.style.width = `${percent}%`;
  pipelinePercentBadge.textContent = `${percent}%`;
  pipelineStatusText.textContent = message;

  appendConsoleLog(`[${percent}%] ${message}`);
  if (details && Object.keys(details).length) {
    const detailText = Object.entries(details)
      .filter(([key]) => !['title', 'uploader'].includes(key))
      .map(([key, value]) => `${key}=${typeof value === 'object' ? JSON.stringify(value) : value}`)
      .join(' | ');
    if (detailText) appendConsoleLog(`[DETAIL] ${detailText}`);
  }

  // Step-specific updates
  if (step === 'ytdlp_start' || step === 'ytdlp_downloading') {
    markStepActive(stepAudio, stepAudioStatus, stepAudioDetail, 'Downloading MP3 audio...');
    markStepActive(stepLyrics, stepLyricsStatus, stepLyricsDetail, 'Fetching YouTube subtitles & captions...');
  } else if (step === 'ytdlp_done') {
    markStepDone(stepAudio, stepAudioStatus, stepAudioDetail, `Extracted audio (${details.duration || 0}s)`);
    markStepDone(stepLyrics, stepLyricsStatus, stepLyricsDetail, `Extracted ${details.subtitles_count || 1} caption stream(s)`);
  } else if (step === 'ass_start') {
    markStepActive(stepAss, stepAssStatus, stepAssDetail, 'Formatting 1080p canvas...');
  } else if (step === 'ass_done') {
    markStepDone(stepAss, stepAssStatus, stepAssDetail, 'Generated styled 1080p ASS');
  } else if (step === 'ffmpeg_start' || step === 'ffmpeg_rendering') {
    markStepActive(stepFfmpeg, stepFfmpegStatus, stepFfmpegDetail, 'Rendering 1080p video...');
  } else if (step === 'ffmpeg_done' || step === 'completed') {
    markStepDone(stepFfmpeg, stepFfmpegStatus, stepFfmpegDetail, '1080p MP4 Ready!');
  }
}

// 3. Handle Generation Complete
function handleGenerationComplete(data) {
  progressBarFill.style.width = '100%';
  pipelinePercentBadge.textContent = '100%';
  pipelineStatusText.textContent = '🎉 1080p Video Ready for Download!';

  state.activeVideoUrl = data.videoUrl;
  state.activeMetadata = data.metadata;
  state.syncedLines = data.metadata?.syncedLines || [];
  renderGenerationMetrics(data.metadata?.metrics);

  showToast('🎉 1080p MP4 Ready for Download! 🚀');

  const isSquare = (data.metadata?.aspect_ratio === 'square') || state.template === 'c19_nokia';
  const isPortrait = !isSquare && ((data.metadata?.aspect_ratio || 'portrait') === 'portrait');
  const tplUsed = (data.metadata?.template || state.template || 'template1').replace('template', 'Template ');

  // Populate Studio Stage
  stageSongTitle.textContent = data.metadata?.track_name || data.query;
  const outputResolution = data.metadata?.metrics?.resolution || (isSquare ? '1080x1080' : (isPortrait ? '1080x1920' : '1920x1080'));
  const outputShape = isSquare ? '1:1 Square' : (isPortrait ? '9:16 Portrait' : '16:9 Landscape');
  stageSongMeta.textContent = `${data.metadata?.artist_name || 'YouTube Video'} &bull; ${data.metadata?.duration || 0}s duration &bull; ${outputResolution} MP4 (${outputShape}) &bull; ${tplUsed.toUpperCase()}`;

  // Toggle Portrait frame styling on video container
  if (videoPreviewWrapper) {
    videoPreviewWrapper.classList.toggle('portrait-mode', isPortrait);
  }

  // Set Video Player source
  try {
    outputVideoPlayer.pause();
    if (videoSource) videoSource.src = data.videoUrl;
    outputVideoPlayer.load();
    const playPromise = outputVideoPlayer.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {});
    }
  } catch (err) {
    console.warn("Video player initialization note:", err);
  }

  applyRealtimePlacementAndSize();

  // Setup Download Links
  dlVideoBtn.href = data.videoUrl;
  dlVideoBtn.download = data.videoFileName || 'lyric_video.mp4';

  if (data.metadata?.syncedLines) {
    setupAssetDownloadBlobs(data.metadata);
  }

  // Populate Teleprompter
  renderTeleprompter(state.syncedLines);

  studioStage.style.display = 'block';
  studioStage.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Reload Gallery
  setTimeout(loadVideosGallery, 1000);
}

function renderGenerationMetrics(metrics) {
  if (!generationMetrics || !generationMetricsGrid) return;
  if (!metrics) {
    generationMetrics.hidden = true;
    generationMetricsGrid.replaceChildren();
    return;
  }

  const format = (value, suffix = '') => value === null || value === undefined
    ? 'Unavailable'
    : `${value}${suffix}`;
  const items = [
    ['Total time', format(metrics.wall_time_seconds, ' s')],
    ['Render time', format(metrics.render_time_seconds, ' s')],
    ['Render speed', format(metrics.render_speed_x, 'x realtime')],
    ['Render speed (no download)', format(metrics.render_speed_x_excluding_download, 'x realtime')],
    ['Peak memory', format(metrics.peak_memory_mb, ' MB')],
    ['Output size', format(metrics.output_size_mb, ' MB')],
    ['Encoder', format(metrics.encoder)],
    ['CPU time', format(metrics.python_cpu_time_seconds, ' s')],
    ['Resolution', format(metrics.resolution)],
    ['Frame rate', format(metrics.fps, ' fps')]
  ];

  generationMetricsGrid.replaceChildren(...items.map(([label, value]) => {
    const item = document.createElement('div');
    item.className = 'metric-item';
    item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    return item;
  }));
  generationMetrics.hidden = false;
}

// 4. Setup Asset Blobs for .ass and .lrc download buttons
function setupAssetDownloadBlobs(meta) {
  if (meta.rawLrc) {
    const lrcBlob = new Blob([meta.rawLrc], { type: 'application/x-subrip' });
    dlLrcBtn.href = URL.createObjectURL(lrcBlob);
    dlLrcBtn.download = `${(meta.track_name || 'lyrics').replace(/\s+/g, '_')}.lrc`;
    dlLrcBtn.style.display = 'inline-flex';
  } else {
    dlLrcBtn.style.display = 'none';
  }

  // ASS download
  if (meta.syncedLines) {
    const assContent = generateAssBlobContent(meta);
    const assBlob = new Blob([assContent], { type: 'text/plain' });
    dlAssBtn.href = URL.createObjectURL(assBlob);
    dlAssBtn.download = `${(meta.track_name || 'subtitles').replace(/\s+/g, '_')}.ass`;
    dlAssBtn.style.display = 'inline-flex';
  }
}

function generateAssBlobContent(meta) {
  const header = `[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,30,30,60,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n`;
  const lines = (meta.syncedLines || []).map(l => `Dialogue: 0,0:${l.timestamp || '00:00'},0:${l.timestamp || '00:04'},Default,,0,0,0,,${l.text}`).join('\n');
  return header + lines;
}

// 5. Synchronized Teleprompter
function renderTeleprompter(lines) {
  teleprompterStream.innerHTML = '';
  teleprompterCount.textContent = `${lines.length} lines`;

  if (!lines || lines.length === 0) {
    teleprompterStream.innerHTML = '<div style="padding:1rem; color:var(--text-muted);">No synchronized lines available.</div>';
    return;
  }

  lines.forEach((line, idx) => {
    const row = document.createElement('div');
    row.className = 'teleprompter-row';
    row.dataset.index = idx;
    row.dataset.time = line.timeSeconds;

    row.innerHTML = `
      <span class="teleprompter-time">${escapeHtml(line.timestamp || '')}</span>
      <span class="teleprompter-text">${escapeHtml(line.text)}</span>
    `;

    // Click to seek video
    row.addEventListener('click', () => {
      outputVideoPlayer.currentTime = line.timeSeconds;
      if (outputVideoPlayer.paused) outputVideoPlayer.play();
    });

    teleprompterStream.appendChild(row);
  });
}

function syncTeleprompter(currentTime) {
  if (!state.syncedLines || !Array.isArray(state.syncedLines) || state.syncedLines.length === 0) return;

  let activeIndex = -1;
  for (let i = 0; i < state.syncedLines.length; i++) {
    const s = state.syncedLines[i];
    if (s && s.timeSeconds !== undefined && s.timeSeconds <= currentTime) {
      activeIndex = i;
    } else {
      break;
    }
  }

  const isBrat = state.template === 'template4_brat' || state.template === 'template_4_brat' || state.template === 'brat';
  const box = document.getElementById("brat-live-text") || document.getElementById("bratTextBox") || bratLiveText;

  if (activeIndex < 0) {
    if (isBrat && box && outputVideoPlayer && !outputVideoPlayer.paused) {
      box.textContent = '';
      lastRenderedWordCount = -1;
    }
  } else if (state.syncedLines[activeIndex]) {
    const activeLine = state.syncedLines[activeIndex];
    const lineEnd = (activeLine.endSeconds !== undefined && activeLine.endSeconds > activeLine.timeSeconds) ? activeLine.endSeconds : (activeLine.timeSeconds + 2.8);
    
    if (isBrat && activeLine.text) {
      if (currentTime >= activeLine.timeSeconds && currentTime <= lineEnd + 0.25) {
        const words = activeLine.text.trim().split(/\s+/).filter(Boolean);
        if (words.length > 0) {
          const lineDur = Math.max(0.4, lineEnd - activeLine.timeSeconds);
          const typeDur = lineDur * 0.85;
          const elapsed = Math.max(0, currentTime - activeLine.timeSeconds);
          const progress = Math.min(1, elapsed / typeDur);
          const wordIdx = Math.min(words.length - 1, Math.floor(progress * words.length));

          if (wordIdx !== lastRenderedWordCount || activeIndex !== state.currentLineIndex) {
            lastRenderedWordCount = wordIdx;
            renderWordStep(words, wordIdx);
          }
        }
      } else if (currentTime > lineEnd + 0.25 && (activeIndex + 1 >= state.syncedLines.length || currentTime < state.syncedLines[activeIndex + 1].timeSeconds)) {
        if (box && outputVideoPlayer && !outputVideoPlayer.paused) {
          box.textContent = '';
          lastRenderedWordCount = -1;
        }
      }
    }
  }

  if (activeIndex !== state.currentLineIndex) {
    state.currentLineIndex = activeIndex;
    const allRows = teleprompterStream ? teleprompterStream.querySelectorAll('.teleprompter-row') : [];
    allRows.forEach((row, idx) => {
      const isActive = idx === activeIndex;
      const isPast = idx < activeIndex;
      row.classList.toggle('active', isActive);
      row.classList.toggle('past', isPast);
    });

    // Auto-scroll the internal teleprompter container so active line stays visible
    if (activeIndex >= 0 && allRows[activeIndex] && teleprompterStream) {
      const activeRow = allRows[activeIndex];
      const targetScroll = activeRow.offsetTop - teleprompterStream.offsetTop - (teleprompterStream.clientHeight / 2) + (activeRow.clientHeight / 2);
      teleprompterStream.scrollTo({
        top: Math.max(0, targetScroll),
        behavior: 'smooth'
      });
    }
  }
}

// 6. Backdrop Switcher (Demonstrating Alpha Channel & Brat Background)
function setBackdrop(bgType) {
  state.currentBackdrop = bgType;
  backdropBtns.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.bg === bgType);
  });

  videoBackdrop.className = `video-backdrop backdrop-${bgType}`;
}

// 7. Load & Render Previously Generated Videos Gallery
async function loadVideosGallery() {
  try {
    const res = await fetch('/api/videos');
    const data = await res.json();

    if (!data.videos || data.videos.length === 0) {
      videosGalleryGrid.innerHTML = `
        <div class="gallery-empty">
          <p>No generated video files found yet. Type a song name above to generate your first transparent overlay!</p>
        </div>
      `;
      return;
    }

    videosGalleryGrid.innerHTML = '';
    data.videos.forEach((vid) => {
      const card = document.createElement('div');
      card.className = 'gallery-card';

      const cleanTitle = vid.filename
        .replace(/\.(mp4|webm)$/, '')
        .replace(/_[0-9]+$/, '')
        .replace(/[_-]/g, ' ');

      card.innerHTML = `
        <div class="gallery-video-thumb backdrop-checkerboard">
          <video src="${vid.url}" preload="metadata" muted playsinline></video>
          <div class="play-overlay-icon">▶</div>
        </div>
        <div class="gallery-card-body">
          <strong class="gallery-card-title" title="${escapeHtml(cleanTitle)}">${escapeHtml(cleanTitle)}</strong>
          <span class="gallery-card-meta">${vid.sizeMb} MB &bull; 1080p ${(vid.format || 'mp4').toUpperCase()} Video</span>
          <div class="gallery-card-actions">
            <button class="mini-btn play-gallery-btn">Preview</button>
            <a href="${vid.url}" download="${vid.filename}" class="mini-btn" target="_blank">Download</a>
          </div>
        </div>
      `;

      card.querySelector('.play-gallery-btn').addEventListener('click', () => {
        outputVideoPlayer.pause();
        videoSource.src = vid.url;
        outputVideoPlayer.load();
        outputVideoPlayer.play().catch(() => {});
        stageSongTitle.textContent = cleanTitle;
        stageSongMeta.textContent = `${vid.sizeMb} MB &bull; 1080p 30fps Transparent Overlay`;
        studioStage.style.display = 'block';
        studioStage.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });

      videosGalleryGrid.appendChild(card);
    });
  } catch (e) {
    console.warn('Could not load videos gallery:', e);
  }
}

// UI Helpers
function resetPipelineUI(query) {
  progressBarFill.style.width = '5%';
  pipelinePercentBadge.textContent = '0%';
  pipelineStatusText.textContent = `Starting pipeline for "${query}"...`;
  consoleStream.innerHTML = '';
  logCount = 0;
  consoleLineCount.textContent = '0 lines';
  if (generationMetrics) generationMetrics.hidden = true;
  if (generationMetricsGrid) generationMetricsGrid.replaceChildren();

  resetStep(stepAudio, stepAudioStatus, stepAudioDetail, 'Waiting to start...');
  resetStep(stepLyrics, stepLyricsStatus, stepLyricsDetail, 'Waiting to start...');
  resetStep(stepAss, stepAssStatus, stepAssDetail, 'Waiting...');
  resetStep(stepFfmpeg, stepFfmpegStatus, stepFfmpegDetail, 'Waiting...');
}

function resetStep(card, status, detail, text) {
  card.className = 'step-card';
  status.textContent = '⏳';
  detail.textContent = text;
}

function markStepActive(card, status, detail, text) {
  card.className = 'step-card active';
  status.innerHTML = '<span class="spinner" style="width:14px; height:14px; margin:0; border-width:2px; display:inline-block;"></span>';
  detail.textContent = text;
}

function markStepDone(card, status, detail, text) {
  card.className = 'step-card done';
  status.textContent = '✅';
  detail.textContent = text;
}

function appendConsoleLog(msg) {
  logCount++;
  consoleLineCount.textContent = `${logCount} lines`;
  const line = document.createElement('div');
  line.className = 'console-line';
  line.textContent = `> ${msg}`;
  consoleStream.appendChild(line);
  consoleStream.scrollTop = consoleStream.scrollHeight;
}

function showToast(msg) {
  toastMessage.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// ==========================================
// Instagram Music Heatmap & Viral Hook Functions
// ==========================================

async function checkInstagramStatus() {
  try {
    if (igStatusBadge) igStatusBadge.textContent = 'IG Status: Checking...';
    const res = await fetch('/api/instagram/status');
    const data = await res.json();
    state.isIgLoggedIn = !!data.logged_in;

    if (state.isIgLoggedIn) {
      if (igStatusBadge) {
        igStatusBadge.textContent = '✅ IG: Logged In';
        igStatusBadge.className = 'badge badge-accent';
        igStatusBadge.style.color = '#4ade80';
      }
      if (igLoginBtn) igLoginBtn.style.display = 'none';
      if (fetchHooksBtn) fetchHooksBtn.style.display = 'inline-block';
    } else {
      if (igStatusBadge) {
        igStatusBadge.textContent = '⚠️ IG: Not Logged In';
        igStatusBadge.className = 'badge badge-subtle';
        igStatusBadge.style.color = '#f87171';
      }
      if (igLoginBtn) igLoginBtn.style.display = 'inline-block';
    }
  } catch (err) {
    console.error('Check IG status error:', err);
    if (igStatusBadge) igStatusBadge.textContent = 'IG: Offline';
  }
}

async function triggerInstagramLogin() {
  try {
    showToast('🚀 Opening Chrome for Instagram login... Please log in in the opened browser window.');
    if (igLoginBtn) {
      igLoginBtn.disabled = true;
      igLoginBtn.textContent = '⏳ Waiting for Chrome Login...';
    }
    if (igStatusBadge) igStatusBadge.textContent = 'IG: Logging in...';

    const res = await fetch('/api/instagram/login', { method: 'POST' });
    const data = await res.json();

    if (res.ok && data.status === 'success') {
      showToast('🎉 Instagram logged in successfully!');
      state.isIgLoggedIn = true;
      await checkInstagramStatus();
      const query = songQueryInput ? songQueryInput.value.trim() : '';
      if (query) {
        fetchViralHooks(query, true);
      }
    } else {
      showToast(`Login notice: ${data.error || 'Login not completed.'}`);
    }
  } catch (err) {
    console.error('IG login trigger error:', err);
    showToast('Failed to start Instagram Chrome login helper.');
  } finally {
    if (igLoginBtn) {
      igLoginBtn.disabled = false;
      igLoginBtn.textContent = '🔑 Open Chrome & Login';
    }
    checkInstagramStatus();
  }
}

async function fetchViralHooks(query, openModalOnSuccess = false) {
  if (!query) return;
  try {
    if (fetchHooksBtn) {
      fetchHooksBtn.disabled = true;
      fetchHooksBtn.textContent = '⏳ Fetching Hooks...';
    }
    showToast(`🔍 Extracting Instagram viral hooks for "${query}"...`);

    const res = await fetch(`/api/viral-hooks?q=${encodeURIComponent(query)}&clip_len=15`);
    if (res.status === 401) {
      showToast('⚠️ Instagram session required. Please log into Instagram first.');
      if (confirm('Instagram login required to extract viral hooks.\n\nOpen Chrome to log in now?')) {
        triggerInstagramLogin();
      }
      return;
    }

    const data = await res.json();
    if (!res.ok || data.error) {
      showToast(data.message || data.error || 'No viral hooks found for this track.');
      return;
    }

    state.availableHooks = data.all_hooks || [];

    if (state.availableHooks.length > 0) {
      populateHookDropdown(data);
      showToast(`✨ Found ${state.availableHooks.length} viral hooks for "${data.title || query}"!`);

      if (openModalOnSuccess) {
        showHookModal(data);
      }
    } else {
      showToast('No specific hook timestamps found. You can render the full song.');
    }
  } catch (err) {
    console.error('Fetch hooks error:', err);
    showToast('Could not fetch Instagram hooks.');
  } finally {
    if (fetchHooksBtn) {
      fetchHooksBtn.disabled = false;
      fetchHooksBtn.textContent = '🔍 Fetch IG Hooks';
    }
  }
}

function populateHookDropdown(data) {
  if (!viralHookSelect) return;
  viralHookSelect.innerHTML = '';

  const fullOpt = document.createElement('option');
  fullOpt.value = 'full';
  fullOpt.textContent = `🎵 Full Song (${data.duration_formatted || 'Full'})`;
  viralHookSelect.appendChild(fullOpt);

  data.all_hooks.forEach((hook) => {
    const opt = document.createElement('option');
    opt.value = String(hook.start_ms);
    opt.textContent = `${hook.label} (${hook.start_formatted} - ${hook.end_formatted}) [${hook.percentage_offset}%]`;
    if (hook.is_recommended) {
      opt.selected = true;
      state.selectedHook = hook;
      state.testStart = hook.start_seconds;
      state.testEnd = hook.end_seconds;
      if (testStartInput) testStartInput.value = hook.start_seconds;
      if (testEndInput) testEndInput.value = hook.end_seconds;
    }
    viralHookSelect.appendChild(opt);
  });

  const customOpt = document.createElement('option');
  customOpt.value = 'custom';
  customOpt.textContent = '⏱️ Custom Range (Manual)';
  viralHookSelect.appendChild(customOpt);
}

function showHookModal(data) {
  if (!hookModal || !hookModalList) return;
  hookModalList.innerHTML = '';

  const hooks = state.availableHooks || [];

  // Add Full Song Option Card
  const fullCard = document.createElement('div');
  fullCard.style.cssText = 'padding: 12px 16px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s;';
  fullCard.innerHTML = `
    <div>
      <div style="font-weight: 700; font-size: 0.95rem;">🎵 Full Song</div>
      <div style="font-size: 0.78rem; color: #a1a1aa;">Render entire track from 0:00 to end</div>
    </div>
    <span class="badge badge-subtle">Full</span>
  `;
  fullCard.addEventListener('click', () => {
    selectHookAndHighlight(null, fullCard);
  });
  hookModalList.appendChild(fullCard);

  // Add each hook
  hooks.forEach((hook) => {
    const card = document.createElement('div');
    const isRec = hook.is_recommended;
    card.style.cssText = `padding: 12px 16px; border-radius: 10px; background: ${isRec ? 'rgba(225, 48, 108, 0.15)' : 'rgba(255,255,255,0.05)'}; border: 1px solid ${isRec ? '#e1306c' : 'rgba(255,255,255,0.1)'}; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s;`;
    card.innerHTML = `
      <div>
        <div style="font-weight: 700; font-size: 0.95rem; color: ${isRec ? '#ff6b8b' : '#fff'};">${hook.label}</div>
        <div style="font-size: 0.78rem; color: #a1a1aa;">Start: ${hook.start_formatted} (${hook.start_seconds}s) · End: ${hook.end_formatted} (${hook.end_seconds}s) · Track ${hook.percentage_offset}%</div>
      </div>
      <span class="badge ${isRec ? 'badge-accent' : 'badge-subtle'}">${isRec ? '⭐ Top Pick' : 'Viral Hook'}</span>
    `;
    card.addEventListener('click', () => {
      selectHookAndHighlight(hook, card);
    });

    if (isRec) {
      card.style.outline = '2px solid #e1306c';
      state.selectedHook = hook;
      state.testStart = hook.start_seconds;
      state.testEnd = hook.end_seconds;
      if (testStartInput) testStartInput.value = hook.start_seconds;
      if (testEndInput) testEndInput.value = hook.end_seconds;
    }

    hookModalList.appendChild(card);
  });

  hookModal.style.display = 'flex';
}

function selectHookAndHighlight(hook, selectedCard) {
  const cards = hookModalList.querySelectorAll('div');
  cards.forEach(c => {
    c.style.outline = 'none';
  });
  selectedCard.style.outline = '2px solid #e1306c';

  if (!hook) {
    state.selectedHook = null;
    state.testStart = 0;
    state.testEnd = '';
    if (testStartInput) testStartInput.value = 0;
    if (testEndInput) testEndInput.value = '';
    if (viralHookSelect) viralHookSelect.value = 'full';
  } else {
    state.selectedHook = hook;
    state.testStart = hook.start_seconds;
    state.testEnd = hook.end_seconds;
    if (testStartInput) testStartInput.value = hook.start_seconds;
    if (testEndInput) testEndInput.value = hook.end_seconds;
    if (viralHookSelect) viralHookSelect.value = String(hook.start_ms);
  }
}

function hideHookModal() {
  if (hookModal) hookModal.style.display = 'none';
}

/* ==========================================================================
   Streaming Lyrics Card Controller (Spotify & YouTube Music Pipeline)
   ========================================================================== */

const SPOTIFY_PRESET = {
  cardType: 'spotify',
  bgColor: '#4884ab', // Exact Card Primary from Figma template
  secondaryBgColor: '#437795', // Exact Outer Background Secondary
  textColor: 'white',
  radius: 28,
  coverImgUrl: '/api/proxy-image?url=' + encodeURIComponent('https://upload.wikimedia.org/wikipedia/en/5/51/KendrickLamarGoodKidmMADCity.jpg'),
  title: 'Bitch, Don’t Kill My Vibe',
  artist: 'Kendrick Lamar',
  fetchedLines: [
    { time_ms: 0, text: "Fell on my face and awoke" },
    { time_ms: 2500, text: "with a scar, another" },
    { time_ms: 5000, text: "mistake livin' deep in my" },
    { time_ms: 7500, text: "heart" },
    { time_ms: 10000, text: "Wear it on top of my sleeve" },
    { time_ms: 12500, text: "in a flick, I can admit that it" },
    { time_ms: 15000, text: "did look like yours" }
  ],
  selectedLineIndices: new Set([0, 1, 2, 3, 4, 5, 6])
};

const YT_MUSIC_PRESET = {
  cardType: 'yt_music',
  bgColor: '#580539', // Deep Berry Plum from YouTube Music reference
  secondaryBgColor: '#380324',
  textColor: 'white',
  radius: 20,
  coverImgUrl: 'achilles_cover.jpg',
  title: 'Achilles Come Down',
  artist: 'Gang of Youths',
  fetchedLines: [
    { time_ms: 0, text: "Achilles, it's not much but there's proof" },
    { time_ms: 3000, text: "You crazy assed cosmonaut" },
    { time_ms: 6000, text: "Remember your virtue" },
    { time_ms: 9000, text: "Redemption lies plainly in truth" },
    { time_ms: 12000, text: "Just humour us" }
  ],
  selectedLineIndices: new Set([0, 1, 2, 3, 4])
};

const GENIUS_PRESET = {
  cardType: 'genius',
  bgColor: '#000000', // Iconic Black Footer from official Genius reference
  secondaryBgColor: '#121212',
  textColor: 'white',
  radius: 0,
  frameRatio: 'card_only',
  coverImgUrl: '/api/proxy-image?url=' + encodeURIComponent('https://upload.wikimedia.org/wikipedia/en/5/51/KendrickLamarGoodKidmMADCity.jpg'),
  title: 'Bitch, Don’t Kill My Vibe',
  artist: 'Kendrick Lamar',
  fetchedLines: [
    { time_ms: 0, text: "Fell on my face and awoke" },
    { time_ms: 2500, text: "with a scar, another" },
    { time_ms: 5000, text: "mistake livin' deep in my" },
    { time_ms: 7500, text: "heart" },
    { time_ms: 10000, text: "Wear it on top of my sleeve" },
    { time_ms: 12500, text: "in a flick, I can admit that it" },
    { time_ms: 15000, text: "did look like yours" }
  ],
  selectedLineIndices: new Set([0, 1, 2, 3])
};

const APPLE_MUSIC_PRESET = {
  cardType: 'apple_music',
  bgColor: 'rgba(255, 255, 255, 0.18)',
  secondaryBgColor: '#0b0b10',
  textColor: 'white',
  radius: 22,
  frameRatio: '9:16',
  backdropStyle: 'blurred_cover',
  blur: 40,
  coverImgUrl: '/api/proxy-image?url=' + encodeURIComponent('https://upload.wikimedia.org/wikipedia/en/5/51/KendrickLamarGoodKidmMADCity.jpg'),
  title: 'Bitch, Don’t Kill My Vibe',
  artist: 'Kendrick Lamar',
  fetchedLines: [
    { time_ms: 0, text: "Fell on my face and awoke" },
    { time_ms: 2500, text: "with a scar, another" },
    { time_ms: 5000, text: "mistake livin' deep in my heart" },
    { time_ms: 7500, text: "Wear it on top of my sleeve" },
    { time_ms: 10000, text: "in a flick, I can admit that it" },
    { time_ms: 12500, text: "did look like yours" }
  ],
  selectedLineIndices: new Set([0, 1, 2])
};

const spotifyCardState = {
  cardType: 'spotify',
  bgColor: '#4884ab',
  secondaryBgColor: '#437795',
  textColor: 'white',
  coverImgUrl: '/api/proxy-image?url=' + encodeURIComponent('https://upload.wikimedia.org/wikipedia/en/5/51/KendrickLamarGoodKidmMADCity.jpg'),
  loadedImg: null,
  blur: 12,
  opacity: 1.0,
  radius: 28,
  fontSize: 23,
  cardWidth: 380,
  enableBackdrop: true,
  backdropStyle: 'card_tint',
  frameRatio: '9:16',
  title: 'Bitch, Don’t Kill My Vibe',
  artist: 'Kendrick Lamar',
  fetchedLines: [
    { time_ms: 0, text: "Fell on my face and awoke" },
    { time_ms: 2500, text: "with a scar, another" },
    { time_ms: 5000, text: "mistake livin' deep in my" },
    { time_ms: 7500, text: "heart" },
    { time_ms: 10000, text: "Wear it on top of my sleeve" },
    { time_ms: 12500, text: "in a flick, I can admit that it" },
    { time_ms: 15000, text: "did look like yours" }
  ],
  selectedLineIndices: new Set([0, 1, 2, 3, 4, 5, 6])
};

function applyCardPreset(preset) {
  spotifyCardState.cardType = preset.cardType;
  spotifyCardState.bgColor = preset.bgColor;
  spotifyCardState.secondaryBgColor = preset.secondaryBgColor;
  spotifyCardState.textColor = preset.textColor;
  spotifyCardState.radius = typeof preset.radius === 'number' ? preset.radius : (preset.cardType === 'genius' ? 0 : 20);
  spotifyCardState.frameRatio = preset.frameRatio || '9:16';
  spotifyCardState.backdropStyle = preset.backdropStyle || (preset.cardType === 'apple_music' ? 'blurred_cover' : 'card_tint');
  spotifyCardState.blur = typeof preset.blur === 'number' ? preset.blur : 12;
  spotifyCardState.coverImgUrl = preset.coverImgUrl;
  spotifyCardState.title = preset.title;
  spotifyCardState.artist = preset.artist;
  spotifyCardState.fetchedLines = [...preset.fetchedLines];
  spotifyCardState.selectedLineIndices = new Set(preset.selectedLineIndices);

  if (songImageName) songImageName.textContent = preset.title;
  if (songImageAuthors) songImageAuthors.textContent = preset.artist;
  if (songImageCover) songImageCover.src = preset.coverImgUrl;
  if (spotifyCardCustomColor) spotifyCardCustomColor.value = preset.bgColor;
  if (spotifyCardSecondaryColor) spotifyCardSecondaryColor.value = preset.secondaryBgColor;
  if (spotifyCardSecondaryVal) spotifyCardSecondaryVal.textContent = preset.secondaryBgColor;
  if (spotifyCardRadiusSlider) spotifyCardRadiusSlider.value = spotifyCardState.radius;
  if (spotifyCardRadiusVal) spotifyCardRadiusVal.textContent = `${spotifyCardState.radius}px`;
  if (spotifyCardFrameRatio) spotifyCardFrameRatio.value = spotifyCardState.frameRatio;

  const cardStudioTitle = document.getElementById('card-studio-title-text');
  const cardStudioIcon = document.getElementById('card-studio-brand-icon');
  const cardStudioSubtitle = document.getElementById('card-studio-subtitle');

  if (preset.cardType === 'apple_music') {
    if (cardStudioTitle) cardStudioTitle.textContent = 'Apple Music Lyrics Card Studio';
    if (cardStudioSubtitle) cardStudioSubtitle.textContent = '1:1 Apple Music card with frosted glassmorphism, bold lyrics, rounded cover thumbnail, and 72px ultra-blurred backdrop.';
    if (cardStudioIcon) {
      cardStudioIcon.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#FA243C">
          <rect width="24" height="24" rx="5.5" fill="#FA243C"/>
          <path d="M15.7 6.2a.8.8 0 0 0-.9-.2l-5.6 1.4a.8.8 0 0 0-.6.8v6.9a2.4 2.4 0 0 0-1.6-.6 2.5 2.5 0 1 0 2.5 2.5V10.2l4.8-1.2v3.7a2.4 2.4 0 0 0-1.6-.6 2.5 2.5 0 1 0 2.5 2.5V7a.8.8 0 0 0-.1-.8z" fill="#FFFFFF"/>
        </svg>
      `;
    }
  } else if (preset.cardType === 'genius') {
    if (cardStudioTitle) cardStudioTitle.textContent = 'Genius Lyrics Card Studio';
    if (cardStudioSubtitle) cardStudioSubtitle.textContent = '1:1 Genius quote card with full cover artwork background, dark legibility shade, and signature yellow footer banner.';
    if (cardStudioIcon) {
      cardStudioIcon.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#FFFF64">
          <circle cx="12" cy="12" r="11" fill="#FFFF64"/>
          <text x="12" y="16.5" font-family="'Plus Jakarta Sans', sans-serif" font-weight="900" font-size="13" text-anchor="middle" fill="#000000">G</text>
        </svg>
      `;
    }
  } else if (preset.cardType === 'yt_music') {
    if (cardStudioTitle) cardStudioTitle.textContent = 'YouTube Music Lyrics Card Studio';
    if (cardStudioSubtitle) cardStudioSubtitle.textContent = 'Official YouTube Music layout with Plus Jakarta Sans bold typography, separator line, and play-icon logo.';
    if (cardStudioIcon) {
      cardStudioIcon.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#ff0000">
          <circle cx="12" cy="12" r="11" fill="#ff0000"/>
          <circle cx="12" cy="12" r="8.5" stroke="#ffffff" stroke-width="1.6" fill="none"/>
          <polygon points="10.5,8.5 15.5,12 10.5,15.5" fill="#ffffff"/>
        </svg>
      `;
    }
  } else {
    if (cardStudioTitle) cardStudioTitle.textContent = 'Spotify Lyrics Card Studio';
    if (cardStudioSubtitle) cardStudioSubtitle.textContent = 'Exact streaming layout with blurred cover, customizable tint, interactive lyrics, framing, and 4K high-DPI export.';
    if (cardStudioIcon) {
      cardStudioIcon.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#1ed760">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12C24 5.373 18.627 0 12 0zm5.502 17.308c-.217.355-.679.467-1.034.25-2.836-1.733-6.407-2.124-10.612-1.163-.404.093-.807-.162-.9-.567-.093-.404.163-.807.568-.9 4.606-1.052 8.562-.607 11.728 1.346.355.217.467.679.25 1.034zm1.47-3.268c-.273.444-.855.584-1.299.311-3.245-1.995-8.192-2.573-12.03-1.407-.497.151-1.026-.135-1.177-.633-.151-.498.136-1.026.634-1.177 4.385-1.332 9.839-.687 13.561 1.606.444.274.584.856.311 1.3zm.126-3.41c-3.89-2.31-10.309-2.523-14.032-1.392-.596.182-1.229-.161-1.411-.758-.181-.597.162-1.229.759-1.411 4.283-1.3 11.37-1.055 15.827 1.591.536.318.71 1.011.392 1.547-.318.536-1.01.71-1.546.392z"/>
        </svg>
      `;
    }
  }

  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => {
    spotifyCardState.loadedImg = img;
    updateSpotifyCardPreview();
  };
  img.src = preset.coverImgUrl;

  populateSpotifyCardLines(spotifyCardState.fetchedLines);
  renderCardLyricsFromSelection();
  updateSpotifyCardPreview();
}

function hexToRgba(hex, alpha) {
  let c = hex.replace('#', '');
  if (c.length === 3) c = c.split('').map(x => x + x).join('');
  const num = parseInt(c, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function contrastingTextColor(hexColor) {
  let hex = hexColor.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(x => x + x).join('');
  const r = parseInt(hex.substring(0, 2), 16) || 0;
  const g = parseInt(hex.substring(2, 4), 16) || 0;
  const b = parseInt(hex.substring(4, 6), 16) || 0;
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 140 ? '#000000' : '#ffffff';
}

function isLightColor(hexColor) {
  let hex = hexColor.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(x => x + x).join('');
  const r = parseInt(hex.substring(0, 2), 16) || 0;
  const g = parseInt(hex.substring(2, 4), 16) || 0;
  const b = parseInt(hex.substring(4, 6), 16) || 0;
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 140;
}

/**
 * Derives a harmonized secondary background color for the canvas backdrop
 * @param {string} hexColor
 * @returns {string}
 */
function deriveSecondaryColor(hexColor) {
  let hex = hexColor.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(x => x + x).join('');
  const num = parseInt(hex, 16) || 0;
  let r = (num >> 16) & 255;
  let g = (num >> 8) & 255;
  let b = num & 255;
  // Harmonious deep tone for outer canvas
  r = Math.max(0, Math.min(255, Math.round(r * 0.86)));
  g = Math.max(0, Math.min(255, Math.round(g * 0.86)));
  b = Math.max(0, Math.min(255, Math.round(b * 0.86)));
  const toHex = v => v.toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Converts RGB (0-255) to HSL (h: 0-360, s: 0-1, l: 0-1)
 */
function rgbToHsl(r, g, b) {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return { h: Math.round(h * 360), s, l };
}

/**
 * Converts RGB numbers to #RRGGBB hex string
 */
function rgbToHex(r, g, b) {
  const h = c => Math.min(255, Math.max(0, Math.round(c))).toString(16).padStart(2, '0');
  return `#${h(r)}${h(g)}${h(b)}`;
}

/**
 * Step 1: Pixel Quantization (Median Cut Color Clustering)
 * Groups thousands of downscaled pixels into 8-16 dominant color clusters.
 */
function medianCutQuantize(pixels, maxClusters = 16) {
  if (!pixels || pixels.length === 0) return [];

  // A box represents a cluster of pixels in 3D RGB space
  class ColorBox {
    constructor(pixelList) {
      this.pixels = pixelList;
      this.calculateBounds();
    }

    calculateBounds() {
      let rMin = 255, rMax = 0, gMin = 255, gMax = 0, bMin = 255, bMax = 0;
      for (let i = 0; i < this.pixels.length; i++) {
        const p = this.pixels[i];
        if (p.r < rMin) rMin = p.r;
        if (p.r > rMax) rMax = p.r;
        if (p.g < gMin) gMin = p.g;
        if (p.g > gMax) gMax = p.g;
        if (p.b < bMin) bMin = p.b;
        if (p.b > bMax) bMax = p.b;
      }
      this.rRange = rMax - rMin;
      this.gRange = gMax - gMin;
      this.bRange = bMax - bMin;
      this.volume = (this.rRange + 1) * (this.gRange + 1) * (this.bRange + 1);
    }

    getWidestChannel() {
      if (this.rRange >= this.gRange && this.rRange >= this.bRange) return 'r';
      if (this.gRange >= this.rRange && this.gRange >= this.bRange) return 'g';
      return 'b';
    }

    split() {
      if (this.pixels.length <= 1) return [this];
      const channel = this.getWidestChannel();
      this.pixels.sort((a, b) => a[channel] - b[channel]);
      const median = Math.floor(this.pixels.length / 2);
      return [
        new ColorBox(this.pixels.slice(0, median)),
        new ColorBox(this.pixels.slice(median))
      ];
    }

    getAverage() {
      let totalR = 0, totalG = 0, totalB = 0;
      const count = this.pixels.length;
      for (let i = 0; i < count; i++) {
        totalR += this.pixels[i].r;
        totalG += this.pixels[i].g;
        totalB += this.pixels[i].b;
      }
      const r = Math.round(totalR / count);
      const g = Math.round(totalG / count);
      const b = Math.round(totalB / count);
      const hsl = rgbToHsl(r, g, b);
      return {
        r, g, b,
        hex: rgbToHex(r, g, b),
        h: hsl.h,
        s: hsl.s,
        l: hsl.l,
        population: count
      };
    }
  }

  let boxes = [new ColorBox(pixels)];
  while (boxes.length < maxClusters) {
    // Sort boxes by pixel count * volume to split the largest heterogeneous box
    boxes.sort((a, b) => (b.pixels.length * b.volume) - (a.pixels.length * a.volume));
    const toSplit = boxes.shift();
    if (!toSplit || toSplit.pixels.length <= 1) {
      if (toSplit) boxes.push(toSplit);
      break;
    }
    const [b1, b2] = toSplit.split();
    boxes.push(b1);
    if (b2) boxes.push(b2);
  }

  return boxes.map(b => b.getAverage());
}

/**
 * Step 2: HSL Filtering & Target Swatches Extraction
 * Sorts clusters into Vibrant, Light Vibrant, Dark Vibrant, Muted, Light Muted, Dark Muted.
 * Selects Primary (Dominant Card) and Secondary (Canvas Background) colors.
 *
 * @param {HTMLImageElement|HTMLCanvasElement} img
 * @returns {{ primary: string, secondary: string, swatches: Object }|null}
 */
function extractPalette(img) {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return null;

    // Downscale to 64x64 to lower overhead & remove minor noise
    const size = 64;
    canvas.width = size;
    canvas.height = size;
    ctx.drawImage(img, 0, 0, size, size);

    const imageData = ctx.getImageData(0, 0, size, size);
    const data = imageData.data;
    const pixels = [];

    // Filter pure white (l > 0.95), pure black (l < 0.05), transparent pixels
    for (let i = 0; i < data.length; i += 4) {
      const a = data[i + 3];
      if (a < 128) continue;
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];

      const { s, l } = rgbToHsl(r, g, b);
      if (l < 0.04 || l > 0.96) continue;

      pixels.push({ r, g, b });
    }

    if (pixels.length === 0) return null;

    // Step 1: Pixel Quantization into clusters
    const clusters = medianCutQuantize(pixels, 16);
    if (clusters.length === 0) return null;

    const maxPop = Math.max(...clusters.map(c => c.population));

    // Target profiles matching Spotify / Android Material Palette
    const TARGET_PROFILES = {
      vibrant: {
        minS: 0.35, targetS: 1.0, maxS: 1.0,
        minL: 0.30, targetL: 0.50, maxL: 0.70
      },
      lightVibrant: {
        minS: 0.35, targetS: 1.0, maxS: 1.0,
        minL: 0.55, targetL: 0.74, maxL: 1.00
      },
      darkVibrant: {
        minS: 0.35, targetS: 1.0, maxS: 1.0,
        minL: 0.05, targetL: 0.26, maxL: 0.45
      },
      muted: {
        minS: 0.00, targetS: 0.30, maxS: 0.40,
        minL: 0.30, targetL: 0.50, maxL: 0.70
      },
      lightMuted: {
        minS: 0.00, targetS: 0.30, maxS: 0.40,
        minL: 0.55, targetL: 0.74, maxL: 1.00
      },
      darkMuted: {
        minS: 0.00, targetS: 0.30, maxS: 0.40,
        minL: 0.05, targetL: 0.26, maxL: 0.45
      }
    };

    // Score swatches for each target profile
    function findBestSwatchForTarget(target) {
      let bestSwatch = null;
      let highestScore = -Infinity;

      for (const swatch of clusters) {
        if (swatch.s >= target.minS && swatch.s <= target.maxS &&
            swatch.l >= target.minL && swatch.l <= target.maxL) {
          const satDiff = Math.abs(swatch.s - target.targetS);
          const lightDiff = Math.abs(swatch.l - target.targetL);
          const popRatio = swatch.population / maxPop;

          // Weightings: 35% Saturation, 50% Lightness, 15% Population
          const score = (1 - satDiff) * 3.5 + (1 - lightDiff) * 5.0 + popRatio * 1.5;

          if (score > highestScore) {
            highestScore = score;
            bestSwatch = swatch;
          }
        }
      }
      return bestSwatch;
    }

    const swatches = {
      vibrant: findBestSwatchForTarget(TARGET_PROFILES.vibrant),
      lightVibrant: findBestSwatchForTarget(TARGET_PROFILES.lightVibrant),
      darkVibrant: findBestSwatchForTarget(TARGET_PROFILES.darkVibrant),
      muted: findBestSwatchForTarget(TARGET_PROFILES.muted),
      lightMuted: findBestSwatchForTarget(TARGET_PROFILES.lightMuted),
      darkMuted: findBestSwatchForTarget(TARGET_PROFILES.darkMuted)
    };

    // Calculate Euclidean color distance between swatches
    const colorDist = (s1, s2) => {
      if (!s1 || !s2) return 0;
      return Math.hypot(s1.r - s2.r, s1.g - s2.g, s1.b - s2.b);
    };

    // Select PRIMARY color for the card (prioritizing Vibrant -> Light Vibrant -> Dark Vibrant -> Muted -> Max Pop)
    let primarySwatch = swatches.vibrant ||
                        swatches.lightVibrant ||
                        swatches.darkVibrant ||
                        swatches.muted ||
                        swatches.darkMuted ||
                        clusters.sort((a, b) => b.population - a.population)[0];

    // Select SECONDARY color for the canvas backdrop (prioritizing harmonized contrast)
    let secondarySwatch = null;
    const secondaryCandidates = [
      swatches.darkVibrant,
      swatches.darkMuted,
      swatches.vibrant,
      swatches.lightVibrant,
      swatches.muted,
      swatches.lightMuted,
      ...clusters.filter(c => colorDist(c, primarySwatch) >= 30)
    ].filter(Boolean);

    for (const candidate of secondaryCandidates) {
      if (candidate.hex !== primarySwatch.hex && colorDist(candidate, primarySwatch) >= 28) {
        secondarySwatch = candidate;
        break;
      }
    }

    const primary = primarySwatch.hex;
    const secondary = secondarySwatch ? secondarySwatch.hex : deriveSecondaryColor(primary);

    return { primary, secondary, swatches };
  } catch (err) {
    console.warn('Spotify Palette extraction fallback:', err);
    return null;
  }
}



/**
 * Recolors Logo image based on streaming template and luminance
 */
function updateSpotifyLogo(isLight) {
  const tagImg = document.getElementById('song-image-tag');
  if (!tagImg) return;
  const isYt = state.template === 'yt_music_card' || spotifyCardState.cardType === 'yt_music';
  if (isYt) {
    tagImg.src = isLight ? 'yt_music_logo_white.png' : 'yt_music_logo_black.png';
    tagImg.alt = 'YouTube Music';
  } else {
    tagImg.src = isLight ? 'spotify_logo_white.svg' : 'spotify_logo_black.svg';
    tagImg.alt = 'Spotify';
  }
}

/**
 * Exact LyricPost canvas blurred cover with edge-clamping padding to eliminate border fade
 */
function renderBlurredCover(coverImg, blurPx, width, height) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  if (blurPx <= 0) {
    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(coverImg, 0, 0, width, height);
    return canvas;
  }

  const pad = Math.ceil(blurPx * 3);
  canvas.width = width + pad * 2;
  canvas.height = height + pad * 2;

  // Center
  ctx.drawImage(coverImg, pad, pad, width, height);

  // Clamped 1px edges to prevent transparent edge bleed
  const nw = coverImg.naturalWidth || width;
  const nh = coverImg.naturalHeight || height;

  // Top
  ctx.drawImage(coverImg, 0, 0, nw, 1, pad, 0, width, pad);
  // Bottom
  ctx.drawImage(coverImg, 0, nh - 1, nw, 1, pad, height + pad, width, pad);
  // Left
  ctx.drawImage(coverImg, 0, 0, 1, nh, 0, pad, pad, height);
  // Right
  ctx.drawImage(coverImg, nw - 1, 0, 1, nh, width + pad, pad, pad, height);

  // Corners
  ctx.drawImage(coverImg, 0, 0, 1, 1, 0, 0, pad, pad);
  ctx.drawImage(coverImg, nw - 1, 0, 1, 1, width + pad, 0, pad, pad);
  ctx.drawImage(coverImg, 0, nh - 1, 1, 1, 0, height + pad, pad, pad);
  ctx.drawImage(coverImg, nw - 1, nh - 1, 1, 1, width + pad, height + pad, pad, pad);

  // Filtered canvas
  const blurCanvas = document.createElement('canvas');
  blurCanvas.width = width;
  blurCanvas.height = height;
  const blurCtx = blurCanvas.getContext('2d');
  blurCtx.filter = `blur(${blurPx}px)`;
  blurCtx.drawImage(canvas, -pad, -pad);

  return blurCanvas;
}

/**
 * Renders composite blurred cover + color overlay data URL
 */
function renderImageBackground(coverImg, bgColor, opacity, blurPx, width, height) {
  const finalCanvas = document.createElement('canvas');
  finalCanvas.width = width;
  finalCanvas.height = height;
  const ctx = finalCanvas.getContext('2d');

  if (coverImg && coverImg.complete && coverImg.naturalWidth > 0) {
    try {
      const blurred = renderBlurredCover(coverImg, blurPx, width, height);
      ctx.drawImage(blurred, 0, 0);
    } catch (e) {
      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, width, height);
    }
  } else {
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, width, height);
  }

  // Tint overlay
  ctx.fillStyle = hexToRgba(bgColor, opacity);
  ctx.fillRect(0, 0, width, height);

  return finalCanvas.toDataURL('image/png');
}

/**
 * Updates the card and outer template backdrop in real time (1:1 with LyricPost / Genius / Apple Music)
 */
function updateSpotifyCardPreview() {
  if (!songImage) return;

  const isGenius = state.template === 'genius_card' || spotifyCardState.cardType === 'genius';
  const isAppleMusic = state.template === 'apple_music_card' || spotifyCardState.cardType === 'apple_music';

  // Apply chosen text color theme (white or black)
  const isWhite = spotifyCardState.textColor === 'white';
  const textColor = isWhite ? '#ffffff' : '#000000';
  const authorColor = isWhite ? 'rgba(255, 255, 255, 0.78)' : 'rgba(0, 0, 0, 0.65)';
  const separatorColor = isWhite ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.10)';

  // 1:1 CSS variables
  songImage.style.setProperty('--song-bg-color', spotifyCardState.bgColor);
  songImage.style.setProperty('--song-text-color', textColor);
  songImage.style.setProperty('--song-author-color', authorColor);
  songImage.style.setProperty('--song-separator-color', separatorColor);
  songImage.style.setProperty('--song-font-family', "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif");
  songImage.style.setProperty('--song-border-radius', `${spotifyCardState.radius}px`);
  songImage.style.setProperty('--song-image-width', `${spotifyCardState.cardWidth}px`);
  songImage.style.setProperty('--song-lyrics-font-size', `${spotifyCardState.fontSize}px`);
  songImage.style.setProperty('--song-line-height', '1.38');
  songImage.style.setProperty('--song-tag-height', '1.85rem');
  songImage.style.color = textColor;

  // Toggle active styling on buttons
  if (spotifyCardTextWhiteBtn) spotifyCardTextWhiteBtn.classList.toggle('active', isWhite);
  if (spotifyCardTextBlackBtn) spotifyCardTextBlackBtn.classList.toggle('active', !isWhite);

  const geniusInner = document.getElementById('genius-inner');
  const appleMusicInner = document.getElementById('apple-music-inner');
  const appleMusicCover = document.getElementById('apple-music-cover');
  const appleMusicName = document.getElementById('apple-music-name');
  const appleMusicAuthors = document.getElementById('apple-music-authors');
  const songHeader = document.getElementById('song-image-header');
  const songLyrics = document.getElementById('song-image-lyrics');
  const songSpotifyFooter = document.getElementById('song-image-spotify-footer');
  const geniusFooter = document.getElementById('genius-footer');
  const geniusFooterMeta = document.getElementById('genius-footer-meta');
  const geniusFooterLogo = document.getElementById('genius-footer-logo');

  if (isAppleMusic) {
    songImage.classList.add('layout-apple-music');
    songImage.classList.remove('layout-genius', 'layout-spotify', 'spotify-tag');
    if (appleMusicInner) appleMusicInner.style.display = 'flex';
    if (geniusInner) geniusInner.style.display = 'none';
    if (songHeader) songHeader.style.display = 'none';
    if (songLyrics) songLyrics.style.display = 'none';
    if (songSpotifyFooter) songSpotifyFooter.style.display = 'none';
    if (geniusFooter) geniusFooter.style.display = 'none';

    if (appleMusicName) appleMusicName.textContent = spotifyCardState.title || 'Song Title';
    if (appleMusicAuthors) appleMusicAuthors.textContent = spotifyCardState.artist || 'Artist';
    if (appleMusicCover && spotifyCardState.coverImgUrl) {
      appleMusicCover.src = spotifyCardState.coverImgUrl;
    }

    songImage.style.backgroundImage = 'none';
    songImage.style.backgroundColor = 'transparent';
  } else if (isGenius) {
    songImage.classList.add('layout-genius');
    songImage.classList.remove('layout-apple-music', 'layout-spotify', 'spotify-tag');
    if (appleMusicInner) appleMusicInner.style.display = 'none';
    if (geniusInner) geniusInner.style.display = 'flex';
    if (songHeader) songHeader.style.display = 'none';
    if (songLyrics) songLyrics.style.display = 'none';
    if (songSpotifyFooter) songSpotifyFooter.style.display = 'none';
    if (geniusFooter) geniusFooter.style.display = 'flex';

    if (geniusFooterMeta) {
      const art = (spotifyCardState.artist || 'Artist').toUpperCase();
      const tit = (spotifyCardState.title || 'Song Title').toUpperCase();
      geniusFooterMeta.textContent = `${art}, "${tit}"`;
    }

    const bannerBg = spotifyCardState.bgColor || '#000000';
    const isBannerLight = isLightColor(bannerBg);
    const bannerFg = isBannerLight ? '#000000' : '#ffffff';

    songImage.style.setProperty('--genius-banner-bg', bannerBg);
    songImage.style.setProperty('--genius-banner-fg', bannerFg);
    songImage.style.setProperty('--genius-highlight-bg', '#ffffff');
    songImage.style.setProperty('--genius-highlight-fg', '#000000');

    if (geniusFooterLogo) {
      geniusFooterLogo.src = isBannerLight ? 'genius_logo.svg' : 'genius_logo_white.svg';
    }

    // Cover image is the main background image
    if (spotifyCardState.coverImgUrl) {
      songImage.style.backgroundImage = `url("${spotifyCardState.coverImgUrl}")`;
      songImage.style.backgroundColor = '#121212';
      songImage.style.backgroundSize = 'cover';
      songImage.style.backgroundPosition = 'center center';
    }
  } else {
    songImage.classList.remove('layout-genius', 'layout-apple-music');
    songImage.classList.add('layout-spotify', 'spotify-tag');
    if (appleMusicInner) appleMusicInner.style.display = 'none';
    if (geniusInner) geniusInner.style.display = 'none';
    if (songHeader) songHeader.style.display = 'flex';
    if (songLyrics) songLyrics.style.display = 'flex';
    if (songSpotifyFooter) songSpotifyFooter.style.display = 'flex';
    if (geniusFooter) geniusFooter.style.display = 'none';

    // Modern official Spotify / YouTube Music logo (white or black)
    updateSpotifyLogo(isWhite);

    // Card background
    if (spotifyCardState.backdropStyle === 'blurred_cover' && spotifyCardState.loadedImg) {
      try {
        const bgData = renderImageBackground(
          spotifyCardState.loadedImg,
          spotifyCardState.bgColor,
          spotifyCardState.opacity,
          spotifyCardState.blur,
          Math.max(songImage.offsetWidth || 320, 320),
          Math.max(songImage.offsetHeight || 360, 360)
        );
        songImage.style.backgroundImage = `url("${bgData}")`;
      } catch (err) {
        songImage.style.backgroundImage = 'none';
        songImage.style.backgroundColor = spotifyCardState.bgColor;
      }
    } else {
      // 1:1 LyricPost native style: background color
      songImage.style.backgroundImage = 'none';
      songImage.style.backgroundColor = spotifyCardState.bgColor;
    }
  }

  // Update outer template canvas
  updateBackdropPreview();
}

/**
 * Updates the outer 9:16 / 1:1 template canvas framing
 */
function updateBackdropPreview() {
  if (!additionalBgPreview) return;

  const isGenius = state.template === 'genius_card' || spotifyCardState.cardType === 'genius';
  additionalBgPreview.style.borderRadius = isGenius ? '0px' : '28px';

  if (spotifyCardState.frameRatio === 'card_only') {
    additionalBgPreview.setAttribute('data-ratio', 'card_only');
    additionalBgPreview.style.background = 'transparent';
    additionalBgPreview.style.boxShadow = 'none';
    if (songImageWrap) songImageWrap.style.boxShadow = 'none';
    return;
  }

  additionalBgPreview.setAttribute('data-ratio', spotifyCardState.frameRatio);
  additionalBgPreview.style.boxShadow = '0 24px 60px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.1)';

  if (songImageWrap) {
    songImageWrap.style.boxShadow = 'none';
  }

  if (spotifyCardState.backdropStyle === 'blurred_cover' && spotifyCardState.loadedImg) {
    try {
      const w = additionalBgPreview.offsetWidth || 375;
      const h = additionalBgPreview.offsetHeight || 667;
      const bgCanvas = renderBlurredCover(spotifyCardState.loadedImg, spotifyCardState.blur || 35, Math.min(w, 800), Math.min(h, 900));
      additionalBgPreview.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("${bgCanvas.toDataURL('image/jpeg', 0.85)}")`;
      additionalBgPreview.style.backgroundColor = '#121212';
    } catch (e) {
      additionalBgPreview.style.backgroundImage = 'none';
      additionalBgPreview.style.backgroundColor = spotifyCardState.bgColor;
    }
  } else if (spotifyCardState.backdropStyle === 'card_tint') {
    // Spotify share card: canvas uses the secondary color from the album art
    additionalBgPreview.style.backgroundImage = 'none';
    additionalBgPreview.style.backgroundColor = spotifyCardState.secondaryBgColor || spotifyCardState.bgColor;
  } else {
    // dark OLED
    additionalBgPreview.style.backgroundImage = 'none';
    additionalBgPreview.style.backgroundColor = '#121212';
  }
}

/**
 * Rebuilds card lyric lines from selectedLineIndices (in Spotify, YouTube Music, Genius, and Apple Music layouts)
 */
function renderCardLyricsFromSelection() {
  const containers = [
    document.getElementById('song-image-lyrics'),
    document.getElementById('genius-lyrics'),
    document.getElementById('apple-music-lyrics')
  ].filter(Boolean);

  containers.forEach(container => {
    container.innerHTML = '';
    const indices = Array.from(spotifyCardState.selectedLineIndices).sort((a, b) => a - b);
    if (indices.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'lyric-line';
      empty.textContent = 'Click lines on the right to add them...';
      empty.style.opacity = '0.5';
      container.appendChild(empty);
      return;
    }

    indices.forEach(idx => {
      const line = spotifyCardState.fetchedLines[idx];
      if (line && line.text) {
        const lineDiv = document.createElement('div');
        lineDiv.className = 'lyric-line';
        lineDiv.style.textAlign = 'left';

        const highlightSpan = document.createElement('span');
        highlightSpan.className = 'lyric-highlight';
        highlightSpan.textContent = line.text;
        lineDiv.appendChild(highlightSpan);

        container.appendChild(lineDiv);
      }
    });

    container.style.textAlign = 'left';
    container.style.alignItems = 'flex-start';
  });

  // Re-render background to fit updated content height
  setTimeout(updateSpotifyCardPreview, 50);
}

/**
 * Populates interactive lyrics picker list
 */
function populateSpotifyCardLines(lines) {
  if (!spotifyCardLinesList) return;
  spotifyCardLinesList.innerHTML = '';

  if (!lines || lines.length === 0) {
    spotifyCardLinesList.innerHTML = '<div style="font-size: 12px; color: var(--text-muted); padding: 8px; text-align: center;">No synced lines found for this song.</div>';
    return;
  }

  lines.forEach((line, idx) => {
    const item = document.createElement('div');
    item.className = 'spotify-line-item';
    if (spotifyCardState.selectedLineIndices.has(idx)) {
      item.classList.add('selected');
    }

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'spotify-line-checkbox';
    checkbox.checked = spotifyCardState.selectedLineIndices.has(idx);

    const time = document.createElement('span');
    time.className = 'spotify-line-time';
    const totalSec = Math.floor((line.time_ms || 0) / 1000);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    time.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;

    const text = document.createElement('span');
    text.style.flex = '1';
    text.textContent = line.text;

    item.appendChild(checkbox);
    item.appendChild(time);
    item.appendChild(text);

    item.addEventListener('click', (e) => {
      if (e.target !== checkbox) checkbox.checked = !checkbox.checked;
      if (checkbox.checked) {
        spotifyCardState.selectedLineIndices.add(idx);
        item.classList.add('selected');
      } else {
        spotifyCardState.selectedLineIndices.delete(idx);
        item.classList.remove('selected');
      }
      renderCardLyricsFromSelection();
    });

    spotifyCardLinesList.appendChild(item);
  });
}

/**
 * Fetches track metadata and synced lyrics from /api/carousel-lyrics
 */
async function fetchSpotifyCardLyrics(query) {
  const q = String(query || songQueryInput.value || '').trim();
  if (!q) {
    showToast('Please enter a Spotify link or song query');
    return;
  }

  if (spotifyCardStatus) {
    spotifyCardStatus.textContent = `🔍 Fetching track info and synced lyrics for "${q}"...`;
    spotifyCardStatus.style.color = '#38bdf8';
  }
  if (spotifyCardFetchBtn) {
    spotifyCardFetchBtn.disabled = true;
    spotifyCardFetchBtn.innerHTML = '<span>⏳ Fetching...</span>';
  }

  try {
    const res = await fetch(`/api/carousel-lyrics?q=${encodeURIComponent(q)}`);
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || 'Failed to fetch lyrics');
    }

    spotifyCardState.title = data.title || q;
    spotifyCardState.artist = data.artist || '';
    if (songImageName) songImageName.textContent = spotifyCardState.title;
    if (songImageAuthors) songImageAuthors.textContent = spotifyCardState.artist || 'Unknown Artist';

    // Lines
    spotifyCardState.fetchedLines = data.lines || [];
    // Select first 4 lines by default
    spotifyCardState.selectedLineIndices = new Set(
      spotifyCardState.fetchedLines.slice(0, 4).map((_, i) => i)
    );
    populateSpotifyCardLines(spotifyCardState.fetchedLines);
    renderCardLyricsFromSelection();

    // Cover art (proxied via /api/proxy-image to avoid CORS tainted canvas)
    if (data.cover_url) {
      spotifyCardState.coverImgUrl = `/api/proxy-image?url=${encodeURIComponent(data.cover_url)}`;
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        spotifyCardState.loadedImg = img;
        if (songImageCover) songImageCover.src = spotifyCardState.coverImgUrl;

        // Automatically pick primary color for card and secondary color for background
        const isGenius = state.template === 'genius_card' || spotifyCardState.cardType === 'genius';
        const palette = extractPalette(img);
        if (palette) {
          spotifyCardState.bgColor = isGenius ? '#FFFF64' : palette.primary;
          spotifyCardState.secondaryBgColor = isGenius ? '#121212' : palette.secondary;
          spotifyCardState.textColor = isGenius ? 'white' : (isLightColor(palette.primary) ? 'black' : 'white');
          if (spotifyCardCustomColor) spotifyCardCustomColor.value = spotifyCardState.bgColor;
          if (spotifyCardSecondaryColor) spotifyCardSecondaryColor.value = spotifyCardState.secondaryBgColor;
          if (spotifyCardSecondaryVal) spotifyCardSecondaryVal.textContent = spotifyCardState.secondaryBgColor;
        }

        updateSpotifyCardPreview();
      };
      img.onerror = () => {
        console.warn('Failed to load proxied cover art; using fallback');
        updateSpotifyCardPreview();
      };
      img.src = spotifyCardState.coverImgUrl;
    } else {
      updateSpotifyCardPreview();
    }

    if (spotifyCardStatus) {
      spotifyCardStatus.textContent = `✨ Loaded "${spotifyCardState.title}" by ${spotifyCardState.artist} (${spotifyCardState.fetchedLines.length} synced lines).`;
      spotifyCardStatus.style.color = '#4ade80';
    }
    showToast(`Loaded ${spotifyCardState.fetchedLines.length} lyric lines`);
  } catch (err) {
    console.error('Error in fetchSpotifyCardLyrics:', err);
    if (spotifyCardStatus) {
      spotifyCardStatus.textContent = `⚠️ ${err.message}`;
      spotifyCardStatus.style.color = '#f87171';
    }
    showToast(`Error: ${err.message}`);
  } finally {
    if (spotifyCardFetchBtn) {
      spotifyCardFetchBtn.disabled = false;
      spotifyCardFetchBtn.innerHTML = '<span>Fetch Track Lyrics</span>';
    }
  }
}

/**
 * Template canvas composite for high-DPI export matching reference photos
 */
function addBgToDownloadCanvas(cardCanvas, options = {}) {
  const ratio = options.frameRatio || '9:16';
  if (ratio === 'card_only') return cardCanvas;

  let outWidth = 1080;
  let outHeight = 1920; // 9:16 Story default

  if (ratio === '1:1') {
    outWidth = 1080;
    outHeight = 1080;
  } else if (ratio === '4:5') {
    outWidth = 1080;
    outHeight = 1350;
  }

  // Scale up for crystal clear 2K/4K export
  const canvas = document.createElement('canvas');
  canvas.width = outWidth;
  canvas.height = outHeight;
  const ctx = canvas.getContext('2d');

  // Fill canvas background
  if (options.backdropStyle === 'blurred_cover' && options.bgCoverImg) {
    try {
      const bgBlurred = renderBlurredCover(options.bgCoverImg, 60, outWidth, outHeight);
      ctx.drawImage(bgBlurred, 0, 0);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
      ctx.fillRect(0, 0, outWidth, outHeight);
    } catch (e) {
      ctx.fillStyle = options.bgColor || '#c1687c';
      ctx.fillRect(0, 0, outWidth, outHeight);
    }
  } else if (options.backdropStyle === 'card_tint') {
    // Spotify Native style: canvas uses the secondary background color
    ctx.fillStyle = options.secondaryBgColor || options.bgColor || '#437795';
    ctx.fillRect(0, 0, outWidth, outHeight);
  } else {
    // OLED Dark
    ctx.fillStyle = '#121212';
    ctx.fillRect(0, 0, outWidth, outHeight);
  }

  // Scale and center the card within the template canvas (occupying ~90% width)
  const targetCardWidth = Math.round(outWidth * 0.90);
  const scale = targetCardWidth / cardCanvas.width;
  const drawW = targetCardWidth;
  const drawH = Math.round(cardCanvas.height * scale);

  const drawX = Math.round((outWidth - drawW) / 2);
  const drawY = Math.round((outHeight - drawH) / 2);

  // Soft, rich drop shadow (matching reference images)
  ctx.save();
  ctx.shadowColor = 'rgba(0, 0, 0, 0.30)';
  ctx.shadowBlur = 54;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 24;

  ctx.drawImage(cardCanvas, drawX, drawY, drawW, drawH);
  ctx.restore();

  return canvas;
}

/**
 * Downloads pristine High-DPI 4K card PNG using html2canvas
 */
async function downloadSpotifyCard() {
  if (!songImage) return;

  if (typeof html2canvas === 'undefined') {
    showToast('html2canvas library is still loading. Please try again in a moment.');
    return;
  }

  if (spotifyCardDownloadBtn) {
    spotifyCardDownloadBtn.disabled = true;
    spotifyCardDownloadBtn.innerHTML = '<span>⏳ Exporting 4K PNG...</span>';
  }

  try {
    // 3x scale for pristine ultra-high DPI output
    const scale = 3;
    const cardCanvas = await html2canvas(songImage, {
      scale: scale,
      useCORS: true,
      allowTaint: true,
      backgroundColor: null,
      logging: false
    });

    let exportCanvas = cardCanvas;

    if (spotifyCardState.frameRatio !== 'card_only') {
      exportCanvas = addBgToDownloadCanvas(cardCanvas, {
        frameRatio: spotifyCardState.frameRatio,
        bgColor: spotifyCardState.bgColor,
        secondaryBgColor: spotifyCardState.secondaryBgColor,
        backdropStyle: spotifyCardState.backdropStyle,
        bgCoverImg: spotifyCardState.loadedImg
      });
    }

    const isAppleMusic = state.template === 'apple_music_card' || spotifyCardState.cardType === 'apple_music';
    const isGenius = state.template === 'genius_card' || spotifyCardState.cardType === 'genius';
    const isYt = state.template === 'yt_music_card' || spotifyCardState.cardType === 'yt_music';
    const tagPrefix = isAppleMusic ? 'applemusic' : (isGenius ? 'genius' : (isYt ? 'ytmusic' : 'spotify'));
    const titleSlug = (spotifyCardState.title || `${tagPrefix}_lyrics`).toLowerCase().replace(/[^a-z0-9]+/g, '_').slice(0, 40);
    const filename = `${titleSlug}_${tagPrefix}_card.png`;

    exportCanvas.toBlob((blob) => {
      if (!blob) {
        showToast('Export failed to create image blob');
        return;
      }
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      showToast(`✅ Downloaded ${filename}`);
    }, 'image/png');
  } catch (err) {
    console.error('Error exporting Spotify card:', err);
    showToast(`Export error: ${err.message}`);
  } finally {
    if (spotifyCardDownloadBtn) {
      spotifyCardDownloadBtn.disabled = false;
      spotifyCardDownloadBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>Download Card (High-DPI PNG)</span>
      `;
    }
  }
}

/**
 * Initializes the Spotify Lyrics Card Studio
 */
function initSpotifyCard() {
  if (!spotifyCardStudio) return;

  // Text Color Buttons: White vs Black
  if (spotifyCardTextWhiteBtn) {
    spotifyCardTextWhiteBtn.addEventListener('click', () => {
      spotifyCardState.textColor = 'white';
      updateSpotifyCardPreview();
    });
  }

  if (spotifyCardTextBlackBtn) {
    spotifyCardTextBlackBtn.addEventListener('click', () => {
      spotifyCardState.textColor = 'black';
      updateSpotifyCardPreview();
    });
  }

  // Swatches
  spotifyCardSwatches.forEach(swatch => {
    swatch.addEventListener('click', () => {
      spotifyCardSwatches.forEach(s => s.classList.remove('active'));
      swatch.classList.add('active');
      spotifyCardState.bgColor = swatch.dataset.color;
      spotifyCardState.secondaryBgColor = deriveSecondaryColor(spotifyCardState.bgColor);
      if (spotifyCardCustomColor) spotifyCardCustomColor.value = spotifyCardState.bgColor;
      if (spotifyCardSecondaryColor) spotifyCardSecondaryColor.value = spotifyCardState.secondaryBgColor;
      if (spotifyCardSecondaryVal) spotifyCardSecondaryVal.textContent = spotifyCardState.secondaryBgColor;
      updateSpotifyCardPreview();
    });
  });

  if (spotifyCardCustomColor) {
    spotifyCardCustomColor.addEventListener('input', (e) => {
      spotifyCardSwatches.forEach(s => s.classList.remove('active'));
      spotifyCardState.bgColor = e.target.value;
      spotifyCardState.secondaryBgColor = deriveSecondaryColor(spotifyCardState.bgColor);
      if (spotifyCardSecondaryColor) spotifyCardSecondaryColor.value = spotifyCardState.secondaryBgColor;
      if (spotifyCardSecondaryVal) spotifyCardSecondaryVal.textContent = spotifyCardState.secondaryBgColor;
      updateSpotifyCardPreview();
    });
  }

  if (spotifyCardSecondaryColor) {
    spotifyCardSecondaryColor.addEventListener('input', (e) => {
      spotifyCardState.secondaryBgColor = e.target.value;
      if (spotifyCardSecondaryVal) spotifyCardSecondaryVal.textContent = spotifyCardState.secondaryBgColor;
      updateBackdropPreview();
    });
  }

  // Sliders
  if (spotifyCardBlurSlider) {
    spotifyCardBlurSlider.addEventListener('input', (e) => {
      spotifyCardState.blur = parseFloat(e.target.value);
      if (spotifyCardBlurVal) spotifyCardBlurVal.textContent = `${spotifyCardState.blur}px`;
      updateSpotifyCardPreview();
    });
  }

  if (spotifyCardRadiusSlider) {
    spotifyCardRadiusSlider.addEventListener('input', (e) => {
      spotifyCardState.radius = parseInt(e.target.value, 10);
      if (spotifyCardRadiusVal) spotifyCardRadiusVal.textContent = `${spotifyCardState.radius}px`;
      updateSpotifyCardPreview();
    });
  }

  if (spotifyCardFontsizeSlider) {
    spotifyCardFontsizeSlider.addEventListener('input', (e) => {
      spotifyCardState.fontSize = parseInt(e.target.value, 10);
      if (spotifyCardFontsizeVal) spotifyCardFontsizeVal.textContent = `${spotifyCardState.fontSize}px`;
      updateSpotifyCardPreview();
    });
  }

  if (spotifyCardWidthSlider) {
    spotifyCardWidthSlider.addEventListener('input', (e) => {
      spotifyCardState.cardWidth = parseInt(e.target.value, 10);
      if (spotifyCardWidthVal) spotifyCardWidthVal.textContent = `${spotifyCardState.cardWidth}%`;
      updateSpotifyCardPreview();
    });
  }

  // Template Canvas Ratio & Backdrop options
  if (spotifyCardBackdropStyle) {
    spotifyCardBackdropStyle.addEventListener('change', (e) => {
      spotifyCardState.backdropStyle = e.target.value;
      updateBackdropPreview();
    });
  }

  if (spotifyCardFrameRatio) {
    spotifyCardFrameRatio.addEventListener('change', (e) => {
      spotifyCardState.frameRatio = e.target.value;
      updateBackdropPreview();
    });
  }

  // Buttons
  if (spotifyCardFetchBtn) {
    spotifyCardFetchBtn.addEventListener('click', () => {
      fetchSpotifyCardLyrics(songQueryInput ? songQueryInput.value : '');
    });
  }

  if (spotifyCardDownloadBtn) {
    spotifyCardDownloadBtn.addEventListener('click', downloadSpotifyCard);
  }

  if (spotifyCardClearLyricsBtn) {
    spotifyCardClearLyricsBtn.addEventListener('click', () => {
      spotifyCardState.selectedLineIndices.clear();
      if (spotifyCardLinesList) {
        spotifyCardLinesList.querySelectorAll('.spotify-line-item').forEach(el => {
          el.classList.remove('selected');
          const cb = el.querySelector('input[type="checkbox"]');
          if (cb) cb.checked = false;
        });
      }
      renderCardLyricsFromSelection();
    });
  }

  if (spotifyCardSampleLyricsBtn) {
    spotifyCardSampleLyricsBtn.addEventListener('click', () => {
      spotifyCardState.selectedLineIndices = new Set([0, 1, 2, 3].filter(i => i < spotifyCardState.fetchedLines.length));
      if (spotifyCardLinesList) {
        spotifyCardLinesList.querySelectorAll('.spotify-line-item').forEach((el, idx) => {
          const isSelected = spotifyCardState.selectedLineIndices.has(idx);
          el.classList.toggle('selected', isSelected);
          const cb = el.querySelector('input[type="checkbox"]');
          if (cb) cb.checked = isSelected;
        });
      }
      renderCardLyricsFromSelection();
    });
  }

  // Initial load
  const initialImg = new Image();
  initialImg.crossOrigin = 'anonymous';
  initialImg.onload = () => {
    spotifyCardState.loadedImg = initialImg;

    // Pick primary color for card and secondary color for background
    const palette = extractPalette(initialImg);
    if (palette) {
      spotifyCardState.bgColor = palette.primary;
      spotifyCardState.secondaryBgColor = palette.secondary;
      spotifyCardState.textColor = isLightColor(palette.primary) ? 'black' : 'white';
      if (spotifyCardCustomColor) spotifyCardCustomColor.value = palette.primary;
      if (spotifyCardSecondaryColor) spotifyCardSecondaryColor.value = palette.secondary;
      if (spotifyCardSecondaryVal) spotifyCardSecondaryVal.textContent = palette.secondary;
    }

    updateSpotifyCardPreview();
  };
  initialImg.src = spotifyCardState.coverImgUrl;

  populateSpotifyCardLines(spotifyCardState.fetchedLines);
  renderCardLyricsFromSelection();
}

/* ==========================================================================
   Song Recognition Studio & Flag UI Elements
   ========================================================================== */
function initSongRecognitionStudio() {
  const tabDirectGenerator = document.getElementById('tab-direct-generator');
  const tabSongRecognition = document.getElementById('tab-song-recognition');
  const songRecognitionStudio = document.getElementById('song-recognition-studio');
  const recognitionCloseBtn = document.getElementById('recognition-close-btn');

  const flagPills = document.querySelectorAll('#recognition-flag-group .flag-pill');
  const recogInputShort = document.getElementById('recog-input-short');
  const recogInputChannel = document.getElementById('recog-input-channel');
  const recogInputLocal = document.getElementById('recog-input-local');

  const recogShortUrl = document.getElementById('recog-short-url');
  const recogRunShortBtn = document.getElementById('recog-run-short-btn');

  const recogChannelUrl = document.getElementById('recog-channel-url');
  const recogRunChannelBtn = document.getElementById('recog-run-channel-btn');
  const countPills = document.querySelectorAll('.recog-count-group .count-pill');

  const recogDropzone = document.getElementById('recog-dropzone');
  const recogFileInput = document.getElementById('recog-file-input');
  const recogFileLabel = document.getElementById('recog-file-label');
  const recogSavedVideoSelect = document.getElementById('recog-saved-video-select');
  const recogRunLocalBtn = document.getElementById('recog-run-local-btn');

  const recogProgressBox = document.getElementById('recog-progress-box');
  const recogProgressText = document.getElementById('recog-progress-text');
  const recogProgressPercent = document.getElementById('recog-progress-percent');
  const recogProgressFill = document.getElementById('recog-progress-fill');
  const recogResultsContainer = document.getElementById('recog-results-container');

  let recogState = {
    mode: 'short',
    topCount: 5,
    selectedFile: null,
    isProcessing: false,
    eventSource: null
  };

  // 1. Workflow mode tab switching
  if (tabSongRecognition) {
    tabSongRecognition.addEventListener('click', () => {
      if (tabDirectGenerator) tabDirectGenerator.classList.remove('active');
      tabSongRecognition.classList.add('active');
      if (songRecognitionStudio) {
        songRecognitionStudio.style.display = 'block';
        songRecognitionStudio.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  if (tabDirectGenerator) {
    tabDirectGenerator.addEventListener('click', () => {
      if (tabSongRecognition) tabSongRecognition.classList.remove('active');
      tabDirectGenerator.classList.add('active');
      if (songRecognitionStudio) {
        songRecognitionStudio.style.display = 'none';
      }
    });
  }

  if (recognitionCloseBtn) {
    recognitionCloseBtn.addEventListener('click', () => {
      if (tabDirectGenerator) tabDirectGenerator.click();
    });
  }

  // 2. Mode Flags switching (Buttons: -s, -c, -l)
  flagPills.forEach(pill => {
    pill.addEventListener('click', () => {
      flagPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const mode = pill.dataset.mode || 'short';
      recogState.mode = mode;

      if (recogInputShort) recogInputShort.style.display = mode === 'short' ? 'block' : 'none';
      if (recogInputChannel) recogInputChannel.style.display = mode === 'channel' ? 'block' : 'none';
      if (recogInputLocal) recogInputLocal.style.display = mode === 'local' ? 'block' : 'none';
    });
  });

  // 3. Count pills for channel mode (-n 3, 5, 10)
  countPills.forEach(pill => {
    pill.addEventListener('click', () => {
      countPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      recogState.topCount = parseInt(pill.dataset.count, 10) || 5;
    });
  });

  // 4. Dropzone & File selection
  if (recogDropzone && recogFileInput) {
    recogDropzone.addEventListener('click', () => recogFileInput.click());

    recogDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      recogDropzone.classList.add('dragover');
    });

    recogDropzone.addEventListener('dragleave', () => {
      recogDropzone.classList.remove('dragover');
    });

    recogDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      recogDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleLocalFileSelected(e.dataTransfer.files[0]);
      }
    });

    recogFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleLocalFileSelected(e.target.files[0]);
      }
    });
  }

  function handleLocalFileSelected(file) {
    recogState.selectedFile = file;
    if (recogFileLabel) {
      recogFileLabel.textContent = `Selected: ${file.name} (${(file.size / (1024 * 1024)).toFixed(1)} MB)`;
    }
  }

  // 5. Populate saved videos in videos/input
  async function loadSavedInputVideos() {
    if (!recogSavedVideoSelect) return;
    try {
      const res = await fetch('/api/background-videos');
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data.videos) && data.videos.length > 0) {
        recogSavedVideoSelect.innerHTML = '<option value="">-- Select from videos/input/ --</option>';
        data.videos.forEach(v => {
          const opt = document.createElement('option');
          opt.value = v.path;
          opt.textContent = `${v.folder !== 'root' ? v.folder + '/' : ''}${v.filename} (${v.sizeMb} MB)`;
          recogSavedVideoSelect.appendChild(opt);
        });
      }
    } catch (e) {
      console.warn('Could not list background videos for recognition:', e);
    }
  }
  loadSavedInputVideos();

  // 6. Action Triggers
  if (recogRunShortBtn) {
    recogRunShortBtn.addEventListener('click', () => {
      const target = (recogShortUrl ? recogShortUrl.value : '').trim();
      if (!target) {
        showToast('Please enter a YouTube Short or video URL.');
        if (recogShortUrl) recogShortUrl.focus();
        return;
      }
      executeRecognition('short', target);
    });
  }

  if (recogRunChannelBtn) {
    recogRunChannelBtn.addEventListener('click', () => {
      const target = (recogChannelUrl ? recogChannelUrl.value : '').trim();
      if (!target) {
        showToast('Please enter a YouTube Channel or Short URL.');
        if (recogChannelUrl) recogChannelUrl.focus();
        return;
      }
      executeRecognition('channel', target, recogState.topCount);
    });
  }

  if (recogRunLocalBtn) {
    recogRunLocalBtn.addEventListener('click', async () => {
      let target = '';
      if (recogState.selectedFile) {
        updateProgress(true, 15, `Uploading "${recogState.selectedFile.name}" for analysis...`);
        try {
          const uploadRes = await fetch(`/api/recognize-upload?name=${encodeURIComponent(recogState.selectedFile.name)}`, {
            method: 'POST',
            body: recogState.selectedFile
          });
          const uploadData = await uploadRes.json();
          if (!uploadRes.ok || !uploadData.filePath) {
            throw new Error(uploadData.error || 'Upload failed');
          }
          target = uploadData.filePath;
        } catch (err) {
          updateProgress(false);
          showToast(`File upload failed: ${err.message}`);
          return;
        }
      } else if (recogSavedVideoSelect && recogSavedVideoSelect.value) {
        target = recogSavedVideoSelect.value;
      }

      if (!target) {
        showToast('Please select or drop a video file first.');
        return;
      }

      executeRecognition('local', target);
    });
  }

  // 7. Core SSE Execution
  function executeRecognition(mode, target, topCount = 5) {
    if (recogState.isProcessing && recogState.eventSource) {
      recogState.eventSource.close();
    }

    recogState.isProcessing = true;
    setRunButtonsState(true);
    updateProgress(true, 5, 'Connecting to Song Recognition Engine...');

    if (recogResultsContainer) {
      recogResultsContainer.style.display = 'block';
      recogResultsContainer.innerHTML = '';
    }

    const sseUrl = `/api/recognize-stream?mode=${encodeURIComponent(mode)}&target=${encodeURIComponent(target)}&top_count=${encodeURIComponent(topCount)}`;
    const eventSource = new EventSource(sseUrl);
    recogState.eventSource = eventSource;

    let accumulatedChannelItems = [];

    eventSource.addEventListener('start', (e) => {
      try {
        const data = JSON.parse(e.data);
        updateProgress(true, 10, data.message || 'Starting song analysis...');
      } catch {}
    });

    eventSource.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data);
        updateProgress(true, data.percent || 30, data.message || 'Analyzing audio sample...');
      } catch {}
    });

    eventSource.addEventListener('short_item', (e) => {
      try {
        const item = JSON.parse(e.data);
        accumulatedChannelItems.push(item);
        renderChannelShortItem(item, recogResultsContainer);
      } catch {}
    });

    eventSource.addEventListener('complete', (e) => {
      try {
        const result = JSON.parse(e.data);
        updateProgress(true, 100, 'Song recognition complete!');
        setTimeout(() => updateProgress(false), 1800);

        if (result.mode === 'single_short' || result.mode === 'local_video') {
          renderSingleTrackResult(result.track, recogResultsContainer, { mode: result.mode, target: result.target });
        } else if (result.mode === 'channel_top') {
          if (accumulatedChannelItems.length === 0 && Array.isArray(result.results)) {
            result.results.forEach(it => renderChannelShortItem(it, recogResultsContainer));
          }
        }
      } catch (err) {
        console.error('Error handling recognition complete:', err);
      } finally {
        recogState.isProcessing = false;
        setRunButtonsState(false);
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (e) => {
      let errMsg = 'Recognition failed or was interrupted.';
      try {
        if (e.data) {
          const d = JSON.parse(e.data);
          if (d.error) errMsg = d.error;
        }
      } catch {}
      updateProgress(false);
      showToast(`⚠️ ${errMsg}`);
      recogState.isProcessing = false;
      setRunButtonsState(false);
      eventSource.close();
    });
  }

  function setRunButtonsState(isLoading) {
    [recogRunShortBtn, recogRunChannelBtn, recogRunLocalBtn].forEach(btn => {
      if (btn) {
        btn.disabled = isLoading;
        btn.classList.toggle('loading', isLoading);
      }
    });
  }

  function updateProgress(show, percent = 0, text = '') {
    if (!recogProgressBox) return;
    recogProgressBox.style.display = show ? 'block' : 'none';
    if (recogProgressText) recogProgressText.textContent = text;
    if (recogProgressPercent) recogProgressPercent.textContent = `${percent}%`;
    if (recogProgressFill) recogProgressFill.style.width = `${percent}%`;
  }

  // 8. Result Card Renderers
  function renderSingleTrackResult(track, container, meta) {
    if (!container) return;
    container.innerHTML = '';

    if (!track) {
      container.innerHTML = `
        <div class="recog-result-card" style="border-color: rgba(239, 68, 68, 0.4);">
          <div class="recog-track-header">
            <div class="recog-track-info">
              <span class="recog-track-title">❌ No Music Recognized</span>
              <span class="recog-track-artist">ACRCloud could not detect a recognizable song fingerprint in this video.</span>
            </div>
          </div>
        </div>
      `;
      return;
    }

    const title = track.title || 'Unknown Title';
    const singer = track.singer || 'Unknown Artist';
    const startSec = (track.start_seconds !== undefined && track.start_seconds !== null)
      ? Number(track.start_seconds)
      : ((track.timestamp_seconds !== undefined && track.timestamp_seconds !== null) ? Number(track.timestamp_seconds) : 0);
    const shortDur = (track.short_duration !== undefined && track.short_duration !== null && Number(track.short_duration) > 0)
      ? Number(track.short_duration)
      : 15;
    const endSec = (track.end_seconds !== undefined && track.end_seconds !== null && Number(track.end_seconds) > startSec)
      ? Number(track.end_seconds)
      : Number((startSec + shortDur).toFixed(2));
    const spotifyUrl = track.spotify_url || '';

    const card = document.createElement('div');
    card.className = 'recog-result-card';

    card.innerHTML = `
      <div class="recog-track-header">
        <div class="recog-track-info">
          <span class="recog-track-title">
            <span>🎵</span>
            <span>${escapeHtml(title)}</span>
          </span>
          <span class="recog-track-artist">🎤 ${escapeHtml(singer)}</span>
          <div class="recog-meta-badges">
            <span class="recog-meta-pill timestamp" title="Exact match offset in song">
              ⏱️ Match: ${startSec}s (${formatMinutesSeconds(startSec)})
            </span>
            <span class="recog-meta-pill duration" title="Short / Reel Duration">
              ⏳ Reel: ${shortDur}s
            </span>
            <span class="recog-meta-pill window" title="Video Overlay Render Window">
              🎯 Range: ${startSec}s – ${endSec}s (${formatMinutesSeconds(startSec)} - ${formatMinutesSeconds(endSec)})
            </span>
            ${spotifyUrl ? `
              <a href="${spotifyUrl}" target="_blank" rel="noopener" class="recog-meta-pill spotify" title="Open in Spotify">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#1ed760"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12C24 5.373 18.627 0 12 0zm5.502 17.308c-.217.355-.679.467-1.034.25-2.836-1.733-6.407-2.124-10.612-1.163-.404.093-.807-.162-.9-.567-.093-.404.163-.807.568-.9 4.606-1.052 8.562-.607 11.728 1.346.355.217.467.679.25 1.034zm1.47-3.268c-.273.444-.855.584-1.299.311-3.245-1.995-8.192-2.573-12.03-1.407-.497.151-1.026-.135-1.177-.633-.151-.498.136-1.026.634-1.177 4.385-1.332 9.839-.687 13.561 1.606.444.274.584.856.311 1.3zm.126-3.41c-3.89-2.31-10.309-2.523-14.032-1.392-.596.182-1.229-.161-1.411-.758-.181-.597.162-1.229.759-1.411 4.283-1.3 11.37-1.055 15.827 1.591.536.318.71 1.011.392 1.547-.318.536-1.01.71-1.546.392z"/></svg>
                Spotify Link Found
              </a>
            ` : `
              <span class="recog-meta-pill" style="color: var(--text-muted);">No direct Spotify link</span>
            `}
          </div>
        </div>
      </div>
      <div class="recog-card-actions">
        <button type="button" class="recog-send-pipeline-btn" id="btn-send-to-pipeline">
          <span>✨ Send to Lyric Pipeline</span>
        </button>
        <button type="button" class="recog-generate-direct-btn" id="btn-send-and-generate">
          <span>⚡ Send &amp; Generate Immediately</span>
        </button>
      </div>
    `;

    card.querySelector('#btn-send-to-pipeline').addEventListener('click', () => {
      sendSongToLyricPipeline(track, false);
    });

    card.querySelector('#btn-send-and-generate').addEventListener('click', () => {
      sendSongToLyricPipeline(track, true);
    });

    container.appendChild(card);
  }

  function renderChannelShortItem(item, container) {
    if (!container) return;
    let listWrap = container.querySelector('.recog-shorts-list');
    if (!listWrap) {
      container.innerHTML = `
        <div class="recog-channel-results-header">
          <span class="recog-channel-name-title">📺 Recognized Channel Shorts</span>
        </div>
        <div class="recog-shorts-list"></div>
      `;
      listWrap = container.querySelector('.recog-shorts-list');
    }

    const short = item.short || {};
    const track = item.track;
    const itemCard = document.createElement('div');
    itemCard.className = 'recog-short-item-card';

    const shortUrl = short.url || '#';
    const shortTitle = short.title || 'Untitled Short';
    const viewsStr = short.views ? `${(short.views / 1000).toFixed(0)}K views` : '';

    if (track) {
      const startSec = (track.start_seconds !== undefined && track.start_seconds !== null)
        ? Number(track.start_seconds)
        : ((track.timestamp_seconds !== undefined && track.timestamp_seconds !== null) ? Number(track.timestamp_seconds) : 0);
      const shortDur = (track.short_duration !== undefined && track.short_duration !== null && Number(track.short_duration) > 0)
        ? Number(track.short_duration)
        : 15;
      const endSec = (track.end_seconds !== undefined && track.end_seconds !== null && Number(track.end_seconds) > startSec)
        ? Number(track.end_seconds)
        : Number((startSec + shortDur).toFixed(2));

      itemCard.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
          <span class="recog-short-rank">#${short.rank || 1}</span>
          <div class="recog-short-main">
            <a href="${shortUrl}" target="_blank" rel="noopener" class="recog-short-title-link">
              🎬 ${escapeHtml(shortTitle)} ${viewsStr ? `· <span style="font-size:0.75rem; color:var(--text-muted);">${viewsStr}</span>` : ''}
            </a>
            <div class="recog-short-identified-track">
              <strong>🎵 ${escapeHtml(track.title)}</strong> · ${escapeHtml(track.singer)}
              <span class="recog-meta-pill timestamp" style="padding: 1px 6px; font-size: 0.72rem;">⏱️ ${startSec}s</span>
              <span class="recog-meta-pill duration" style="padding: 1px 6px; font-size: 0.72rem;">⏳ ${shortDur}s</span>
              <span class="recog-meta-pill window" style="padding: 1px 6px; font-size: 0.72rem;">🎯 ${startSec}s - ${endSec}s</span>
              ${track.spotify_url ? `
                <a href="${track.spotify_url}" target="_blank" rel="noopener" class="recog-meta-pill spotify" style="padding: 1px 6px; font-size: 0.72rem;">
                  Spotify
                </a>
              ` : ''}
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 6px;">
          <button type="button" class="recog-send-pipeline-btn" style="padding: 6px 10px; font-size: 0.78rem;">
            <span>✨ Pipeline</span>
          </button>
          <button type="button" class="recog-generate-direct-btn" style="padding: 6px 10px; font-size: 0.78rem;">
            <span>⚡ Generate</span>
          </button>
        </div>
      `;

      itemCard.querySelector('.recog-send-pipeline-btn').addEventListener('click', () => {
        sendSongToLyricPipeline(track, false);
      });

      itemCard.querySelector('.recog-generate-direct-btn').addEventListener('click', () => {
        sendSongToLyricPipeline(track, true);
      });
    } else {
      itemCard.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
          <span class="recog-short-rank">#${short.rank || 1}</span>
          <div class="recog-short-main">
            <a href="${shortUrl}" target="_blank" rel="noopener" class="recog-short-title-link">
              🎬 ${escapeHtml(shortTitle)} ${viewsStr ? `· <span style="font-size:0.75rem; color:var(--text-muted);">${viewsStr}</span>` : ''}
            </a>
            <div class="recog-no-song-tag">No recognizable music detected</div>
          </div>
        </div>
      `;
    }

    listWrap.appendChild(itemCard);
  }

  // 9. Send Identified Track & Timestamps into Pipeline
  function sendSongToLyricPipeline(track, autoGenerate = false) {
    if (!track) return;

    const spotifyUrl = track.spotify_url || '';
    const title = track.title || '';
    const singer = track.singer || '';
    const queryValue = spotifyUrl || `${title} ${singer}`.trim();

    // Resolve exact match start timestamp in song and original short duration
    const startSec = (track.start_seconds !== undefined && track.start_seconds !== null)
      ? Number(track.start_seconds)
      : ((track.timestamp_seconds !== undefined && track.timestamp_seconds !== null) ? Number(track.timestamp_seconds) : 0);

    const shortDur = (track.short_duration !== undefined && track.short_duration !== null && Number(track.short_duration) > 0)
      ? Number(track.short_duration)
      : ((track.duration !== undefined && track.duration !== null && Number(track.duration) > 0) ? Number(track.duration) : 15);

    const endSec = (track.end_seconds !== undefined && track.end_seconds !== null && Number(track.end_seconds) > startSec)
      ? Number(track.end_seconds)
      : Number((startSec + shortDur).toFixed(2));

    // A. Populate Main Command Search Form
    if (songQueryInput) {
      songQueryInput.value = queryValue;
      songQueryInput.classList.remove('pipeline-input-highlighted');
      void songQueryInput.offsetWidth; // Reflow
      songQueryInput.classList.add('pipeline-input-highlighted');
    }

    // B. Set exact match start timestamp from original reel
    if (testStartInput) {
      testStartInput.value = String(startSec);
      testStartInput.classList.remove('pipeline-input-highlighted');
      void testStartInput.offsetWidth; // Reflow
      testStartInput.classList.add('pipeline-input-highlighted');
    }
    state.testStart = startSec;

    // C. Set exact end timestamp keeping the duration identical to the short
    if (testEndInput) {
      testEndInput.value = String(endSec);
      testEndInput.classList.remove('pipeline-input-highlighted');
      void testEndInput.offsetWidth; // Reflow
      testEndInput.classList.add('pipeline-input-highlighted');
    }
    state.testEnd = endSec;

    // D. Reset viral hook selector so it does not override recognized timestamps
    if (viralHookSelect) {
      viralHookSelect.value = 'custom';
    }

    // E. Switch to direct generator tab
    if (tabDirectGenerator) {
      tabDirectGenerator.click();
    }

    // F. Smoothly scroll to the generator command form
    if (generatorForm) {
      generatorForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // G. Show toast feedback with exact match & duration details
    showToast(`✅ Loaded "${title || 'Track'}" (${startSec}s - ${endSec}s · ${shortDur}s duration) into Lyric Pipeline!`);

    // H. Immediate video generation if requested
    if (autoGenerate) {
      startGenerationPipeline(queryValue);
    }
  }

  function formatMinutesSeconds(seconds) {
    const s = Math.max(0, Math.floor(seconds));
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
}

// Initialize Song Recognition Studio on load
initSongRecognitionStudio();

// ==============================================================================
// 📅 Metricool Social Hub Schedule Bridge
// ==============================================================================
function initSocialHubScheduleBridge() {
  const scheduleBtn = document.getElementById('schedule-to-hub-btn');
  const modal = document.getElementById('schedule-hub-modal');
  const closeBtn = document.getElementById('close-schedule-modal-btn');
  const cancelBtn = document.getElementById('cancel-schedule-modal-btn');
  const confirmBtn = document.getElementById('confirm-schedule-modal-btn');
  const brandSelect = document.getElementById('hub-brand-select');
  const captionInput = document.getElementById('hub-post-caption');
  const dateInput = document.getElementById('hub-post-date');
  const timeInput = document.getElementById('hub-post-time');

  if (!scheduleBtn || !modal) return;

  scheduleBtn.addEventListener('click', async () => {
    modal.style.display = 'flex';
    const now = new Date();
    if (dateInput) dateInput.value = now.toISOString().slice(0, 10);
    if (timeInput) timeInput.value = '18:00';

    const currentSong = typeof songInput !== 'undefined' && songInput ? songInput.value.trim() : '';
    const currentHeader = typeof topHeaderInput !== 'undefined' && topHeaderInput ? topHeaderInput.value.trim() : '';
    if (captionInput) {
      captionInput.value = currentHeader || `When lyrics feel too personal... 🤌🤍 ${currentSong ? '#' + currentSong.replace(/[^a-zA-Z0-9]/g, '') : ''}`;
    }

    try {
      const res = await fetch('http://localhost:8000/api/brands');
      if (res.ok && brandSelect) {
        const brands = await res.json();
        brandSelect.innerHTML = '';
        brands.forEach(b => {
          const opt = document.createElement('option');
          opt.value = b.id;
          opt.textContent = b.name;
          brandSelect.appendChild(opt);
        });
      }
    } catch (e) {
      if (brandSelect) brandSelect.innerHTML = '<option value="default">Main Brand (Default)</option>';
    }
  });

  const closeModal = () => { modal.style.display = 'none'; };
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  if (confirmBtn) {
    confirmBtn.addEventListener('click', async () => {
      confirmBtn.disabled = true;
      confirmBtn.textContent = 'Scheduling...';

      const brandId = brandSelect ? brandSelect.value : 'default';
      const caption = captionInput ? captionInput.value.trim() : '';
      const scheduledTime = `${dateInput ? dateInput.value : ''}T${timeInput ? timeInput.value : '18:00'}:00`;

      const platforms = [];
      if (document.getElementById('hub-plat-ig')?.checked) platforms.push('instagram');
      if (document.getElementById('hub-plat-fb')?.checked) platforms.push('facebook');
      if (document.getElementById('hub-plat-threads')?.checked) platforms.push('threads');
      if (document.getElementById('hub-plat-yt')?.checked) platforms.push('youtube');

      const dlBtn = document.getElementById('dl-video-btn');
      const videoHref = dlBtn ? dlBtn.getAttribute('href') : '';
      const videoFileName = videoHref ? videoHref.split('/').pop() : '';

      const payload = {
        brand_id: brandId,
        target_platforms: platforms,
        post_type: 'reel',
        media_paths: videoFileName ? [`videos/output/${videoFileName}`] : [],
        caption: caption,
        scheduled_time: scheduledTime,
        share_to_facebook: platforms.includes('facebook'),
        share_to_threads: platforms.includes('threads')
      };

      try {
        const res = await fetch('http://localhost:8000/api/posts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          closeModal();
          showToast('✅ Post scheduled to Metricool Hub!');
        } else {
          throw new Error(await res.text());
        }
      } catch (e) {
        alert('Could not schedule post to Social Hub (is it running on port 8000?): ' + e.message);
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Schedule Post 🚀';
      }
    });
  }
}

initSocialHubScheduleBridge();

