// State Management
const state = {
  brands: [],
  currentBrandId: null,
  posts: [],
  media: { videos: [], carousels: [] },
  calendarDate: new Date(),
  activeTab: 'folders',
  showBestTimes: false,
  previewPlatform: 'instagram',
  accountsVerifiedOnly: true,
  accountsPlatformFilter: 'all',
  accountsData: null,
  folderStatus: [],
  csvRawText: null,
  csvValidationData: null
};

// DOM Elements
const brandSelect = document.getElementById('brand-select');
const brandColorDot = document.getElementById('brand-color-dot');
const calendarMonthTitle = document.getElementById('calendar-month-title');
const calendarDaysGrid = document.getElementById('calendar-days-grid');
const composerModal = document.getElementById('composer-modal');
const brandModal = document.getElementById('brand-modal');
const trackUrlModal = document.getElementById('track-url-modal');
const competitorModal = document.getElementById('competitor-modal');
const bulkModal = document.getElementById('bulk-modal');
const composerMediaSelect = document.getElementById('composer-media-select');
const composerCaption = document.getElementById('composer-caption');
const composerFirstComment = document.getElementById('composer-first-comment');
const captionCount = document.getElementById('caption-count');
const phoneCaptionPreview = document.getElementById('phone-caption-preview');
const phonePreviewScreen = document.getElementById('phone-preview-screen');
const toast = document.getElementById('toast');
const btnToggleBestTimes = document.getElementById('btn-toggle-best-times');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigationTabs();
  setupEventListeners();
  await loadBrands();
  await loadFolderQueues();
  await loadGeneratedMedia();
  renderCalendar();
  loadAnalytics();
  loadAccounts(); // Check live account status once on startup
  setInterval(() => {
    loadAccounts();
  }, 30 * 60 * 1000); // Gentle background refresh every 30 minutes
});

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.style.display = 'block';
  setTimeout(() => { toast.style.display = 'none'; }, 3500);
}

// Navigation Tabs
function setupNavigationTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const target = btn.dataset.tab;
      state.activeTab = target;

      document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
      const activePanel = document.getElementById(`view-${target}`);
      if (activePanel) activePanel.classList.add('active');

      if (target === 'folders') loadFolderQueues();
      if (target === 'planner') renderCalendar();
      if (target === 'feed') loadFeedPreview();
      if (target === 'competitors') loadCompetitors();
      if (target === 'evergreen') loadEvergreen();
      if (target === 'queue') loadQueue();
      if (target === 'analytics') loadAnalytics();
      if (target === 'accounts') loadAccounts(true);
    });
  });
}

// Event Listeners
function setupEventListeners() {
  // Calendar Nav
  document.getElementById('cal-prev-btn').addEventListener('click', () => {
    state.calendarDate.setMonth(state.calendarDate.getMonth() - 1);
    renderCalendar();
  });
  document.getElementById('cal-next-btn').addEventListener('click', () => {
    state.calendarDate.setMonth(state.calendarDate.getMonth() + 1);
    renderCalendar();
  });
  document.getElementById('cal-today-btn').addEventListener('click', () => {
    state.calendarDate = new Date();
    renderCalendar();
  });

  // Best Times Heatmap Toggle
  if (btnToggleBestTimes) {
    btnToggleBestTimes.addEventListener('click', () => {
      state.showBestTimes = !state.showBestTimes;
      btnToggleBestTimes.classList.toggle('active', state.showBestTimes);
      renderCalendar();
      showToast(state.showBestTimes ? '🔥 Best Times Heatmap Active (Peak Audience Slots)' : 'Heatmap Disabled');
    });
  }

  // Composer Modal Open/Close
  document.getElementById('btn-open-composer').addEventListener('click', () => openComposer());
  document.getElementById('btn-close-composer').addEventListener('click', () => closeComposer());
  document.getElementById('btn-cancel-composer').addEventListener('click', () => closeComposer());

  const btnFeedAdd = document.getElementById('btn-feed-add-post');
  if (btnFeedAdd) btnFeedAdd.addEventListener('click', () => openComposer());

  // Bulk Scheduler Modal Open/Close
  const btnBulk1 = document.getElementById('btn-open-bulk');
  const btnBulk2 = document.getElementById('btn-open-bulk-2');
  if (btnBulk1) btnBulk1.addEventListener('click', () => openBulkModal());
  if (btnBulk2) btnBulk2.addEventListener('click', () => openBulkModal());
  document.getElementById('btn-close-bulk').addEventListener('click', () => { bulkModal.style.display = 'none'; });
  document.getElementById('btn-cancel-bulk').addEventListener('click', () => { bulkModal.style.display = 'none'; });
  document.getElementById('btn-submit-bulk').addEventListener('click', handleBulkSchedule);

  // CSV Importer Modal Listeners
  const btnOpenCsv = document.getElementById('btn-open-csv-import');
  if (btnOpenCsv) btnOpenCsv.addEventListener('click', () => openCsvImportModal());
  const btnCloseCsv = document.getElementById('btn-close-csv-modal') || document.getElementById('btn-close-csv-import');
  if (btnCloseCsv) btnCloseCsv.addEventListener('click', () => closeCsvImportModal());
  const btnCancelCsv = document.getElementById('btn-csv-cancel');
  if (btnCancelCsv) btnCancelCsv.addEventListener('click', () => closeCsvImportModal());
  const btnChooseCsv = document.getElementById('btn-csv-choose-file');
  const csvDropzone = document.getElementById('csv-upload-dropzone');
  const btnCsvBack = document.getElementById('btn-csv-back');
  if (btnCsvBack) btnCsvBack.addEventListener('click', () => showCsvUploadStep());
  const btnCsvImport = document.getElementById('btn-csv-execute-import');
  if (btnCsvImport) btnCsvImport.addEventListener('click', () => executeCsvImport());

  const csvFileInput = document.getElementById('csv-file-input');
  if (csvFileInput) {
    csvFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleCsvFileSelect(e.target.files[0]);
      }
    });
  }
  if (btnChooseCsv && csvFileInput) btnChooseCsv.addEventListener('click', (event) => {
    event.stopPropagation();
    csvFileInput.click();
  });
  if (csvDropzone) {
    csvDropzone.addEventListener('click', () => csvFileInput && csvFileInput.click());
    csvDropzone.addEventListener('keydown', (event) => {
      if ((event.key === 'Enter' || event.key === ' ') && csvFileInput) {
        event.preventDefault();
        csvFileInput.click();
      }
    });
    ['dragenter', 'dragover'].forEach((eventName) => csvDropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      csvDropzone.classList.add('is-dragging');
    }));
    ['dragleave', 'drop'].forEach((eventName) => csvDropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      csvDropzone.classList.remove('is-dragging');
    }));
    csvDropzone.addEventListener('drop', (event) => {
      const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
      if (file) handleCsvFileSelect(file);
    });
  }

  const csvDateFormat = document.getElementById('csv-date-format');
  if (csvDateFormat) csvDateFormat.addEventListener('change', () => validateCurrentCsv());
  if (csvTimeFormat) csvTimeFormat.addEventListener('change', () => validateCurrentCsv());

  // Brand Folders & Master Broadcast Action Listeners
  const btnMasterPost = document.getElementById('btn-master-post-all');
  if (btnMasterPost) btnMasterPost.addEventListener('click', () => triggerPublishAllBrands());
  const btnHeroPost = document.getElementById('btn-hero-post-all');
  if (btnHeroPost) btnHeroPost.addEventListener('click', () => triggerPublishAllBrands());
  const btnRefreshFolders = document.getElementById('btn-refresh-folders');
  if (btnRefreshFolders) btnRefreshFolders.addEventListener('click', () => loadFolderQueues());
  const btnOpenAllFolders = document.getElementById('btn-open-all-folders');
  if (btnOpenAllFolders) btnOpenAllFolders.addEventListener('click', () => openAllFolders());
  const btnHeroOpenFolders = document.getElementById('btn-hero-open-folders');
  if (btnHeroOpenFolders) btnHeroOpenFolders.addEventListener('click', () => openAllFolders());

  const btnCloseBroadcast = document.getElementById('btn-close-broadcast');
  if (btnCloseBroadcast) btnCloseBroadcast.addEventListener('click', () => closeBroadcastModal());
  const btnDoneBroadcast = document.getElementById('btn-done-broadcast');
  if (btnDoneBroadcast) btnDoneBroadcast.addEventListener('click', () => closeBroadcastModal());

  // Competitor Modal Open/Close
  const btnOpenComp = document.getElementById('btn-open-add-competitor');
  if (btnOpenComp) btnOpenComp.addEventListener('click', () => { competitorModal.style.display = 'flex'; });
  document.getElementById('btn-close-competitor').addEventListener('click', () => { competitorModal.style.display = 'none'; });
  document.getElementById('btn-cancel-competitor').addEventListener('click', () => { competitorModal.style.display = 'none'; });
  document.getElementById('btn-save-competitor').addEventListener('click', handleAddCompetitor);

  // Competitor Refresh Button
  const btnRefreshComp = document.getElementById('btn-refresh-competitors');
  if (btnRefreshComp) {
    btnRefreshComp.addEventListener('click', async () => {
      showToast('🔄 Scraping live competitor metrics...');
      btnRefreshComp.style.opacity = '0.5';
      try {
        await fetch(`/api/competitors/refresh?brand_id=${state.currentBrandId || ''}`, { method: 'POST' });
        showToast('Competitor metrics updated!');
        await loadCompetitors();
      } catch (e) {
        showToast('Refresh finished.');
      } finally {
        btnRefreshComp.style.opacity = '1';
      }
    });
  }

  // Evergreen Auto-fill Button
  const btnAutoFill = document.getElementById('btn-trigger-autofill');
  if (btnAutoFill) {
    btnAutoFill.addEventListener('click', async () => {
      showToast('⚡ Scanning next 7 days and recycling evergreen content...');
      try {
        const res = await fetch('/api/evergreen/auto-fill-queue', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brand_id: state.currentBrandId, days_ahead: 7, preferred_time: '19:30' })
        });
        const data = await res.json();
        showToast(`✅ ${data.message || `Scheduled ${data.scheduled_count} recycled posts!`}`);
        await loadEvergreen();
        renderCalendar();
      } catch (e) {
        alert('Autofill error: ' + e.message);
      }
    });
  }

  // Brand Modal
  document.getElementById('btn-add-brand').addEventListener('click', () => { brandModal.style.display = 'flex'; });
  document.getElementById('btn-close-brand').addEventListener('click', () => { brandModal.style.display = 'none'; });
  document.getElementById('btn-cancel-brand').addEventListener('click', () => { brandModal.style.display = 'none'; });
  document.getElementById('btn-save-brand').addEventListener('click', handleCreateBrand);

  // Sync .env Credentials Button
  const btnSyncEnv = document.getElementById('btn-sync-env');
  if (btnSyncEnv) {
    btnSyncEnv.addEventListener('click', async () => {
      btnSyncEnv.textContent = '⏳';
      btnSyncEnv.style.opacity = '0.6';
      showToast('🔑 Syncing credentials from .env and authenticating accounts...');
      try {
        const res = await fetch('/api/sync-credentials', { method: 'POST' });
        const data = await res.json();
        const r = data.result || {};
        await loadBrands();
        loadAccounts(true);
        btnSyncEnv.textContent = '✅';
        const brands = r.brands_synced || [];
        let summary = '';
        if (brands.length > 0) {
          const igAccounts = brands.filter(b => b.instagram).map(b => `@${b.instagram}`);
          const igPart = igAccounts.length > 0 ? `IG: ${igAccounts.join(', ')}` : 'No IG';
          summary = `${brands.length} brand(s) [${igPart}]`;
        } else if (r.instagram) {
          summary = `IG: @${r.instagram} (${r.instagram_status || 'active'})`;
        } else {
          summary = 'No brands found in .env';
        }
        showToast(`✅ Synced from .env! ${summary}`);
        setTimeout(() => {
          btnSyncEnv.textContent = '🔑';
          btnSyncEnv.style.opacity = '1';
        }, 2500);
      } catch (err) {
        btnSyncEnv.textContent = '⚠️';
        showToast('⚠️ Could not sync credentials. Check terminal output.');
        setTimeout(() => {
          btnSyncEnv.textContent = '🔑';
          btnSyncEnv.style.opacity = '1';
        }, 2500);
      }
    });
  }

  // Track URL Modal (Analytics)
  const btnTrackUrl = document.getElementById('btn-track-url');
  if (btnTrackUrl) {
    btnTrackUrl.addEventListener('click', () => { trackUrlModal.style.display = 'flex'; });
    document.getElementById('btn-close-track-modal').addEventListener('click', () => { trackUrlModal.style.display = 'none'; });
    document.getElementById('btn-cancel-track-modal').addEventListener('click', () => { trackUrlModal.style.display = 'none'; });
    document.getElementById('btn-save-track-url').addEventListener('click', handleTrackUrl);
  }

  // Analytics Refresh Button
  const btnRefresh = document.getElementById('btn-refresh-analytics');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      showToast('🔄 Running zero-login scrapers across all public links...');
      btnRefresh.style.opacity = '0.5';
      try {
        const res = await fetch('/api/analytics/refresh-all', { method: 'POST' });
        const data = await res.json();
        showToast(`✅ Updated ${data.processed_count || 0} links with latest metrics!`);
        await loadAnalytics();
      } catch (e) {
        showToast('Scraper refresh finished.');
        await loadAnalytics();
      } finally {
        btnRefresh.style.opacity = '1';
      }
    });
  }

  // Caption Live Sync
  composerCaption.addEventListener('input', () => {
    const val = composerCaption.value;
    captionCount.textContent = `${val.length} / 2200`;
    phoneCaptionPreview.textContent = val || 'Your caption will appear here...';
  });

  // Media preview sync
  composerMediaSelect.addEventListener('change', () => {
    updateMediaPreview();
  });

  // Best Times Smart Recommendation Chips in Composer
  const bestTimeChips = document.querySelectorAll('.best-time-chip');
  bestTimeChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const timeVal = chip.dataset.time;
      document.getElementById('composer-time').value = timeVal;
      const today = new Date().toISOString().slice(0, 10);
      if (!document.getElementById('composer-date').value) {
        document.getElementById('composer-date').value = today;
      }
      showToast(`⚡ Selected peak time: ${timeVal} (${chip.dataset.score}% audience active)`);
    });
  });

  // Platform Preview Switcher (Reels vs Shorts vs Thread)
  const prevTabs = document.querySelectorAll('.prev-tab-btn');
  prevTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      prevTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.previewPlatform = btn.dataset.previewType;
      updateMediaPreview();
    });
  });

  // Submit Post
  document.getElementById('btn-submit-post').addEventListener('click', () => handleSubmitPost(false));
  document.getElementById('btn-publish-now').addEventListener('click', () => handleSubmitPost(true));

  // Feed Refresh Button
  const btnFeedRefresh = document.getElementById('btn-feed-refresh');
  if (btnFeedRefresh) {
    btnFeedRefresh.addEventListener('click', () => {
      showToast('🔄 Refreshing real-time Instagram feed & profile stats...');
      loadFeedPreview();
    });
  }

  // Accounts Tab Listeners
  const btnAccountsRefresh = document.getElementById('btn-accounts-refresh');
  if (btnAccountsRefresh) {
    btnAccountsRefresh.addEventListener('click', () => {
      window._hasAutoRetriedAccounts = false;
      showToast('🔄 Refreshing account verification status across all services...');
      loadAccounts(true);
    });
  }

  const btnAccountsSyncEnv = document.getElementById('btn-accounts-sync-env');
  if (btnAccountsSyncEnv) {
    btnAccountsSyncEnv.addEventListener('click', async () => {
      showToast('🔑 Syncing credentials from .env...');
      try {
        await fetch('/api/sync-credentials', { method: 'POST' });
        showToast('✅ .env synced. Checking sessions...');
        await loadAccounts();
      } catch (e) {
        showToast('Sync error: ' + e.message);
      }
    });
  }

  const chkVerifiedOnly = document.getElementById('chk-verified-only');
  if (chkVerifiedOnly) {
    chkVerifiedOnly.addEventListener('change', (e) => {
      state.accountsVerifiedOnly = e.target.checked;
      const indicator = document.getElementById('accounts-filter-indicator');
      if (indicator) {
        indicator.textContent = state.accountsVerifiedOnly 
          ? 'Filtered: Showing 100% verified' 
          : 'Showing all accounts (including unverified)';
      }
      renderAccountsGrid();
    });
  }

  const accountsPlatformFilters = document.getElementById('accounts-platform-filters');
  if (accountsPlatformFilters) {
    accountsPlatformFilters.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        accountsPlatformFilters.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        state.accountsPlatformFilter = chip.dataset.filter;
        renderAccountsGrid();
      });
    });
  }

  // Brand Switch
  brandSelect.addEventListener('change', () => {
    state.currentBrandId = brandSelect.value;
    updateBrandDot();
    renderCalendar();
    if (state.activeTab === 'feed') loadFeedPreview();
    if (state.activeTab === 'competitors') loadCompetitors();
    if (state.activeTab === 'evergreen') loadEvergreen();
    if (state.activeTab === 'queue') loadQueue();
    if (state.activeTab === 'analytics') loadAnalytics();
    if (state.activeTab === 'accounts') loadAccounts();
  });
}

function updateMediaPreview() {
  const selectedPath = composerMediaSelect.value;
  if (!selectedPath) {
    phonePreviewScreen.innerHTML = '<div class="preview-placeholder-text">Select media above to see instant preview</div>';
    return;
  }
  const item = state.media.videos.find(v => v.path === selectedPath);
  if (!item) return;

  const badge = state.previewPlatform === 'youtube'
    ? '<span style="position:absolute; bottom:8px; right:8px; background:#ff0000; color:#fff; font-size:9px; font-weight:800; padding:2px 5px; border-radius:3px;">Shorts</span>'
    : state.previewPlatform === 'threads'
    ? '<span style="position:absolute; top:8px; left:8px; background:#000; color:#fff; font-size:9px; font-weight:800; padding:2px 5px; border-radius:3px;">@threads</span>'
    : '<span style="position:absolute; bottom:8px; right:8px; background:rgba(0,0,0,0.6); color:#fff; font-size:9px; font-weight:800; padding:2px 5px; border-radius:3px;">🎵 Original Audio</span>';

  phonePreviewScreen.innerHTML = `
    <div style="position:relative; width:100%; height:100%;">
      <video src="${item.preview_url}" autoplay loop muted style="width:100%; height:100%; object-fit:cover;"></video>
      ${badge}
    </div>
  `;
}

// Brand Loading & Switching
async function loadBrands() {
  try {
    const res = await fetch('/api/brands');
    const brands = await res.json();
    state.brands = brands;
    brandSelect.innerHTML = '';
    brands.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.name;
      brandSelect.appendChild(opt);
    });
    if (brands.length > 0) {
      state.currentBrandId = brands[0].id;
      brandSelect.value = state.currentBrandId;
      updateBrandDot();
    }
  } catch (err) {
    console.error('Error loading brands:', err);
  }
}

function updateBrandDot() {
  const current = state.brands.find(b => b.id === state.currentBrandId);
  if (current && brandColorDot) {
    brandColorDot.style.background = current.color_badge || '#8ACE00';
  }
}

async function handleCreateBrand() {
  const nameInput = document.getElementById('new-brand-name');
  const colorInput = document.getElementById('new-brand-color');
  const name = nameInput.value.trim();
  if (!name) return alert('Enter brand name');

  try {
    const res = await fetch('/api/brands', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, color_badge: colorInput.value })
    });
    if (!res.ok) throw new Error(await res.text());
    brandModal.style.display = 'none';
    nameInput.value = '';
    showToast(`Brand "${name}" created!`);
    await loadBrands();
    renderCalendar();
  } catch (err) {
    alert('Error creating brand: ' + err.message);
  }
}

// Competitors Manager
async function loadCompetitors() {
  const container = document.getElementById('competitor-cards-container');
  container.innerHTML = '<div style="color:#888; padding:20px;">Loading competitor metrics...</div>';
  try {
    const res = await fetch(`/api/competitors?brand_id=${state.currentBrandId || ''}`);
    const competitors = await res.json();
    if (competitors.length === 0) {
      container.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-state-icon">📡</div>
          <div class="empty-state-title">No Competitors Monitored Yet</div>
          <div class="empty-state-desc">Benchmark public YouTube &amp; Instagram creator channels without login. Track subscriber pace, view trajectories, and posting rhythm.</div>
          <button type="button" class="btn-primary" onclick="document.getElementById('competitor-modal').style.display='flex'">
            <span>➕ Track First Competitor</span>
          </button>
        </div>
      `;
      return;
    }
    container.innerHTML = '';
    competitors.forEach(c => {
      const card = document.createElement('div');
      card.className = 'competitor-card';
      const icon = c.platform === 'youtube' ? '📺' : '📸';
      card.innerHTML = `
        <div class="comp-header">
          <div class="comp-title-group">
            <span class="comp-platform-icon">${icon}</span>
            <div>
              <div class="comp-name">${escapeHtml(c.display_name || c.account_handle)}</div>
              <div class="comp-handle">${escapeHtml(c.account_handle)}</div>
            </div>
          </div>
          <button class="btn-subtle" onclick="deleteCompetitorItem('${c.id}')" title="Delete competitor">✕</button>
        </div>
        <div class="comp-stats-row">
          <div>
            <div class="comp-stat-val">${(c.followers || 0).toLocaleString()}</div>
            <div class="comp-stat-lbl">Followers</div>
          </div>
          <div>
            <div class="comp-stat-val">${(c.total_posts || 0).toLocaleString()}</div>
            <div class="comp-stat-lbl">Total Posts</div>
          </div>
          <div>
            <div class="comp-stat-val">${(c.recent_avg_views || 0).toLocaleString()}</div>
            <div class="comp-stat-lbl">Avg Views</div>
          </div>
        </div>
        <div class="comp-footer">
          <span>Platform: <b>${c.platform.toUpperCase()}</b></span>
          <span>Updated: ${c.last_scraped_at ? c.last_scraped_at.slice(0, 10) : 'Pending'}</span>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    container.innerHTML = '<div style="color:#ef4444;">Could not load competitors.</div>';
  }
}

async function handleAddCompetitor() {
  const handle = document.getElementById('comp-handle-input').value.trim();
  const platform = document.getElementById('comp-platform-select').value;
  const name = document.getElementById('comp-name-input').value.trim();

  if (!handle) return alert('Enter account handle or link');

  try {
    const res = await fetch('/api/competitors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_id: state.currentBrandId || (state.brands[0] ? state.brands[0].id : 'main'),
        platform: platform,
        account_handle: handle,
        display_name: name || handle
      })
    });
    if (!res.ok) throw new Error(await res.text());
    competitorModal.style.display = 'none';
    document.getElementById('comp-handle-input').value = '';
    document.getElementById('comp-name-input').value = '';
    showToast(`Tracking competitor ${handle}!`);
    await loadCompetitors();
  } catch (e) {
    alert('Error adding competitor: ' + e.message);
  }
}

window.deleteCompetitorItem = async function(id) {
  if (!confirm('Stop tracking this competitor?')) return;
  await fetch(`/api/competitors/${id}`, { method: 'DELETE' });
  loadCompetitors();
};

// Evergreen Library Manager
async function loadEvergreen() {
  const container = document.getElementById('evergreen-posts-list');
  container.innerHTML = '<div style="color:#888;">Loading evergreen library...</div>';
  try {
    const res = await fetch(`/api/evergreen?brand_id=${state.currentBrandId || ''}`);
    const items = await res.json();

    document.getElementById('evergreen-active-count').textContent = items.length;
    const totalRecycles = items.reduce((acc, curr) => acc + (curr.times_posted || 0), 0);
    document.getElementById('evergreen-recycle-count').textContent = totalRecycles;

    if (items.length === 0) {
      container.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-state-icon">♻️</div>
          <div class="empty-state-title">Evergreen Pool is Empty</div>
          <div class="empty-state-desc">Save your top lyric videos to your evergreen library so Social Hub can automatically recycle them into upcoming peak audience windows.</div>
          <button type="button" class="btn-primary" onclick="openComposer()">
            <span>✍️ Schedule Evergreen Post</span>
          </button>
        </div>
      `;
      return;
    }
    container.innerHTML = '';
    items.forEach(p => {
      const card = document.createElement('div');
      card.className = 'evergreen-card';
      card.innerHTML = `
        <div class="evergreen-card-caption">${escapeHtml(p.caption || 'Evergreen Video Post')}</div>
        <div class="evergreen-card-meta">
          <span class="badge-repeats">Recycled: ${p.times_posted} / ${p.max_repeats}</span>
          <button class="btn-subtle" onclick="deleteEvergreenItem('${p.id}')">Remove</button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    container.innerHTML = '<div style="color:#ef4444;">Failed to load evergreen library.</div>';
  }
}

window.deleteEvergreenItem = async function(id) {
  if (!confirm('Remove this post from the evergreen pool?')) return;
  await fetch(`/api/evergreen/${id}`, { method: 'DELETE' });
  loadEvergreen();
};

// Bulk Batch Scheduler
function openBulkModal() {
  bulkModal.style.display = 'flex';
  const container = document.getElementById('bulk-media-checkboxes');
  container.innerHTML = '';

  const today = new Date();
  today.setDate(today.getDate() + 1);
  document.getElementById('bulk-start-date').value = today.toISOString().slice(0, 10);

  if (!state.media.videos || state.media.videos.length === 0) {
    container.innerHTML = '<div style="color:#888; font-size:12px;">No videos found in output folder. Render a lyric video in new-lyrics-2 first!</div>';
    return;
  }

  state.media.videos.forEach((v, idx) => {
    const item = document.createElement('label');
    item.className = 'bulk-media-item';
    item.innerHTML = `
      <input type="checkbox" name="bulk-media" value="${v.path}" ${idx < 3 ? 'checked' : ''}>
      <span>🎬 <b>${v.filename}</b> (${(v.size / (1024*1024)).toFixed(1)} MB)</span>
    `;
    container.appendChild(item);
  });
}

async function handleBulkSchedule() {
  const checkedBoxes = document.querySelectorAll('input[name="bulk-media"]:checked');
  const selectedPaths = Array.from(checkedBoxes).map(cb => cb.value);

  if (selectedPaths.length === 0) return alert('Select at least one video to schedule');

  const captionTemplate = document.getElementById('bulk-caption-template').value.trim();
  const firstComment = document.getElementById('bulk-first-comment').value.trim();
  const startDate = document.getElementById('bulk-start-date').value;
  const interval = parseInt(document.getElementById('bulk-interval').value) || 1;

  showToast(`⚡ Auto-distributing ${selectedPaths.length} videos across peak windows...`);

  try {
    const res = await fetch('/api/posts/bulk-schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_id: state.currentBrandId,
        media_paths: selectedPaths,
        caption_template: captionTemplate,
        first_comment: firstComment,
        target_platforms: ['instagram', 'facebook'],
        start_date: startDate,
        interval_days: interval,
        use_best_times: true
      })
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    bulkModal.style.display = 'none';
    showToast(`🚀 Successfully scheduled ${data.total_scheduled} posts across peak times!`);
    renderCalendar();
  } catch (e) {
    alert('Bulk schedule error: ' + e.message);
  }
}

// ==============================================================================
// 📄 Metricool & Custom CSV Bulk Importer Controller
// ==============================================================================
function openCsvImportModal() {
  const modal = document.getElementById('csv-import-modal');
  if (!modal) return;
  state.csvRawText = null;
  state.csvValidationData = null;
  showCsvUploadStep();
  modal.style.display = 'flex';
}

function closeCsvImportModal() {
  const modal = document.getElementById('csv-import-modal');
  if (modal) modal.style.display = 'none';
}

function showCsvUploadStep() {
  const uploadStep = document.getElementById('csv-upload-step');
  const previewStep = document.getElementById('csv-preview-step');
  if (uploadStep) {
    uploadStep.hidden = false;
    uploadStep.style.display = 'block';
  }
  if (previewStep) {
    previewStep.hidden = true;
    previewStep.style.display = 'none';
  }
  const backButton = document.getElementById('btn-csv-back');
  const importButton = document.getElementById('btn-csv-execute-import');
  if (backButton) backButton.hidden = true;
  if (importButton) {
    importButton.disabled = true;
    importButton.textContent = 'Import 0 posts';
  }
  const fileInput = document.getElementById('csv-file-input');
  if (fileInput) fileInput.value = '';
}

function showCsvPreviewStep() {
  const uploadStep = document.getElementById('csv-upload-step');
  const previewStep = document.getElementById('csv-preview-step');
  if (uploadStep) {
    uploadStep.hidden = true;
    uploadStep.style.display = 'none';
  }
  if (previewStep) {
    previewStep.hidden = false;
    previewStep.style.display = 'block';
  }
  const backButton = document.getElementById('btn-csv-back');
  if (backButton) backButton.hidden = false;
}

async function handleCsvFileSelect(file) {
  if (!file) return;
  const errorBox = document.getElementById('csv-upload-error');
  if (errorBox) {
    errorBox.hidden = true;
    errorBox.textContent = '';
  }
  if (!file.name.toLowerCase().endsWith('.csv')) {
    if (errorBox) {
      errorBox.textContent = 'Please choose a .csv file.';
      errorBox.hidden = false;
    }
    return;
  }
  const reader = new FileReader();
  reader.onload = async (e) => {
    state.csvRawText = e.target.result;
    await validateCurrentCsv();
  };
  reader.readAsText(file);
}

async function validateCurrentCsv() {
  if (!state.csvRawText) return;
  showToast('🔍 Parsing & verifying CSV posts...');
  const dateFormat = document.getElementById('csv-date-format')?.value || 'YYYY-MM-DD';
  const timeFormat = document.getElementById('csv-time-format')?.value || '24h';

  try {
    const res = await fetch('/api/posts/csv-validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        csv_text: state.csvRawText,
        date_format: dateFormat,
        time_format: timeFormat,
        brand_id: state.currentBrandId
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Validation failed');
    }

    const data = await res.json();
    state.csvValidationData = data;
    renderCsvValidationReport(data);
    showCsvPreviewStep();
  } catch (err) {
    const errorBox = document.getElementById('csv-upload-error');
    if (errorBox) {
      errorBox.textContent = 'CSV validation error: ' + err.message;
      errorBox.hidden = false;
    } else {
      alert('CSV Validation Error: ' + err.message);
    }
  }
}

function renderCsvValidationReport(data) {
  const alerts = document.getElementById('csv-alerts');
  const summary = document.getElementById('csv-preview-summary');
  const postsList = document.getElementById('csv-posts-list');
  const banner = data.banner_errors || {};
  if (alerts) {
    alerts.innerHTML = '';
    const alertItems = [];
    if (banner.some_posts_have_errors) {
      alertItems.push(['csv-alert-error', '!', 'Some posts have errors.', 'They will be imported as draft. If the post date is invalid, it will be scheduled today at current time.']);
    }
    if (banner.wrong_brand_names) {
      alertItems.push(['csv-alert-brand-error', '!', 'Posts with wrong brand names will not be imported.', '']);
    }
    if (banner.unidentified_urls) {
      alertItems.push(['csv-alert-warning', '!', 'Some URLs could not be identified.', 'Their preview will not be available, but will be published if the image or video meets the social network\'s requirements.']);
    }
    const alertIds = {
      'csv-alert-error': 'csv-alert-errors',
      'csv-alert-brand-error': 'csv-alert-brand-errors',
      'csv-alert-warning': 'csv-alert-url-warnings'
    };
    alerts.innerHTML = alertItems.map(([className, icon, title, detail]) => `
      <div id="${alertIds[className]}" class="csv-alert-box ${className}" role="alert">
        <span class="csv-alert-icon">${icon}</span>
        <div><strong>${title}</strong>${detail ? `<span>${detail}</span>` : ''}</div>
      </div>
    `).join('');
  }

  if (summary) {
    summary.textContent = `${data.total_rows || 0} posts found - ${data.can_import_count || 0} ready to import, ${data.warnings_count || 0} with warnings, ${data.errors_count || 0} with errors.`;
  }

  const btnImport = document.getElementById('btn-csv-execute-import');
  if (btnImport) {
    const count = data.can_import_count || 0;
    btnImport.textContent = `Import ${count} posts`;
    btnImport.disabled = count === 0;
  }

  if (postsList) {
    postsList.innerHTML = '';
    (data.posts || []).forEach((post) => {
      const item = document.createElement('div');
      const statusClass = post.status === 'valid' ? 'ok' : post.status;
      const mediaName = post.video_path ? post.video_path.split('\\').pop().split('/').pop() : (post.video_url ? 'Web video' : 'No media');
      const allMessages = [...(post.errors || []), ...(post.warnings || [])];
      const caption = post.caption || '(No caption)';
      const shortCaption = caption.length > 120 ? caption.slice(0, 120) + '...' : caption;
      const platforms = (post.platforms || []).map((platform) => `<span class="csv-post-media-tag">${escapeHtml(platform)}</span>`).join('');
      item.className = 'csv-post-row';
      item.innerHTML = `
        <span class="csv-post-status-icon ${statusClass}" title="${escapeHtml(post.status)}">${post.status === 'valid' ? '&#10003;' : '!'}</span>
        <div class="csv-post-meta">
          <strong>${escapeHtml(post.date_formatted || 'Today')}</strong>
          <span>${escapeHtml(post.time_formatted || '')}</span>
          <span>${escapeHtml(post.brand_name || 'Unknown brand')}</span>
        </div>
        <div class="csv-post-caption">
          <strong>Caption</strong>
          <span class="csv-caption-text ${caption.length > 120 ? 'is-collapsed' : ''}" data-full-caption="${escapeHtml(caption)}">${escapeHtml(shortCaption)}</span>
          ${caption.length > 120 ? '<button type="button" class="csv-caption-more">More</button>' : ''}
        </div>
        <div class="csv-post-platforms">${platforms || '<span class="csv-post-error-tag">No platforms</span>'}</div>
        <div>
          <span class="csv-post-media-tag">${escapeHtml(mediaName)}</span>
          ${allMessages.map((message) => `<span class="csv-post-error-tag">${escapeHtml(message)}</span>`).join('')}
        </div>
      `;
      const moreButton = item.querySelector('.csv-caption-more');
      if (moreButton) moreButton.addEventListener('click', () => {
        const captionNode = item.querySelector('.csv-caption-text');
        const expanded = captionNode.classList.toggle('is-collapsed') === false;
        captionNode.textContent = expanded ? caption : shortCaption;
        moreButton.textContent = expanded ? 'Less' : 'More';
      });
      postsList.appendChild(item);
    });
  }
  return;

  const bannerErrors = document.getElementById('csv-alert-errors');
  const bannerBrandErrors = document.getElementById('csv-alert-brand-errors');
  const bannerUrlWarnings = document.getElementById('csv-alert-url-warnings');

  if (bannerErrors) {
    bannerErrors.style.display = data.banner_errors?.some_posts_have_errors ? 'flex' : 'none';
  }
  if (bannerBrandErrors) {
    bannerBrandErrors.style.display = data.banner_errors?.wrong_brand_names ? 'flex' : 'none';
  }
  if (bannerUrlWarnings) {
    bannerUrlWarnings.style.display = data.banner_errors?.unidentified_urls ? 'flex' : 'none';
  }

  const legacyBtnImport = document.getElementById('btn-csv-execute-import');
  if (legacyBtnImport) {
    const count = data.can_import_count || 0;
    legacyBtnImport.textContent = `Import ${count} posts`;
    legacyBtnImport.disabled = count === 0;
    legacyBtnImport.style.opacity = count === 0 ? '0.5' : '1';
  }

  const listContainer = document.getElementById('csv-posts-list');
  if (!listContainer) return;
  listContainer.innerHTML = '';

  (data.posts || []).forEach(post => {
    const item = document.createElement('div');
    item.className = `csv-post-item ${post.status}`;

    const isError = post.status === 'error';
    const isWarning = post.status === 'warning';
    const statusIcon = (isError || isWarning)
      ? '<span class="csv-status-badge csv-badge-warning" title="Has warnings/errors">!</span>'
      : '<span class="csv-status-badge csv-badge-ok" title="Valid">✓</span>';

    const platformIcons = (post.platforms || []).map(p => {
      if (p === 'instagram') return '📸';
      if (p === 'facebook') return '📘';
      if (p === 'threads') return '🧵';
      if (p === 'youtube') return '📺';
      return '🌐';
    }).join(' ');

    const mediaIndicator = post.video_path
      ? `<span class="csv-media-pill">🎥 ${escapeHtml(post.video_path.split('\\').pop().split('/').pop())}</span>`
      : post.video_url
      ? `<span class="csv-media-pill">🔗 Web Video</span>`
      : `<span class="csv-media-pill csv-media-missing">⚠️ No media</span>`;

    const errorsList = [...(post.errors || []), ...(post.warnings || [])].map(msg => 
      `<div class="csv-row-error-msg">${escapeHtml(msg)}</div>`
    ).join('');

    item.innerHTML = `
      <div class="csv-post-left">
        ${statusIcon}
        <div class="csv-post-datetime">
          <div class="csv-dt-date">${escapeHtml(post.date_formatted)}</div>
          <div class="csv-dt-time">${escapeHtml(post.time_formatted)}</div>
        </div>
      </div>
      <div class="csv-post-right">
        <div class="csv-post-header-line">
          <span class="csv-brand-tag" style="color:${post.brand_color || '#8ACE00'};">● ${escapeHtml(post.brand_name)}</span>
          <span class="csv-plat-icons">${platformIcons}</span>
          ${mediaIndicator}
        </div>
        <div class="csv-post-caption-box">
          <div class="csv-post-caption-text">${escapeHtml(post.caption)}</div>
        </div>
        ${errorsList ? `<div class="csv-post-errors-box">${errorsList}</div>` : ''}
      </div>
    `;
    listContainer.appendChild(item);
  });
}

async function executeCsvImport() {
  if (!state.csvValidationData || !state.csvValidationData.posts) return;
  const validPosts = state.csvValidationData.posts.filter(p => p.can_import);
  if (validPosts.length === 0) {
    alert('No valid posts to import. Please fix errors and retry.');
    return;
  }

  showToast(`⏳ Importing ${validPosts.length} posts...`);
  try {
    const res = await fetch('/api/posts/csv-import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ posts: validPosts })
    });
    if (!res.ok) throw new Error(await res.text());
    const result = await res.json();
    closeCsvImportModal();
    showToast(`✅ Successfully imported ${result.total_imported} posts (${result.scheduled_count} scheduled, ${result.draft_count} drafts)!`);
    renderCalendar();
    if (state.activeTab === 'queue') loadQueue();
  } catch (err) {
    alert('Import failed: ' + err.message);
  }
}

async function handleTrackUrl() {
  const url = document.getElementById('track-url-input').value.trim();
  const platform = document.getElementById('track-platform-select').value;
  const title = document.getElementById('track-title-input').value.trim();

  if (!url) return alert('Please enter a URL');

  try {
    const res = await fetch('/api/analytics/track-link', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_id: state.currentBrandId || (state.brands[0] ? state.brands[0].id : 'main'),
        platform: platform,
        url: url,
        title: title || url
      })
    });
    if (!res.ok) throw new Error(await res.text());
    trackUrlModal.style.display = 'none';
    document.getElementById('track-url-input').value = '';
    document.getElementById('track-title-input').value = '';
    showToast('Link added to tracking! Fetching stats...');

    // Auto trigger refresh
    await fetch('/api/analytics/refresh-all', { method: 'POST' });
    loadAnalytics();
  } catch (e) {
    alert('Error saving tracked link: ' + e.message);
  }
}

// Media Loader
async function loadGeneratedMedia() {
  try {
    const res = await fetch('/api/media/generated');
    const media = await res.json();
    state.media = media;
    composerMediaSelect.innerHTML = '<option value="">(Select a generated video or carousel)</option>';
    if (media.videos) {
      media.videos.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.path;
        opt.textContent = `🎬 ${v.filename} (${(v.size / (1024*1024)).toFixed(1)} MB)`;
        composerMediaSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error('Error loading media:', err);
  }
}

// Calendar Rendering with Best Times Heatmap
async function renderCalendar() {
  const year = state.calendarDate.getFullYear();
  const month = state.calendarDate.getMonth();
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  calendarMonthTitle.textContent = `${monthNames[month]} ${year}`;
  calendarDaysGrid.innerHTML = '';

  let posts = [];
  try {
    const res = await fetch(`/api/posts?brand_id=${state.currentBrandId || ''}`);
    posts = await res.json();
    state.posts = posts;
  } catch (e) {
    console.warn('Could not fetch posts for calendar:', e);
  }

  // Update stat pills
  const schedCount = posts.filter(p => p.status === 'scheduled').length;
  const pubCount = posts.filter(p => p.status === 'published').length;
  document.getElementById('stat-scheduled-count').textContent = schedCount;
  document.getElementById('stat-published-count').textContent = pubCount;

  const firstDayIndex = new Date(year, month, 1).getDay() === 0 ? 6 : new Date(year, month, 1).getDay() - 1;
  const totalDays = new Date(year, month + 1, 0).getDate();
  const prevMonthTotalDays = new Date(year, month, 0).getDate();

  const today = new Date();
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;

  // Previous month trailing days
  for (let x = firstDayIndex; x > 0; x--) {
    const dayNum = prevMonthTotalDays - x + 1;
    const cell = createDayCell(dayNum, true);
    calendarDaysGrid.appendChild(cell);
  }

  // Current month days
  for (let i = 1; i <= totalDays; i++) {
    const isToday = isCurrentMonth && today.getDate() === i;
    const cell = createDayCell(i, false, isToday);

    const dayStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
    const dayOfWeek = new Date(year, month, i).getDay(); // 0 = Sun, 6 = Sat

    // Best Times Heatmap Shading
    if (state.showBestTimes) {
      if (dayOfWeek === 5 || dayOfWeek === 6) {
        cell.classList.add('heat-peak');
        const badge = document.createElement('span');
        badge.className = 'heat-badge-tag';
        badge.textContent = '🔥 97%';
        cell.querySelector('.day-header').appendChild(badge);
      } else if (dayOfWeek === 0 || dayOfWeek === 4) {
        cell.classList.add('heat-high');
        const badge = document.createElement('span');
        badge.className = 'heat-badge-tag';
        badge.textContent = '⚡ 92%';
        cell.querySelector('.day-header').appendChild(badge);
      }
    }

    // Filter posts for this day
    const daysPosts = posts.filter(p => p.scheduled_time.startsWith(dayStr));
    daysPosts.forEach(p => {
      const chip = document.createElement('div');
      chip.className = 'post-chip';
      const timeStr = p.scheduled_time.split('T')[1] ? p.scheduled_time.split('T')[1].slice(0, 5) : '';
      const dotColor = p.status === 'published' ? '#22c55e' : p.status === 'failed' ? '#ef4444' : '#e7ff56';

      chip.innerHTML = `
        <span class="chip-status-dot" style="background:${dotColor};"></span>
        <span class="chip-time">${timeStr}</span>
        <span class="chip-caption">${escapeHtml(p.caption || 'Media Post')}</span>
      `;
      chip.addEventListener('click', (e) => {
        e.stopPropagation();
        alert(`Post: ${p.caption}\nStatus: ${p.status}\nPlatforms: ${p.target_platforms.join(', ')}\nScheduled: ${p.scheduled_time}`);
      });
      cell.appendChild(chip);
    });

    cell.addEventListener('click', () => {
      openComposer(dayStr);
    });

    calendarDaysGrid.appendChild(cell);
  }

  // Next month trailing days
  const totalCells = firstDayIndex + totalDays;
  const remaining = (7 - (totalCells % 7)) % 7;
  for (let j = 1; j <= remaining; j++) {
    const cell = createDayCell(j, true);
    calendarDaysGrid.appendChild(cell);
  }
}

function createDayCell(dayNum, isOtherMonth, isToday = false) {
  const cell = document.createElement('div');
  cell.className = `cal-day-cell ${isOtherMonth ? 'other-month' : ''}`;
  const header = document.createElement('div');
  header.className = 'day-header';
  const numSpan = document.createElement('span');
  numSpan.className = `day-number ${isToday ? 'today' : ''}`;
  numSpan.textContent = dayNum;
  header.appendChild(numSpan);
  cell.appendChild(header);
  return cell;
}

// Instagram Feed Preview
// Instagram Feed Preview - Real Time
async function loadFeedPreview() {
  const gridContainer = document.getElementById('feed-tiles-grid');
  gridContainer.innerHTML = '<div style="color:#888; grid-column:span 3; padding:20px; text-align:center;">Loading real-time feed &amp; live profile...</div>';

  try {
    // 1. Fetch real-time profile data & published media from social-hub
    const profileRes = await fetch(`/api/feed/profile?brand_id=${state.currentBrandId || ''}`);
    const feedData = await profileRes.json();
    const profile = feedData.profile || {};
    const liveMedias = feedData.live_medias || [];

    // Update Profile Header elements
    const handleEl = document.getElementById('feed-profile-handle');
    const badgeEl = document.getElementById('feed-brand-badge');
    const postsEl = document.getElementById('feed-val-posts');
    const followersEl = document.getElementById('feed-val-followers');
    const followingEl = document.getElementById('feed-val-following');
    const bioEl = document.getElementById('feed-profile-bio');
    const statusPill = document.getElementById('feed-live-status-pill');
    const verifiedBadge = document.getElementById('feed-verified-badge');
    const avatarImg = document.getElementById('feed-avatar-img');
    const avatarInitials = document.getElementById('feed-avatar-initials');

    if (handleEl) handleEl.textContent = `@${profile.handle || 'account'}`;
    if (badgeEl) badgeEl.textContent = profile.brand_name || 'Brand';
    if (postsEl) postsEl.textContent = (profile.media_count || 0).toLocaleString();
    if (followersEl) followersEl.textContent = (profile.follower_count || 0).toLocaleString();
    if (followingEl) followingEl.textContent = (profile.following_count || 0).toLocaleString();
    if (bioEl) bioEl.textContent = profile.biography || (profile.is_authenticated ? 'No bio description set on Instagram.' : 'Session offline. Connect account in .env to sync live bio.');

    if (verifiedBadge) {
      verifiedBadge.style.display = profile.is_verified ? 'inline-block' : 'none';
    }

    if (statusPill) {
      if (profile.is_authenticated) {
        statusPill.textContent = '● Live Authenticated (Port 8001)';
        statusPill.style.background = 'rgba(34, 197, 94, 0.2)';
        statusPill.style.color = '#22c55e';
      } else if (profile.source === 'public_scrape') {
        statusPill.textContent = '● Public Sync (Live Stats)';
        statusPill.style.background = 'rgba(234, 179, 8, 0.2)';
        statusPill.style.color = '#eab308';
      } else {
        statusPill.textContent = '● Session Offline';
        statusPill.style.background = 'rgba(239, 68, 68, 0.2)';
        statusPill.style.color = '#ef4444';
      }
    }

    // Avatar
    if (avatarImg && avatarInitials) {
      if (profile.profile_pic_url) {
        avatarImg.src = profile.profile_pic_url;
        avatarImg.style.display = 'block';
        avatarInitials.style.display = 'none';
      } else {
        avatarImg.style.display = 'none';
        avatarInitials.style.display = 'flex';
        const brandName = profile.brand_name || 'Brand';
        avatarInitials.textContent = brandName.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'IG';
      }
    }

    // 2. Fetch scheduled posts from Social Hub
    const postsRes = await fetch(`/api/posts?brand_id=${state.currentBrandId || ''}`);
    const posts = await postsRes.json();

    gridContainer.innerHTML = '';
    const items = [];

    // Prepend live published Instagram posts if available
    if (liveMedias && liveMedias.length > 0) {
      liveMedias.forEach(m => {
        items.push({
          id: `live-${m.id}`,
          caption: m.caption,
          status: 'published_live',
          thumbnail_url: m.thumbnail_url,
          video_url: m.video_url,
          scheduled_time: m.taken_at,
          likes: m.like_count,
          views: m.view_count
        });
      });
    }

    // Add scheduled posts
    posts.forEach(p => items.push(p));

    // Fallback to local generated media if completely empty
    if (items.length === 0 && state.media.videos && state.media.videos.length > 0) {
      state.media.videos.slice(0, 6).forEach((v, idx) => {
        items.push({
          id: `media-${idx}`,
          caption: v.filename.replace('.mp4', ''),
          status: 'ready',
          preview_url: v.preview_url,
          scheduled_time: new Date().toISOString()
        });
      });
    }

    if (items.length === 0) {
      gridContainer.innerHTML = '<div style="grid-column:span 3; text-align:center; padding:40px; color:#888;">No reels or posts to display. Schedule a video above to see your feed preview!</div>';
      return;
    }

    items.forEach(item => {
      const tile = document.createElement('div');
      tile.className = 'feed-tile';

      let videoSrc = '';
      let thumbSrc = item.thumbnail_url || '';
      if (item.preview_url) {
        videoSrc = item.preview_url;
      } else if (item.video_url) {
        videoSrc = item.video_url;
      } else if (item.media_paths && item.media_paths.length > 0) {
        const matching = state.media.videos.find(v => v.path === item.media_paths[0]);
        if (matching) {
          videoSrc = matching.preview_url;
          if (!thumbSrc && matching.thumbnail_url) thumbSrc = matching.thumbnail_url;
        }
      }

      const isScheduled = item.status === 'scheduled';
      const isLiveIg = item.status === 'published_live';
      const badgeHtml = isLiveIg
        ? `<span class="feed-tile-scheduled-badge" style="background:#22c55e;">✓ LIVE ON IG</span>`
        : isScheduled
        ? `<span class="feed-tile-scheduled-badge">🗓️ SCHEDULED</span>`
        : item.status === 'published'
        ? `<span class="feed-tile-scheduled-badge" style="background:#22c55e;">✓ PUBLISHED</span>`
        : '';

      const statsOverlay = isLiveIg
        ? `<div style="font-size:10px; color:#e7ff56; margin-top:2px;">❤️ ${(item.likes || 0).toLocaleString()} • 👁️ ${(item.views || 0).toLocaleString()}</div>`
        : '';

      tile.innerHTML = `
        ${badgeHtml}
        ${thumbSrc 
          ? `<img src="${thumbSrc}" loading="lazy" alt="Preview" style="width:100%;height:100%;object-fit:cover;">` 
          : videoSrc 
          ? `<video src="${videoSrc}" muted loop preload="none" onmouseover="this.play()" onmouseout="this.pause()"></video>` 
          : `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:24px;">🎬</div>`}
        <div class="feed-tile-overlay">
          <span style="font-weight:800;">${escapeHtml(item.caption || 'Video Reel')}</span>
          <span style="font-size:10px; color:#e7ff56;">${item.scheduled_time ? item.scheduled_time.replace('T', ' ').slice(0, 16) : ''}</span>
          ${statsOverlay}
        </div>
      `;
      gridContainer.appendChild(tile);
    });
  } catch (e) {
    console.error('Error loading feed preview:', e);
    gridContainer.innerHTML = '<div style="color:#ef4444; grid-column:span 3; padding:20px; text-align:center;">Failed to load real-time feed preview: ' + escapeHtml(e.message) + '</div>';
  }
}

// Composer Handlers
function openComposer(dateStr = null) {
  composerModal.style.display = 'flex';
  const now = new Date();
  document.getElementById('composer-date').value = dateStr || now.toISOString().slice(0, 10);
  document.getElementById('composer-time').value = '19:30';
}

function closeComposer() {
  composerModal.style.display = 'none';
}

async function handleSubmitPost(publishNow = false) {
  if (!state.currentBrandId) return alert('Please select a brand');
  const mediaPath = composerMediaSelect.value;
  const caption = composerCaption.value.trim();
  const firstComment = composerFirstComment ? composerFirstComment.value.trim() : null;
  const dateVal = document.getElementById('composer-date').value;
  const timeVal = document.getElementById('composer-time').value;
  const addToEvergreen = document.getElementById('chk-add-evergreen') ? document.getElementById('chk-add-evergreen').checked : false;

  if (!caption && !mediaPath) return alert('Please provide a caption or media.');

  const platforms = [];
  if (document.getElementById('chk-platform-ig').checked) platforms.push('instagram');
  if (document.getElementById('chk-platform-fb').checked) platforms.push('facebook');
  if (document.getElementById('chk-platform-threads').checked) platforms.push('threads');
  if (document.getElementById('chk-platform-yt').checked) platforms.push('youtube');

  if (platforms.length === 0) return alert('Select at least one platform');

  const scheduledTime = publishNow ? new Date().toISOString() : `${dateVal}T${timeVal}:00`;

  const payload = {
    brand_id: state.currentBrandId,
    target_platforms: platforms,
    post_type: 'reel',
    media_paths: mediaPath ? [mediaPath] : [],
    caption: caption,
    first_comment: firstComment,
    scheduled_time: scheduledTime,
    share_to_facebook: platforms.includes('facebook'),
    share_to_threads: platforms.includes('threads')
  };

  try {
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    const createdPost = await res.json();

    // If requested, save to evergreen library as well
    if (addToEvergreen) {
      await fetch('/api/evergreen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_id: state.currentBrandId,
          caption: caption,
          media_paths: mediaPath ? [mediaPath] : [],
          target_platforms: platforms,
          max_repeats: 3
        })
      });
    }

    if (publishNow) {
      showToast('⚡ Dispatching post now...');
      await fetch(`/api/posts/${createdPost.id}/publish-now`, { method: 'POST' });
    }

    closeComposer();
    showToast(publishNow ? 'Post published!' : 'Post scheduled to calendar!');
    renderCalendar();
    if (state.activeTab === 'feed') loadFeedPreview();
    if (state.activeTab === 'evergreen') loadEvergreen();
  } catch (err) {
    alert('Scheduling error: ' + err.message);
  }
}

// Queue View
async function loadQueue() {
  const queueList = document.getElementById('queue-list');
  queueList.innerHTML = '<div style="color:#888;">Loading queue...</div>';
  try {
    const res = await fetch(`/api/posts?brand_id=${state.currentBrandId || ''}`);
    const posts = await res.json();
    if (posts.length === 0) {
      queueList.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-state-icon">⏳</div>
          <div class="empty-state-title">No Posts in Queue</div>
          <div class="empty-state-desc">Your publishing pipeline is currently clear. Use Bulk Batch Scheduler to automatically populate optimal slots or create a post now.</div>
          <button type="button" class="btn-primary" onclick="openComposer()">
            <span>✍️ Schedule New Post</span>
          </button>
        </div>
      `;
      return;
    }
    queueList.innerHTML = '';
    posts.forEach(p => {
      const card = document.createElement('div');
      card.className = 'queue-card';
      const plats = p.target_platforms.join(', ');
      const commentHtml = p.first_comment ? `<div style="font-size:11px; color:#c9e847; margin-top:3px;">💬 First comment: ${escapeHtml(p.first_comment)}</div>` : '';
      card.innerHTML = `
        <div>
          <div style="font-weight: 800; font-size: 15px; margin-bottom: 4px;">${escapeHtml(p.caption || 'Media Post')}</div>
          <div style="font-size: 12px; color: #8b949e;">Platforms: <b>${plats}</b> | Time: <b>${p.scheduled_time.replace('T', ' ')}</b></div>
          ${commentHtml}
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
          <span style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; background: ${p.status === 'published' ? '#22c55e' : p.status === 'failed' ? '#ef4444' : '#ffcc00'}; color: #000;">${p.status.toUpperCase()}</span>
          <button class="btn-subtle" onclick="deletePostItem('${p.id}')">Delete</button>
        </div>
      `;
      queueList.appendChild(card);
    });
  } catch (e) {
    queueList.innerHTML = '<div style="color:#ef4444;">Could not load queue.</div>';
  }
}

window.deletePostItem = async function(id) {
  if (!confirm('Delete this scheduled post?')) return;
  await fetch(`/api/posts/${id}`, { method: 'DELETE' });
  loadQueue();
  renderCalendar();
};

// Analytics View with Engagement Rate & Leaderboard
async function loadAnalytics() {
  try {
    const res = await fetch(`/api/analytics/summary?brand_id=${state.currentBrandId || ''}`);
    const data = await res.json();
    document.getElementById('kpi-total-views').textContent = (data.total_views || 0).toLocaleString();
    document.getElementById('kpi-total-likes').textContent = (data.total_likes || 0).toLocaleString();
    document.getElementById('kpi-total-comments').textContent = (data.total_comments || 0).toLocaleString();

    const rateEl = document.getElementById('kpi-engagement-rate');
    if (rateEl) {
      rateEl.textContent = `${data.engagement_rate || 0.0}%`;
    }

    const plats = data.platform_breakdown || {};
    document.getElementById('plat-views-yt').textContent = `${(plats.youtube || 0).toLocaleString()} views`;
    document.getElementById('plat-views-ig').textContent = `${(plats.instagram || 0).toLocaleString()} views`;
    document.getElementById('plat-views-threads').textContent = `${(plats.threads || 0).toLocaleString()} views`;

    // Leaderboard Table
    const tableBody = document.getElementById('leaderboard-table-body');
    if (tableBody) {
      const topPosts = data.top_posts || [];
      if (topPosts.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="empty-table-msg">No tracked links recorded yet. Click "Track New Public URL" above to track a YouTube Short or Instagram Reel!</td></tr>';
      } else {
        tableBody.innerHTML = '';
        topPosts.forEach(tp => {
          const row = document.createElement('tr');
          const platBadge = tp.platform === 'youtube' ? '📺 YouTube' : tp.platform === 'instagram' ? '📸 Instagram' : '🧵 Threads';
          row.innerHTML = `
            <td><strong>${escapeHtml(tp.title || 'Untitled Post')}</strong></td>
            <td><span class="badge-brand-pill">${platBadge}</span></td>
            <td><b>${(tp.views || 0).toLocaleString()}</b></td>
            <td>${(tp.likes || 0).toLocaleString()}</td>
            <td>${(tp.comments || 0).toLocaleString()}</td>
            <td><b style="color:var(--color-surface-raised);">${tp.engagement_rate || 0.0}%</b></td>
            <td><a href="${tp.url}" target="_blank" class="table-link-btn">View Post ↗</a></td>
          `;
          tableBody.appendChild(row);
        });
      }
    }
  } catch (e) {
    console.warn('Could not load analytics summary:', e);
  }
}

function escapeHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ==============================================================================
// 🔐 Connected & Verified Accounts Dashboard Manager
// ==============================================================================
async function loadAccounts(force = false) {
  const container = document.getElementById('verified-accounts-grid');
  if (!container) return;
  if (force || !state.accountsData) {
    container.innerHTML = '<div style="color:#888; grid-column:span 3; padding:40px; text-align:center;">🔍 Checking live verification status across all services...</div>';
  }

  try {
    const res = await fetch('/api/accounts/status');
    const data = await res.json();
    state.accountsData = data;

    // Update Summary Header Pills
    const sumBrands = document.getElementById('acc-sum-brands');
    const sumVerified = document.getElementById('acc-sum-verified');
    const sumPending = document.getElementById('acc-sum-pending');
    const pendingAccounts = (data.all_accounts || []).filter(a =>
      a.status !== 'disabled' && (!a.is_authenticated || a.status !== 'verified')
    );
    if (sumBrands) sumBrands.textContent = data.total_brands || 0;
    if (sumVerified) sumVerified.textContent = data.total_verified || 0;
    if (sumPending) sumPending.textContent = pendingAccounts.length;

    renderAccountsGrid();

    // If any service was still warming up (status === 'offline') on initial server startup, auto-retry once
    const hasOffline = (data.all_accounts || []).some(a => a.status === 'offline');
    if (hasOffline && !window._hasAutoRetriedAccounts) {
      window._hasAutoRetriedAccounts = true;
      setTimeout(() => {
        loadAccounts(true);
      }, 3500);
    }
  } catch (err) {
    console.error('Error loading accounts status:', err);
    container.innerHTML = '<div style="color:#ef4444; grid-column:span 3; padding:30px; text-align:center;">Failed to connect to accounts status service: ' + escapeHtml(err.message) + '</div>';
    if (!window._hasAutoRetriedAccounts) {
      window._hasAutoRetriedAccounts = true;
      setTimeout(() => {
        loadAccounts(true);
      }, 3500);
    }
  }
}

function renderAccountsGrid() {
  const verifiedContainer = document.getElementById('verified-accounts-grid');
  const disconnectedSection = document.getElementById('disconnected-accounts-section');
  const disconnectedGrid = document.getElementById('disconnected-accounts-grid');
  if (!verifiedContainer || !state.accountsData) return;

  const allAccounts = state.accountsData.all_accounts || [];
  const platformFilter = state.accountsPlatformFilter || 'all';

  // Filter accounts
  let filteredVerified = allAccounts.filter(a => a.is_authenticated && a.status === 'verified');
  let filteredDisconnected = allAccounts.filter(a => a.status !== 'disabled' && (!a.is_authenticated || a.status !== 'verified'));

  if (platformFilter !== 'all') {
    filteredVerified = filteredVerified.filter(a => a.platform === platformFilter);
    filteredDisconnected = filteredDisconnected.filter(a => a.platform === platformFilter);
  }

  // Render Verified Accounts
  if (filteredVerified.length === 0) {
    verifiedContainer.innerHTML = `
      <div class="empty-state-card" style="grid-column: span 3; text-align: center; padding: 40px;">
        <div style="font-size: 36px; margin-bottom: 12px;">🔒</div>
        <div style="font-size: 16px; font-weight: 700; color: #fff;">No verified accounts found matching filters</div>
        <div style="font-size: 13px; color: #888; max-width: 420px; margin: 8px auto;">
          Ensure credentials and session IDs are populated in your <code>.env</code> file, then click "Sync from .env" above.
        </div>
      </div>
    `;
  } else {
    verifiedContainer.innerHTML = '';
    filteredVerified.forEach(acc => {
      const card = createAccountCard(acc, true);
      verifiedContainer.appendChild(card);
    });
  }

  // Handle Disconnected Section
  if (!state.accountsVerifiedOnly) {
    if (disconnectedSection) disconnectedSection.style.display = 'block';
    if (disconnectedGrid) {
      disconnectedGrid.innerHTML = '';
      if (filteredDisconnected.length === 0) {
        disconnectedGrid.innerHTML = '<div style="color:#22c55e; padding:15px; font-size:13px;">✅ All accounts are verified! No offline sessions detected.</div>';
      } else {
        filteredDisconnected.forEach(acc => {
          const card = createAccountCard(acc, false);
          disconnectedGrid.appendChild(card);
        });
      }
    }
  } else {
    if (disconnectedSection) disconnectedSection.style.display = 'none';
  }
}

function createAccountCard(acc, isVerified) {
  const card = document.createElement('div');
  card.className = `account-hub-card ${isVerified ? 'verified-card' : 'unverified-card'}`;
  card.style.borderLeftColor = acc.brand_color || '#8ACE00';

  const platIcon = acc.platform === 'instagram' ? '📸' : acc.platform === 'threads' ? '🧵' : acc.platform === 'youtube' ? '📺' : '🌐';
  const platLabel = acc.platform.toUpperCase();

  const statusBadge = isVerified
    ? `<span class="badge-acc-status live-status"><span class="pulse-dot"></span>✓ Verified Logged In</span>`
    : `<span class="badge-acc-status dead-status">⚠️ ${escapeHtml(acc.status_label || 'Offline')}</span>`;

  const avatarContent = acc.avatar_url
    ? `<img src="${acc.avatar_url}" alt="${acc.handle}" class="acc-avatar-img">`
    : `<div class="acc-avatar-initials" style="background:${acc.brand_color || '#333'};">${(acc.brand_name || 'B').slice(0, 2).toUpperCase()}</div>`;

  const metricsRow = isVerified
    ? `
      <div class="acc-metrics-row">
        <div><span class="acc-m-val">${(acc.followers || 0).toLocaleString()}</span><span class="acc-m-lbl">Followers</span></div>
        <div><span class="acc-m-val">${(acc.following || 0).toLocaleString()}</span><span class="acc-m-lbl">Following</span></div>
        <div><span class="acc-m-val">${(acc.posts_count || 0).toLocaleString()}</span><span class="acc-m-lbl">Posts</span></div>
      </div>
    `
    : `
      <div class="acc-error-box">
        <b>Notice:</b> ${escapeHtml(acc.error_details || 'Session requires updating in .env (or login challenge pending).')}
      </div>
    `;

  const userIdentifier = acc.user_id 
    ? `<span class="acc-uid-tag">ID: ${escapeHtml(acc.user_id)}</span>` 
    : '';

  card.innerHTML = `
    <div class="acc-card-header">
      <div class="acc-card-brand-pill" style="color:${acc.brand_color || '#8ACE00'};">
        <span class="acc-brand-dot" style="background:${acc.brand_color || '#8ACE00'};"></span>
        ${escapeHtml(acc.brand_name)}
      </div>
      <div class="acc-plat-tag">${platIcon} ${platLabel}</div>
    </div>

    <div class="acc-card-body">
      <div class="acc-avatar-wrap">
        ${avatarContent}
      </div>
      <div class="acc-user-info">
        <div class="acc-handle-row">
          <span class="acc-handle">@${escapeHtml(acc.handle)}</span>
          ${isVerified ? '<span class="verified-badge-mini" title="Verified Session">✓</span>' : ''}
        </div>
        <div class="acc-display-name">${escapeHtml(acc.display_name || acc.handle)}</div>
        <div class="acc-meta-tags">
          ${statusBadge}
          ${userIdentifier}
        </div>
      </div>
    </div>

    ${metricsRow}

    <div class="acc-card-footer">
      <button type="button" class="btn-subtle btn-ping" onclick="pingAccountSession('${acc.platform}', '${acc.handle}')">
        ⚡ Ping Session
      </button>
      ${acc.platform === 'instagram' ? `
        <button type="button" class="btn-subtle" onclick="launchSessionHarvester('${acc.handle}')" title="Opens isolated browser window to log in once and auto-sync cookies">
          🔑 Auto-Login / Refresh
        </button>
      ` : ''}
      ${isVerified && acc.platform === 'instagram' ? `
        <button type="button" class="btn-subtle" onclick="switchToFeedTab('${acc.brand_id}')">
          📱 View Live Feed
        </button>
      ` : ''}
    </div>
  `;

  return card;
}

window.launchSessionHarvester = async function(handle) {
  showToast(`🚀 Launching isolated browser for @${handle}...`);
  try {
    const res = await fetch(`/api/accounts/${encodeURIComponent(handle)}/harvest-session`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(`🔑 Browser window opened! Log in once to auto-sync cookies.`);
    } else {
      showToast(`⚠️ Could not launch browser: ${data.detail || 'Error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Request failed: ${err.message}`);
  }
};

window.pingAccountSession = async function(platform, handle) {
  showToast(`⚡ Pinging ${platform.toUpperCase()} session for @${handle}...`);
  try {
    const url = platform === 'instagram' 
      ? `http://127.0.0.1:8001/accounts/${handle}/status`
      : `http://127.0.0.1:8002/accounts/${handle}/status`;
    const start = performance.now();
    const res = await fetch(url);
    const duration = Math.round(performance.now() - start);
    const data = await res.json();
    if (data.is_authenticated) {
      showToast(`🟢 Active & Verified! (${duration}ms ping, User ID: ${data.user_id || 'Active'})`);
    } else {
      showToast(`🔴 Offline / Expired! (${duration}ms, Session invalid)`);
    }
  } catch (err) {
    showToast(`⚠️ Ping error: ${err.message}`);
  }
};

window.switchToFeedTab = function(brandId) {
  if (brandId && brandSelect) {
    brandSelect.value = brandId;
    state.currentBrandId = brandId;
    updateBrandDot();
  }
  const feedBtn = document.querySelector('.tab-btn[data-tab="feed"]');
  if (feedBtn) feedBtn.click();
};

// ==============================================================================
// 📁 BRAND FOLDERS & 1-CLICK AUTO-PUBLISHER FUNCTIONS
// ==============================================================================

async function loadFolderQueues() {
  const container = document.getElementById('brand-folders-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/folder-queue/status');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.folderStatus = data;
    renderFolderQueueView(data);
  } catch (err) {
    console.error('Error loading folder queues:', err);
    container.innerHTML = `
      <div class="empty-state-card" style="grid-column: 1 / -1; padding: 30px; text-align: center;">
        <p style="color: #f87171; font-weight: 600;">⚠️ Could not load brand media queues: ${err.message}</p>
        <button class="btn-secondary" onclick="loadFolderQueues()" style="margin-top: 10px;">🔄 Try Again</button>
      </div>
    `;
  }
}

function renderFolderQueueView(folderData) {
  const container = document.getElementById('brand-folders-grid');
  if (!container) return;

  // Update Hero KPIs
  let totalBrands = folderData.length;
  let totalQueued = 0;
  let totalPosted = 0;

  folderData.forEach(b => {
    totalQueued += (b.pending_count || 0);
    totalPosted += (b.posted_count || 0);
  });

  const elBrandsCount = document.getElementById('stat-folder-brands-count');
  const elQueuedCount = document.getElementById('stat-folder-queue-total');
  const elPostedCount = document.getElementById('stat-folder-posted-total');
  if (elBrandsCount) elBrandsCount.textContent = totalBrands;
  if (elQueuedCount) elQueuedCount.textContent = totalQueued;
  if (elPostedCount) elPostedCount.textContent = totalPosted;

  if (folderData.length === 0) {
    container.innerHTML = `
      <div class="empty-state-card" style="grid-column: 1 / -1; padding: 40px; text-align: center;">
        <div style="font-size: 36px; margin-bottom: 12px;">📁</div>
        <h3 style="font-size: 16px; color: var(--color-text-primary); margin-bottom: 6px;">No Brand Folders Configured</h3>
        <p style="color: var(--color-text-secondary); font-size: 13px;">Add brand profiles in .env or create a brand to start auto-publishing.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = folderData.map(b => renderBrandFolderCard(b)).join('');
}

function renderBrandFolderCard(brand) {
  const hasItems = brand.pending_count > 0;
  const next = brand.next_item;

  const platformBadges = (brand.active_platforms || []).map(p => {
    let icon = '🌐';
    if (p === 'instagram') icon = '📸 Instagram';
    else if (p === 'facebook') icon = '📘 Facebook';
    else if (p === 'threads') icon = '🧵 Threads';
    else if (p === 'youtube') icon = '▶️ YouTube';
    return `<span class="platform-chip-mini">${icon}</span>`;
  }).join('');

  let previewHtml = '';
  if (hasItems && next) {
    const thumbHtml = next.thumbnail_url
      ? `<img src="${next.thumbnail_url}" alt="Thumbnail" class="next-thumb-img" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'next-thumb-placeholder\\'>${next.is_video ? '🎬' : '🖼️'}</div>'">`
      : `<div class="next-thumb-placeholder">${next.is_video ? '🎬' : '🖼️'}</div>`;

    previewHtml = `
      <div class="next-item-box">
        <div class="next-thumb-wrapper">
          ${thumbHtml}
          ${next.is_video ? '<span class="video-tag-pill">VIDEO</span>' : '<span class="video-tag-pill">PHOTO</span>'}
        </div>
        <div class="next-details">
          <div>
            <div class="next-label">Next in line (FIFO)</div>
            <div class="next-filename" title="${next.file_name}">${next.title || next.file_name}</div>
            <div class="next-caption-preview" title="${escapeHtml(next.full_caption || '')}">${escapeHtml(next.caption_preview || '')}</div>
          </div>
          <div class="next-meta-row">
            <span>💾 ${next.file_size_mb} MB</span>
            ${next.formatted_timestamp ? `<span>⏱️ ${next.formatted_timestamp}</span>` : ''}
            ${next.music_query ? `<span>🎵 ${escapeHtml(next.music_query)}</span>` : ''}
          </div>
        </div>
      </div>
    `;
  } else {
    previewHtml = `
      <div class="empty-queue-box">
        <span class="empty-queue-icon">✨</span>
        <div class="empty-queue-title">Queue is empty</div>
        <div class="empty-queue-desc">Drop video or image files into this brand's folder to queue them up.</div>
      </div>
    `;
  }

  // Upcoming items thumbnails carousel (if > 1 item)
  let upcomingHtml = '';
  if (brand.upcoming_items && brand.upcoming_items.length > 1) {
    const items = brand.upcoming_items.slice(1, 6).map(it => {
      const itThumb = it.thumbnail_url 
        ? `<img src="${it.thumbnail_url}" alt="Upcoming" class="upcoming-thumb-img">`
        : `<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 16px;">${it.is_video ? '🎬' : '🖼️'}</div>`;
      return `
        <div class="upcoming-thumb-box" title="${it.file_name} (${it.file_size_mb} MB)">
          ${itThumb}
        </div>
      `;
    }).join('');

    upcomingHtml = `
      <div style="margin-top: -6px;">
        <div style="font-size: 10.5px; font-weight: 700; color: var(--color-text-tertiary); margin-bottom: 6px; text-transform: uppercase;">Next in Queue (${brand.pending_count - 1} more):</div>
        <div class="upcoming-strip">${items}</div>
      </div>
    `;
  }

  return `
    <div class="brand-folder-card" data-brand-id="${brand.brand_id}">
      <div class="brand-card-header">
        <div class="brand-info-left">
          <span class="brand-color-badge-lg" style="background: ${brand.brand_color}; color: ${brand.brand_color};"></span>
          <div>
            <div class="brand-card-name">${escapeHtml(brand.brand_name)}</div>
            <div class="platform-chips-row">${platformBadges || '<span class="platform-chip-mini">No platforms</span>'}</div>
          </div>
        </div>
        <span class="queue-count-badge ${hasItems ? 'has-items' : 'is-empty'}">
          ${hasItems ? `⏳ ${brand.pending_count} Ready` : '0 Queued'}
        </span>
      </div>

      <div class="folder-path-strip">
        <span class="folder-path-text" title="${escapeHtml(brand.folder_path)}">${escapeHtml(brand.folder_path)}</span>
        <button type="button" class="btn-icon-copy" onclick="copyFolderPath('${escapeHtml(brand.folder_path).replace(/\\/g, '\\\\')}')" title="Copy Folder Path">📋</button>
      </div>

      ${previewHtml}
      ${upcomingHtml}

      <div class="brand-card-actions">
        <button type="button" class="btn-brand-post-now" 
          onclick="triggerPublishBrand('${brand.brand_id}')" 
          ${!hasItems ? 'disabled title="Folder is empty"' : 'title="Publish next media across all platforms for this brand"'}>
          <span>⚡</span>
          <span>Post Next Item</span>
        </button>
        <button type="button" class="btn-brand-open-folder" onclick="openBrandFolder('${brand.brand_id}')" title="Open folder in Windows Explorer">
          <span>📂</span>
          <span>Open Folder</span>
        </button>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

async function openBrandFolder(brandId) {
  try {
    showToast('📂 Opening brand media folder in Explorer...');
    const res = await fetch(`/api/folder-queue/open-folder/${brandId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('✅ Folder opened in File Explorer');
    } else {
      showToast(`⚠️ Could not open folder: ${data.detail || 'Error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Error: ${err.message}`);
  }
}

async function openAllFolders() {
  try {
    showToast('📂 Opening media_queue directory in Explorer...');
    const res = await fetch('/api/folder-queue/open-all-folders', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('✅ media_queue folder opened');
    } else {
      showToast(`⚠️ Could not open directory`);
    }
  } catch (err) {
    showToast(`⚠️ Error: ${err.message}`);
  }
}

function copyFolderPath(path) {
  navigator.clipboard.writeText(path).then(() => {
    showToast(`📋 Copied folder path: ${path}`);
  }).catch(() => {
    showToast(`Path: ${path}`);
  });
}

// ==============================================================================
// 🚀 MASTER 1-CLICK BROADCAST CONTROLLER
// ==============================================================================

const broadcastModal = document.getElementById('broadcast-modal');
const broadcastTitle = document.getElementById('broadcast-modal-title');
const broadcastMsg = document.getElementById('broadcast-status-msg');
const broadcastSpinner = document.getElementById('broadcast-spinner');
const broadcastBrandsList = document.getElementById('broadcast-brands-list');
const broadcastLog = document.getElementById('broadcast-log-output');
const btnCloseBroadcastModal = document.getElementById('btn-close-broadcast');
const btnDoneBroadcastModal = document.getElementById('btn-done-broadcast');

function openBroadcastModal(titleText) {
  if (!broadcastModal) return;
  broadcastModal.style.display = 'flex';
  if (broadcastTitle) broadcastTitle.textContent = titleText || '1-Click Multi-Brand Publishing';
  if (broadcastSpinner) broadcastSpinner.style.display = 'block';
  if (broadcastMsg) broadcastMsg.textContent = 'Contacting publishing microservices...';
  if (broadcastBrandsList) broadcastBrandsList.innerHTML = '';
  if (broadcastLog) broadcastLog.textContent = `[${new Date().toLocaleTimeString()}] Pipeline started.\n`;
  if (btnCloseBroadcastModal) btnCloseBroadcastModal.disabled = true;
  if (btnDoneBroadcastModal) btnDoneBroadcastModal.style.display = 'none';
}

function closeBroadcastModal() {
  if (broadcastModal) broadcastModal.style.display = 'none';
  loadFolderQueues();
  renderCalendar();
}

function appendBroadcastLog(line) {
  if (!broadcastLog) return;
  broadcastLog.textContent += `[${new Date().toLocaleTimeString()}] ${line}\n`;
  broadcastLog.scrollTop = broadcastLog.scrollHeight;
}

async function triggerPublishAllBrands() {
  openBroadcastModal('🚀 Master Multi-Brand Broadcast in Progress');
  appendBroadcastLog('Scanning brand folders for pending media...');

  // Initialize placeholder brand rows in modal
  if (state.folderStatus && state.folderStatus.length > 0) {
    broadcastBrandsList.innerHTML = state.folderStatus.map(b => `
      <div class="broadcast-brand-row" id="broadcast-row-${b.brand_id}">
        <div class="broadcast-brand-name">
          <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${b.brand_color};"></span>
          <span>${escapeHtml(b.brand_name)}</span>
        </div>
        <div class="broadcast-platform-badges">
          <span class="platform-status-badge status-publishing">⏳ Publishing...</span>
        </div>
      </div>
    `).join('');
  }

  try {
    appendBroadcastLog('Dispatched POST /api/folder-queue/publish-all');
    const res = await fetch('/api/folder-queue/publish-all', { method: 'POST' });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`);

    appendBroadcastLog(`Completed: ${data.total_posted} published, ${data.total_failed} failed, ${data.total_empty} empty.`);

    // Render results in rows
    if (data.results) {
      data.results.forEach(r => {
        appendBroadcastLog(`Brand [${r.brand_name}]: ${r.status.toUpperCase()} ${r.file_name ? `(${r.file_name})` : ''} ${r.error ? `Error: ${r.error}` : ''}`);
        const row = document.getElementById(`broadcast-row-${r.brand_id}`);
        if (row) {
          let badgeClass = 'status-pending';
          let badgeText = r.status;
          if (r.status === 'published') {
            badgeClass = 'status-success';
            badgeText = `✅ Published (${r.file_name || '1 item'})`;
          } else if (r.status === 'empty') {
            badgeClass = 'status-pending';
            badgeText = '✨ Folder Empty';
          } else {
            badgeClass = 'status-failed';
            badgeText = `❌ Failed (${r.error || 'Upload error'})`;
          }
          row.querySelector('.broadcast-platform-badges').innerHTML = `
            <span class="platform-status-badge ${badgeClass}">${badgeText}</span>
          `;
        }
      });
    }

    if (broadcastMsg) {
      broadcastMsg.innerHTML = `<strong>Broadcast Finished!</strong> ${data.total_posted} brand(s) published successfully.`;
    }
    if (broadcastSpinner) broadcastSpinner.style.display = 'none';
    if (btnCloseBroadcastModal) btnCloseBroadcastModal.disabled = false;
    if (btnDoneBroadcastModal) btnDoneBroadcastModal.style.display = 'inline-block';
    showToast(`🚀 Broadcast complete! ${data.total_posted} items published.`);

  } catch (err) {
    appendBroadcastLog(`CRITICAL ERROR: ${err.message}`);
    if (broadcastMsg) broadcastMsg.innerHTML = `<span style="color:#f87171;">⚠️ Broadcast failed: ${err.message}</span>`;
    if (broadcastSpinner) broadcastSpinner.style.display = 'none';
    if (btnCloseBroadcastModal) btnCloseBroadcastModal.disabled = false;
    if (btnDoneBroadcastModal) btnDoneBroadcastModal.style.display = 'inline-block';
  }
}

async function triggerPublishBrand(brandId) {
  const brand = (state.folderStatus || []).find(b => b.brand_id === brandId);
  const brandName = brand ? brand.brand_name : 'Brand';

  openBroadcastModal(`⚡ Publishing Next for ${brandName}`);
  appendBroadcastLog(`Triggering single-brand publish for: ${brandName}`);

  broadcastBrandsList.innerHTML = `
    <div class="broadcast-brand-row" id="broadcast-row-${brandId}">
      <div class="broadcast-brand-name">
        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${brand ? brand.brand_color : '#fff'};"></span>
        <span>${escapeHtml(brandName)}</span>
      </div>
      <div class="broadcast-platform-badges">
        <span class="platform-status-badge status-publishing">⏳ Publishing...</span>
      </div>
    </div>
  `;

  try {
    const res = await fetch(`/api/folder-queue/publish-brand/${brandId}`, { method: 'POST' });
    const data = await res.json();

    if (!res.ok || data.success === false) {
      const errMsg = data.error || data.detail || 'Failed to publish';
      appendBroadcastLog(`Error: ${errMsg}`);
      const row = document.getElementById(`broadcast-row-${brandId}`);
      if (row) {
        row.querySelector('.broadcast-platform-badges').innerHTML = `
          <span class="platform-status-badge status-failed">❌ ${errMsg}</span>
        `;
      }
      if (broadcastMsg) broadcastMsg.innerHTML = `<span style="color:#f87171;">⚠️ ${errMsg}</span>`;
    } else {
      appendBroadcastLog(`SUCCESS! Published ${data.file_name} across platforms.`);
      if (data.published_urls) {
        Object.entries(data.published_urls).forEach(([plat, val]) => {
          appendBroadcastLog(`   -> ${plat.toUpperCase()}: ${val}`);
        });
      }
      if (data.archived_to) {
        appendBroadcastLog(`Archived file to: ${data.archived_to}`);
      }

      const row = document.getElementById(`broadcast-row-${brandId}`);
      if (row) {
        row.querySelector('.broadcast-platform-badges').innerHTML = `
          <span class="platform-status-badge status-success">✅ Published (${data.file_name})</span>
        `;
      }
      if (broadcastMsg) {
        broadcastMsg.innerHTML = `<strong>Success!</strong> Published <em>${escapeHtml(data.file_name)}</em> across all connected platforms.`;
      }
      showToast(`✅ ${brandName}: Post published & archived!`);
    }

    if (broadcastSpinner) broadcastSpinner.style.display = 'none';
    if (btnCloseBroadcastModal) btnCloseBroadcastModal.disabled = false;
    if (btnDoneBroadcastModal) btnDoneBroadcastModal.style.display = 'inline-block';

  } catch (err) {
    appendBroadcastLog(`CRITICAL ERROR: ${err.message}`);
    if (broadcastMsg) broadcastMsg.innerHTML = `<span style="color:#f87171;">⚠️ Request failed: ${err.message}</span>`;
    if (broadcastSpinner) broadcastSpinner.style.display = 'none';
    if (btnCloseBroadcastModal) btnCloseBroadcastModal.disabled = false;
    if (btnDoneBroadcastModal) btnDoneBroadcastModal.style.display = 'inline-block';
  }
}

