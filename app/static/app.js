/* ==============================================================================
   INSTAGRAM ACCOUNT HUB - FRONTEND LOGIC & CONTROLLER
   ============================================================================== */

let allAccounts = [];
let currentFilter = 'all';

// DOM Elements
const accountsGrid = document.getElementById('accountsGrid');
const searchInput = document.getElementById('searchInput');
const activeCountEl = document.getElementById('activeCount');
const expiredCountEl = document.getElementById('expiredCount');
const btnRefresh = document.getElementById('btnRefresh');

// Modal Elements
const modalConnectAccount = document.getElementById('modalConnectAccount');
const modalAccountDetail = document.getElementById('modalAccountDetail');
const modalUpload = document.getElementById('modalUpload');
const modalProxySettings = document.getElementById('modalProxySettings');
const modalHistory = document.getElementById('modalHistory');

const btnOpenAddAccount = document.getElementById('btnOpenAddAccount');
const btnOpenUploader = document.getElementById('btnOpenUploader');
const btnOpenHistory = document.getElementById('btnOpenHistory');
const historyTableContainer = document.getElementById('historyTableContainer');
const profilesTableContainer = document.getElementById('profilesTableContainer');

const formLoginPurchased = document.getElementById('formAttachPurchased') || document.getElementById('formLoginPurchased');
const loginPurchasedRaw = document.getElementById('purchasedRawInput') || document.getElementById('loginPurchasedRaw');
const purchasedParsedPreview = document.getElementById('purchasedParsedPreview');
const previewUser = document.getElementById('previewUser');
const previewPass = document.getElementById('previewPass');
const preview2FA = document.getElementById('preview2FA');

const formLoginSessionId = document.getElementById('formAttachSessionId') || document.getElementById('formLoginSessionId');
const formLoginCredentials = document.getElementById('formAttachCreds') || document.getElementById('formLoginCredentials');
const formQuickUpload = document.getElementById('formQuickUpload');
const formAccountProxy = document.getElementById('formAccountProxy');
const btnClearProxy = document.getElementById('btnClearProxy');

const uploadAccountSelect = document.getElementById('uploadAccountSelect');
const toastContainer = document.getElementById('toastContainer');

// ==========================================
// Toast Notification
// ==========================================
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : '⚠️'}</span>
    <span>${message}</span>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==========================================
// Modal Handlers
// ==========================================
function openModal(modalEl) {
  modalEl.classList.add('open');
}

function closeModal(modalEl) {
  modalEl.classList.remove('open');
}

document.querySelectorAll('[data-close]').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetId = btn.getAttribute('data-close');
    const targetModal = document.getElementById(targetId);
    if (targetModal) closeModal(targetModal);
  });
});

// Close modal when clicking outside content
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal(overlay);
  });
});

if (btnOpenAddAccount) btnOpenAddAccount.addEventListener('click', () => openModal(modalConnectAccount));
if (btnOpenUploader) {
  btnOpenUploader.addEventListener('click', () => {
    populateUploaderAccountOptions();
    openModal(modalUpload);
  });
}
if (btnOpenHistory) {
  btnOpenHistory.addEventListener('click', () => {
    loadPostHistory();
    loadDbProfiles();
    openModal(modalHistory);
  });
}

// ==========================================
// Post Links Database Explorer
// ==========================================
async function loadPostHistory(username = null) {
  if (!historyTableContainer) return;
  historyTableContainer.innerHTML = `
    <div style="text-align: center; padding: 30px;">
      <div class="spinner"></div>
      <p style="margin-top: 10px; color: var(--text-secondary); font-size: 0.85rem;">Loading post links from database...</p>
    </div>
  `;

  try {
    const url = username ? `/upload/history?username=${encodeURIComponent(username)}` : '/upload/history';
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load history');
    const posts = await res.json();

    if (posts.length === 0) {
      historyTableContainer.innerHTML = `
        <div class="empty-state" style="padding: 40px 20px;">
          <p style="color: var(--text-muted); font-size: 0.9rem;">
            No post links recorded in the database yet.<br>
            Whenever a Reel, Post, or Story is published, its link and proxy will be stored here automatically!
          </p>
        </div>
      `;
      return;
    }

    historyTableContainer.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Account</th>
            <th>Type</th>
            <th>Instagram Link</th>
            <th>Proxy Routed Through</th>
            <th>Caption</th>
          </tr>
        </thead>
        <tbody>
          ${posts.map(p => `
            <tr>
              <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); white-space: nowrap;">
                ${new Date(p.created_at).toLocaleString()}
              </td>
              <td style="font-weight: 600;">@${p.username}</td>
              <td><span class="badge-type">${p.media_type}</span></td>
              <td>
                <a href="${p.url}" target="_blank" rel="noopener" style="color: #38bdf8; text-decoration: underline; font-family: var(--font-mono); font-size: 0.8rem; display: inline-flex; align-items: center; gap: 4px;">
                  ${p.code || 'View Post'} &rarr;
                </a>
              </td>
              <td style="font-family: var(--font-mono); font-size: 0.75rem;">
                ${p.proxy_used ? `<span style="color: #7dd3fc;">🌐 ${maskProxy(p.proxy_used)}</span>` : `<span style="color: var(--text-muted);">Direct IP</span>`}
              </td>
              <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-secondary);" title="${p.caption || ''}">
                ${p.caption || '-'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    historyTableContainer.innerHTML = `
      <div class="empty-state" style="padding: 20px;">
        <p style="color: var(--accent-red);">Error loading database history: ${err.message}</p>
      </div>
    `;
  }
}

// ==========================================
// Attached Profiles Database Explorer
// ==========================================
async function loadDbProfiles() {
  if (!profilesTableContainer) return;
  profilesTableContainer.innerHTML = `
    <div style="text-align: center; padding: 30px;">
      <div class="spinner"></div>
      <p style="margin-top: 10px; color: var(--text-secondary); font-size: 0.85rem;">Loading attached profiles from database...</p>
    </div>
  `;

  try {
    const res = await fetch('/accounts/database');
    if (!res.ok) throw new Error('Failed to load database accounts');
    const accounts = await res.json();

    if (accounts.length === 0) {
      profilesTableContainer.innerHTML = `
        <div class="empty-state" style="padding: 40px 20px;">
          <p style="color: var(--text-muted); font-size: 0.9rem;">
            No profiles registered in the database yet.
          </p>
        </div>
      `;
      return;
    }

    profilesTableContainer.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Instagram User ID</th>
            <th>Attached Proxy</th>
            <th>Password</th>
            <th>Session Cookie</th>
            <th>Registered At</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${accounts.map(a => `
            <tr>
              <td style="font-weight: 700;">@${a.username}</td>
              <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary);">
                ${a.user_id || '-'}
              </td>
              <td style="font-family: var(--font-mono); font-size: 0.75rem;">
                ${a.proxy ? `<span style="color: #7dd3fc;">🌐 ${maskProxy(a.proxy)}</span>` : `<span style="color: var(--text-muted);">Direct IP</span>`}
              </td>
              <td style="font-size: 0.8rem;">
                ${a.password ? '<span style="color: #34d399;">●●●●●● (Saved)</span>' : '<span style="color: var(--text-muted);">Not set</span>'}
              </td>
              <td style="font-size: 0.8rem;">
                ${a.session_id ? '<span style="color: #34d399;">●●●●●● (Saved)</span>' : '<span style="color: var(--text-muted);">File only</span>'}
              </td>
              <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); white-space: nowrap;">
                ${a.created_at ? new Date(a.created_at).toLocaleDateString() : '-'}
              </td>
              <td>
                <button class="btn btn-proxy" style="padding: 4px 8px; font-size: 0.75rem;" onclick="closeModal(modalHistory); openProxyModal('${a.username}')">
                  ⚙️ Proxy
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    profilesTableContainer.innerHTML = `
      <div class="empty-state" style="padding: 20px;">
        <p style="color: var(--accent-red);">Error loading profiles: ${err.message}</p>
      </div>
    `;
  }
}

// Tab Switcher inside Modals (scoped to modal-content container)
document.querySelectorAll('.modal-tab-btn').forEach(tabBtn => {
  tabBtn.addEventListener('click', () => {
    const parentModal = tabBtn.closest('.modal-content') || tabBtn.parentElement.parentElement;
    parentModal.querySelectorAll('.modal-tab-btn').forEach(b => b.classList.remove('active'));
    parentModal.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.remove('active');
      pane.style.display = 'none';
    });

    tabBtn.classList.add('active');
    const targetTabId = tabBtn.getAttribute('data-tab');
    const targetPane = document.getElementById(targetTabId);
    if (targetPane) {
      targetPane.classList.add('active');
      targetPane.style.display = 'block';
    }
  });
});

// ==========================================
// Helper: Mask Proxy String
// ==========================================
function maskProxy(proxy) {
  if (!proxy) return 'None';
  try {
    const url = new URL(proxy);
    if (url.username || url.password) {
      return `${url.protocol}//${url.username ? url.username + ':***@' : ''}${url.host}`;
    }
    return `${url.protocol}//${url.host}`;
  } catch (e) {
    // Basic regex masking
    return proxy.replace(/:([^@/]+)@/, ':***@');
  }
}

// ==========================================
// Load & Render Accounts
// ==========================================
async function fetchAccounts() {
  accountsGrid.innerHTML = `
    <div style="grid-column: 1 / -1; text-align: center; padding: 60px 0;">
      <div class="spinner" style="width: 32px; height: 32px; border-width: 3px; border-top-color: #dd2a7b;"></div>
      <p style="margin-top: 16px; color: var(--text-secondary); font-size: 0.9rem;">Scanning Instagram sessions on disk...</p>
    </div>
  `;

  try {
    const res = await fetch('/accounts', {
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error('Failed to fetch accounts');
    allAccounts = await res.json();
    renderAccounts();
    updateStats();
    populateUploaderAccountOptions();
  } catch (err) {
    console.error(err);
    accountsGrid.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        <h3>Could not load accounts</h3>
        <p>${err.message}</p>
        <button class="btn btn-secondary" onclick="fetchAccounts()">Try Again</button>
      </div>
    `;
  }
}

function updateStats() {
  const active = allAccounts.filter(a => a.is_authenticated).length;
  const expired = allAccounts.length - active;
  activeCountEl.textContent = active;
  expiredCountEl.textContent = expired;
}

function renderAccounts() {
  const query = searchInput.value.toLowerCase().trim();
  const filtered = allAccounts.filter(acc => {
    const matchesSearch = acc.username.toLowerCase().includes(query) ||
                          (acc.full_name && acc.full_name.toLowerCase().includes(query));
    if (!matchesSearch) return false;

    if (currentFilter === 'active') return acc.is_authenticated;
    if (currentFilter === 'expired') return !acc.is_authenticated;
    if (currentFilter === 'proxy') return Boolean(acc.proxy);
    return true;
  });

  if (filtered.length === 0) {
    accountsGrid.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        <h3>No Accounts Found</h3>
        <p>${allAccounts.length === 0 ? 'No Instagram accounts connected yet. Add your first account using its session ID or credentials.' : 'No accounts matching your current search or filter.'}</p>
        <button class="btn btn-primary" onclick="openModal(modalConnectAccount)">+ Connect Account</button>
      </div>
    `;
    return;
  }

  accountsGrid.innerHTML = filtered.map(acc => {
    const initial = (acc.full_name || acc.username).charAt(0).toUpperCase();
    const avatarHtml = acc.profile_pic_url
      ? `<img src="${acc.profile_pic_url}" alt="${acc.username}" class="avatar" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'avatar-fallback\\'>${initial}</div>'">`
      : `<div class="avatar-fallback">${initial}</div>`;

    const isAuth = Boolean(acc.is_authenticated);
    const hasProxy = Boolean(acc.proxy);

    return `
      <div class="account-card" data-username="${acc.username}">
        <div style="display: flex; flex-direction: column; gap: 14px;">
          <div class="account-card-header">
            <div class="avatar-container">
              ${avatarHtml}
              <div class="status-badge-dot ${isAuth ? 'active' : 'expired'}" title="${isAuth ? 'Session Active' : 'Session Expired'}"></div>
            </div>

            <div class="account-info">
              <div class="account-title-row">
                <span class="account-username">@${acc.username}</span>
                <span class="session-status-badge ${isAuth ? 'active' : 'expired'}">
                  ${isAuth ? 'Active' : 'Expired'}
                </span>
              </div>
              <div class="account-fullname">${acc.full_name || acc.username}</div>
              <div class="account-bio">${acc.biography || 'No bio available'}</div>
            </div>
          </div>

          <div class="account-stats-grid">
            <div class="stat-box">
              <div class="stat-number">${formatNumber(acc.follower_count)}</div>
              <div class="stat-label">Followers</div>
            </div>
            <div class="stat-box">
              <div class="stat-number">${formatNumber(acc.following_count)}</div>
              <div class="stat-label">Following</div>
            </div>
            <div class="stat-box">
              <div class="stat-number">${formatNumber(acc.media_count)}</div>
              <div class="stat-label">Posts</div>
            </div>
          </div>

          <div class="account-proxy-box">
            <div class="proxy-tag ${hasProxy ? 'active' : 'inactive'}">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
              </svg>
              <span>${hasProxy ? 'Proxy Active' : 'Direct IP'}</span>
            </div>
            <div class="proxy-host" title="${acc.proxy || 'No proxy configured'}">${hasProxy ? maskProxy(acc.proxy) : 'No Proxy'}</div>
          </div>
        </div>

        <div class="account-card-actions">
          <button type="button" class="btn-card-action" onclick="openAccountInBrowser('${acc.username}')" title="Open browser with this account logged in via assigned proxy">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
            <span>Open IG</span>
          </button>

          <button type="button" class="btn-card-action" onclick="viewAccountDetail('${acc.username}')" title="Inspect profile & media feed">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
            <span>Details</span>
          </button>

          <button type="button" class="btn-card-action" onclick="openProxyModal('${acc.username}')" title="Configure proxy for this account">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
            <span>Proxy</span>
          </button>

          <button type="button" class="btn-card-action btn-accent" onclick="quickUploadForAccount('${acc.username}')" title="Upload Reel to this account">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>Upload</span>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function formatNumber(num) {
  if (!num && num !== 0) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

function populateUploaderAccountOptions() {
  uploadAccountSelect.innerHTML = allAccounts.map(a => `
    <option value="${a.username}">${a.username} ${a.is_authenticated ? '(🟢 Active)' : '(🔴 Expired)'} ${a.proxy ? '(🌐 Proxy)' : ''}</option>
  `).join('');
}

function normalizeProxyInput(val) {
  if (!val) return '';
  const trimmed = val.trim();
  if (trimmed.includes('://')) return trimmed;
  const parts = trimmed.split(':');
  if (parts.length === 4) {
    const [ip, port, user, pw] = parts;
    return `http://${user}:${pw}@${ip}:${port}`;
  } else if (parts.length === 2) {
    return `http://${parts[0]}:${parts[1]}`;
  }
  return trimmed;
}

['proxyUrlInput', 'loginPurchasedProxy', 'loginSessionProxy', 'loginCredProxy', 'browserLoginProxy'].forEach(id => {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener('blur', () => {
      const normalized = normalizeProxyInput(el.value);
      if (normalized && normalized !== el.value) {
        el.value = normalized;
      }
    });
  }
});

// ==========================================
// Proxy Modal Handlers
// ==========================================
function openProxyModal(username) {
  const targetAcc = allAccounts.find(a => a.username === username);
  document.getElementById('proxyTargetUsername').value = username;
  document.getElementById('proxyModalTitle').textContent = `Proxy Configuration for @${username}`;
  document.getElementById('proxyUrlInput').value = targetAcc?.proxy || '';
  openModal(modalProxySettings);
}

if (formAccountProxy) {
  formAccountProxy.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('proxyTargetUsername').value;
    const proxy = document.getElementById('proxyUrlInput').value.trim() || null;
    const btn = document.getElementById('btnSaveProxy');

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> <span>Saving Proxy...</span>`;

    try {
      const res = await fetch(`/accounts/${username}/proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proxy })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update proxy');

      showToast(`Proxy ${proxy ? 'configured' : 'cleared'} for @${username}!`);
      closeModal(modalProxySettings);
      await fetchAccounts();
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>Save Proxy</span>`;
    }
  });
}

if (btnClearProxy) {
  btnClearProxy.addEventListener('click', async () => {
    const username = document.getElementById('proxyTargetUsername').value;
    if (!confirm(`Clear proxy for @${username}? The account will connect directly.`)) return;

    try {
      const res = await fetch(`/accounts/${username}/proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proxy: null })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to clear proxy');

      showToast(`Proxy cleared for @${username}!`);
      document.getElementById('proxyUrlInput').value = '';
      closeModal(modalProxySettings);
      await fetchAccounts();
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    }
  });
}

// ==========================================
// Account Detail View & Media Inspector
// ==========================================
async function viewAccountDetail(username) {
  const detailModalBody = document.getElementById('detailModalBody');
  const detailModalTitle = document.getElementById('detailModalTitle');

  detailModalTitle.textContent = `@${username} Profile & Gallery`;
  detailModalBody.innerHTML = `
    <div style="text-align: center; padding: 40px;">
      <div class="spinner"></div>
      <p style="margin-top: 12px; color: var(--text-secondary);">Fetching account profile and media from Instagram...</p>
    </div>
  `;
  openModal(modalAccountDetail);

  try {
    const [profileRes, mediaRes] = await Promise.all([
      fetch(`/accounts/${username}/profile`),
      fetch(`/accounts/${username}/medias?amount=12`)
    ]);

    const profile = await profileRes.json();
    const medias = await mediaRes.json();

    const initial = (profile.full_name || username).charAt(0).toUpperCase();
    const avatarHtml = profile.profile_pic_url
      ? `<img src="${profile.profile_pic_url}" alt="${username}" class="avatar" style="width: 72px; height: 72px;">`
      : `<div class="avatar-fallback" style="width: 72px; height: 72px;">${initial}</div>`;

    const mediaTiles = medias.length > 0 ? medias.map(m => `
      <div class="media-tile">
        ${m.thumbnail_url ? `<img src="${m.thumbnail_url}" alt="${m.code}">` : `<div style="background: #232736; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #9ca3af;">Media ${m.code}</div>`}
        <div class="media-tile-overlay">
          <div style="font-size: 0.7rem; color: #fff; line-height: 1.2; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
            ${m.caption || 'No caption'}
          </div>
          <div class="media-stats">
            <span>❤️ ${formatNumber(m.like_count)}</span>
            ${m.view_count ? `<span>👁️ ${formatNumber(m.view_count)}</span>` : ''}
          </div>
          <a href="https://www.instagram.com/p/${m.code}/" target="_blank" style="color: #38bdf8; font-size: 0.75rem; text-decoration: underline; margin-top: 4px;">View on Instagram &rarr;</a>
        </div>
      </div>
    `).join('') : `<p style="color: var(--text-muted); font-size: 0.85rem; padding: 20px 0;">No media posts found for this account.</p>`;

    detailModalBody.innerHTML = `
      <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid var(--border-subtle);">
        ${avatarHtml}
        <div style="flex: 1;">
          <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <h2 style="font-size: 1.3rem; font-weight: 700; color: #fff;">@${profile.username}</h2>
            <span style="font-size: 0.75rem; padding: 3px 8px; border-radius: 99px; ${profile.is_authenticated ? 'background: rgba(16,185,129,0.15); color: #34d399;' : 'background: rgba(239,68,68,0.15); color: #f87171;'}">
              ${profile.is_authenticated ? '🟢 Active Session' : '🔴 Session Expired'}
            </span>
            ${profile.proxy ? `
              <span style="font-size: 0.75rem; padding: 3px 8px; border-radius: 99px; background: rgba(56,189,248,0.15); color: #38bdf8;" title="${profile.proxy}">
                🌐 Proxy: ${maskProxy(profile.proxy)}
              </span>
            ` : `
              <span style="font-size: 0.75rem; padding: 3px 8px; border-radius: 99px; background: rgba(255,255,255,0.05); color: var(--text-muted);">
                🌐 Direct IP
              </span>
            `}
          </div>
          <p style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 2px;">${profile.full_name || ''}</p>
          <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 6px;">${profile.biography || ''}</p>
          <div style="display: flex; gap: 16px; margin-top: 10px; font-size: 0.85rem; color: var(--text-secondary);">
            <span><strong>${formatNumber(profile.follower_count)}</strong> Followers</span>
            <span><strong>${formatNumber(profile.following_count)}</strong> Following</span>
            <span><strong>${formatNumber(profile.media_count)}</strong> Posts</span>
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap;">
        <button class="btn btn-primary" onclick="openAccountInBrowser('${profile.username}')" style="flex: 1;">
          🌐 Open Logged-in Browser
        </button>
        <button class="btn btn-proxy" onclick="closeModal(modalAccountDetail); openProxyModal('${profile.username}')" style="flex: 1;">
          ⚙️ Change Proxy
        </button>
        <button class="btn btn-secondary" onclick="closeModal(modalAccountDetail); quickUploadForAccount('${profile.username}')" style="flex: 1;">
          🚀 Publish Reel
        </button>
        <button class="btn btn-danger-ghost" onclick="closeModal(modalAccountDetail); deleteAccount('${profile.username}')" style="flex: 1;">
          🗑️ Delete Session
        </button>
      </div>

      <div>
        <h3 style="font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 12px;">Recent Uploads & Gallery</h3>
        <div class="media-grid">
          ${mediaTiles}
        </div>
      </div>
    `;

  } catch (err) {
    detailModalBody.innerHTML = `
      <div class="empty-state">
        <p style="color: var(--accent-red);">Failed to load account media: ${err.message}</p>
      </div>
    `;
  }
}

async function openAccountInBrowser(username) {
  showToast(`Opening browser for @${username}...`);
  try {
    const res = await fetch(`/accounts/${username}/open-browser`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to open browser');
    showToast(`Browser opened for @${username} (logged in via proxy)!`);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

function quickUploadForAccount(username) {
  populateUploaderAccountOptions();
  uploadAccountSelect.value = username;
  openModal(modalUpload);
}

// ==========================================
// Delete Account Session
// ==========================================
async function deleteAccount(username) {
  if (!confirm(`Are you sure you want to remove the saved session for @${username}?`)) return;

  try {
    const res = await fetch(`/accounts/${username}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to delete session');
    showToast(`Session for @${username} removed`);
    await fetchAccounts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// Form Submissions
// ==========================================

// ------------------------------------------
// Browser Login via Proxy Controller
// ------------------------------------------
let browserPollInterval = null;

const formStartBrowserLogin = document.getElementById('formStartBrowserLogin');
const browserLoginProxy = document.getElementById('browserLoginProxy');
const btnLaunchBrowser = document.getElementById('btnLaunchBrowser');
const browserActivePanel = document.getElementById('browserActivePanel');
const browserStatusText = document.getElementById('browserStatusText');
const btnExtractSession = document.getElementById('btnExtractBrowserSession') || document.getElementById('btnExtractSession');
const btnCancelBrowser = document.getElementById('btnCancelBrowser');

if (formStartBrowserLogin) {
  formStartBrowserLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    const proxy = browserLoginProxy.value.trim();
    if (!proxy) {
      showToast('Please enter a proxy string', 'error');
      return;
    }

    btnLaunchBrowser.disabled = true;
    btnLaunchBrowser.innerHTML = `<span class="spinner"></span> <span>Launching Browser Window...</span>`;

    try {
      const res = await fetch('/accounts/browser-login/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proxy })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to start browser');

      formStartBrowserLogin.style.display = 'none';
      browserActivePanel.style.display = 'block';
      browserStatusText.textContent = 'Browser window is open. Waiting for you to log in...';
      showToast('Browser launched! Log in on Instagram window.');

      // Start polling status in background
      if (browserPollInterval) clearInterval(browserPollInterval);
      browserPollInterval = setInterval(pollBrowserStatus, 1500);

    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      btnLaunchBrowser.disabled = false;
      btnLaunchBrowser.innerHTML = `<span>🚀 Launch Browser via Proxy</span>`;
    }
  });
}

async function pollBrowserStatus() {
  try {
    const res = await fetch('/accounts/browser-login/status');
    const data = await res.json();
    if (data.status === 'success') {
      clearInterval(browserPollInterval);
      showToast(`🎉 Successfully authenticated @${data.username}!`);
      resetBrowserPanel();
      closeModal(modalConnectAccount);
      await fetchAccounts();
    } else if (data.status === 'extracting') {
      browserStatusText.textContent = 'Detected login! Extracting session & saving...';
    } else if (data.status === 'error') {
      clearInterval(browserPollInterval);
      showToast(`Login error: ${data.error}`, 'error');
      resetBrowserPanel();
    } else if (data.status === 'cancelled') {
      clearInterval(browserPollInterval);
      resetBrowserPanel();
    }
  } catch (e) {
    // ignore polling error
  }
}

if (btnExtractSession) {
  btnExtractSession.addEventListener('click', async () => {
    btnExtractSession.disabled = true;
    btnExtractSession.innerHTML = `<span class="spinner"></span> <span>Extracting Session Cookies...</span>`;
    try {
      const res = await fetch('/accounts/browser-login/extract', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Session cookie not detected yet.');

      if (browserPollInterval) clearInterval(browserPollInterval);
      showToast(`🎉 Successfully authenticated @${data.username}!`);
      resetBrowserPanel();
      closeModal(modalConnectAccount);
      await fetchAccounts();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btnExtractSession.disabled = false;
      btnExtractSession.innerHTML = `<span>✅ I've Logged In! Extract Session & Save</span>`;
    }
  });
}

if (btnCancelBrowser) {
  btnCancelBrowser.addEventListener('click', async () => {
    if (browserPollInterval) clearInterval(browserPollInterval);
    await fetch('/accounts/browser-login/stop', { method: 'POST' });
    resetBrowserPanel();
    showToast('Browser closed');
  });
}

function resetBrowserPanel() {
  if (browserActivePanel) browserActivePanel.style.display = 'none';
  if (formStartBrowserLogin) formStartBrowserLogin.style.display = 'block';
}

// Helper: Parse purchased account string
function parsePurchasedString(raw) {
  raw = raw.trim();
  if (!raw) return null;
  let parts = [];
  if (raw.includes('\t')) {
    parts = raw.split('\t').map(s => s.trim()).filter(Boolean);
  } else if (raw.includes('|')) {
    parts = raw.split('|').map(s => s.trim()).filter(Boolean);
  } else if (raw.includes(':') && !raw.startsWith('http')) {
    parts = raw.split(':').map(s => s.trim()).filter(Boolean);
  } else {
    const tokens = raw.split(/\s+/);
    if (tokens.length >= 2) {
      parts = [tokens[0], tokens[1], tokens.slice(2).join(' ')];
    } else {
      parts = tokens;
    }
  }
  return {
    username: parts[0] || '',
    password: parts[1] || '',
    totp_secret: parts[2] || ''
  };
}

// Live preview when typing or pasting purchased string
if (loginPurchasedRaw) {
  loginPurchasedRaw.addEventListener('input', () => {
    const parsed = parsePurchasedString(loginPurchasedRaw.value);
    if (purchasedParsedPreview && previewUser && previewPass && preview2FA) {
      if (parsed && (parsed.username || parsed.password)) {
        purchasedParsedPreview.style.display = 'block';
        previewUser.textContent = parsed.username ? `@${parsed.username}` : '(not detected)';
        previewPass.textContent = parsed.password ? `•••••••• (${parsed.password.length} chars)` : '(not detected)';
        preview2FA.textContent = parsed.totp_secret || '(none detected)';
      } else {
        purchasedParsedPreview.style.display = 'none';
      }
    }
  });
}

// 0. Purchased Account (1-Click Auto 2FA) Login
if (formLoginPurchased) {
  formLoginPurchased.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btnSubmitPurchased') || document.getElementById('btnSubmitPurchasedLogin');
    const raw_string = (loginPurchasedRaw ? loginPurchasedRaw.value.trim() : '') || (document.getElementById('purchasedRawInput')?.value.trim() || '');
    const proxyInput = document.getElementById('purchasedProxyOverride') || document.getElementById('loginPurchasedProxy');
    const proxy = proxyInput ? proxyInput.value.trim() || null : null;

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span> <span>Calculating 2FA & logging in...</span>`;
    }

    try {
      const res = await fetch('/accounts/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_account_string: raw_string, proxy })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');

      showToast(`Successfully authenticated @${data.username}!`);
      formLoginPurchased.reset();
      if (purchasedParsedPreview) purchasedParsedPreview.style.display = 'none';
      closeModal(modalConnectAccount);
      await fetchAccounts();
    } catch (err) {
      showToast(`Login failed: ${err.message}`, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>Authenticate & Save to Database</span>`;
      }
    }
  });
}

// 2FA Helper Tool in Session ID tab
const btnGen2FA = document.getElementById('btnGen2FA');
const helper2faSecret = document.getElementById('helper2faSecret');
const helper2faResult = document.getElementById('helper2faResult');
const helper2faCode = document.getElementById('helper2faCode');
const helper2faTimer = document.getElementById('helper2faTimer');
let totpInterval = null;

if (btnGen2FA && helper2faSecret) {
  btnGen2FA.addEventListener('click', async () => {
    const secret = helper2faSecret.value.trim();
    if (!secret) {
      showToast('Please paste a 2FA secret key', 'error');
      return;
    }
    async function updateCode() {
      try {
        const res = await fetch(`/accounts/totp-code?secret=${encodeURIComponent(secret)}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);
        if (helper2faResult) helper2faResult.style.display = 'block';
        if (helper2faCode) helper2faCode.textContent = data.code;
        if (helper2faTimer) helper2faTimer.textContent = `(${data.seconds_remaining}s remaining)`;
      } catch (e) {
        showToast(`Failed: ${e.message}`, 'error');
      }
    }
    await updateCode();
    if (totpInterval) clearInterval(totpInterval);
    totpInterval = setInterval(updateCode, 5000);
  });
}

// 1. Session ID Login
if (formLoginSessionId) {
  formLoginSessionId.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btnSubmitSessionId') || document.getElementById('btnSubmitSessionLogin');
    const uInput = document.getElementById('sessionUsername') || document.getElementById('loginSessionUsername');
    const sInput = document.getElementById('sessionCookie') || document.getElementById('loginSessionId');
    const pInput = document.getElementById('sessionPassword') || document.getElementById('loginSessionPassword');
    const pxInput = document.getElementById('sessionProxy') || document.getElementById('loginSessionProxy');

    const username = uInput ? uInput.value.trim() : '';
    const session_id = sInput ? sInput.value.trim() : '';
    const password = pInput ? pInput.value || null : null;
    const proxy = pxInput ? pxInput.value.trim() || null : null;

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span> <span>Authenticating with Instagram...</span>`;
    }

    try {
      const res = await fetch('/accounts/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, session_id, password, proxy })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');

      showToast(`Successfully authenticated @${username}!`);
      formLoginSessionId.reset();
      closeModal(modalConnectAccount);
      await fetchAccounts();
    } catch (err) {
      showToast(`Login failed: ${err.message}`, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>Save Session to Database</span>`;
      }
    }
  });
}

// 2. Credentials Login
if (formLoginCredentials) {
  formLoginCredentials.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btnSubmitCreds') || document.getElementById('btnSubmitCredLogin');
    const uInput = document.getElementById('credsUsername') || document.getElementById('loginCredUsername');
    const pInput = document.getElementById('credsPassword') || document.getElementById('loginCredPassword');
    const pxInput = document.getElementById('credsProxy') || document.getElementById('loginCredProxy');
    const tInput = document.getElementById('credsTotpSecret') || document.getElementById('loginCred2FA');

    const username = uInput ? uInput.value.trim() : '';
    const password = pInput ? pInput.value : '';
    const proxy = pxInput ? pxInput.value.trim() || null : null;
    const totp_secret = tInput ? tInput.value.trim() || null : null;

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span> <span>Logging in...</span>`;
    }

    try {
      const res = await fetch('/accounts/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, proxy, totp_secret })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');

      showToast(`Successfully authenticated @${username}!`);
      formLoginCredentials.reset();
      closeModal(modalConnectAccount);
      await fetchAccounts();
    } catch (err) {
      showToast(`Login failed: ${err.message}`, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>Login & Save Session</span>`;
      }
    }
  });
}

// ==========================================
// Media Drag & Drop and File Browser
// ==========================================
const mediaDropZone = document.getElementById('mediaDropZone');
const mediaFileInput = document.getElementById('mediaFileInput');
const btnBrowseMedia = document.getElementById('btnBrowseMedia');
const dropZonePrompt = document.getElementById('dropZonePrompt');
const mediaPreviewCard = document.getElementById('mediaPreviewCard');
const mediaPreviewThumb = document.getElementById('mediaPreviewThumb');
const mediaPreviewName = document.getElementById('mediaPreviewName');
const mediaPreviewMeta = document.getElementById('mediaPreviewMeta');
const btnRemoveMedia = document.getElementById('btnRemoveMedia');
const btnToggleManualPath = document.getElementById('btnToggleManualPath');
const uploadVideoPath = document.getElementById('uploadVideoPath');

if (btnBrowseMedia && mediaFileInput) {
  btnBrowseMedia.addEventListener('click', (e) => {
    e.stopPropagation();
    mediaFileInput.click();
  });
}

if (mediaDropZone) {
  mediaDropZone.addEventListener('click', (e) => {
    if (e.target.closest('#btnRemoveMedia') || e.target.closest('#btnBrowseMedia')) return;
    mediaFileInput.click();
  });

  mediaDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    mediaDropZone.classList.add('dragover');
  });

  mediaDropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    mediaDropZone.classList.remove('dragover');
  });

  mediaDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    mediaDropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleMediaFileUpload(e.dataTransfer.files[0]);
    }
  });
}

if (mediaFileInput) {
  mediaFileInput.addEventListener('change', () => {
    if (mediaFileInput.files && mediaFileInput.files.length > 0) {
      handleMediaFileUpload(mediaFileInput.files[0]);
    }
  });
}

async function handleMediaFileUpload(file) {
  if (!file) return;

  const isVideo = file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|webm)$/i);

  dropZonePrompt.innerHTML = `
    <div style="padding: 10px;">
      <div class="spinner" style="width: 24px; height: 24px;"></div>
      <p style="margin-top: 8px; font-size: 0.85rem; color: #38bdf8;">Uploading ${file.name}...</p>
    </div>
  `;

  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/upload/file', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');

    // Set resolved local server path for the upload payload
    uploadVideoPath.value = data.file_path;

    // Show preview card
    dropZonePrompt.style.display = 'none';
    mediaPreviewCard.style.display = 'flex';
    mediaPreviewThumb.textContent = isVideo ? '🎬' : '🖼️';
    mediaPreviewName.textContent = data.filename;
    mediaPreviewMeta.textContent = `${(data.size_bytes / (1024 * 1024)).toFixed(2)} MB • Ready to publish`;

    showToast(`Media "${data.filename}" ready!`);
  } catch (err) {
    showToast(`Failed to upload media: ${err.message}`, 'error');
    resetMediaDropZone();
  }
}

if (btnRemoveMedia) {
  btnRemoveMedia.addEventListener('click', (e) => {
    e.stopPropagation();
    resetMediaDropZone();
  });
}

function resetMediaDropZone() {
  uploadVideoPath.value = '';
  if (mediaFileInput) mediaFileInput.value = '';
  mediaPreviewCard.style.display = 'none';
  dropZonePrompt.style.display = 'block';
  dropZonePrompt.innerHTML = `
    <div class="drop-zone-icon">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
      </svg>
    </div>
    <div class="drop-zone-title">Drag & drop your video or photo here</div>
    <div class="drop-zone-subtitle">or <button type="button" class="btn-browse-link" id="btnBrowseMedia">browse files</button> from your computer</div>
    <div class="drop-zone-hints">Supports MP4, MOV, JPG, PNG</div>
  `;
  const newBtn = document.getElementById('btnBrowseMedia');
  if (newBtn) {
    newBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      mediaFileInput.click();
    });
  }
}

if (btnToggleManualPath) {
  btnToggleManualPath.addEventListener('click', () => {
    if (uploadVideoPath.style.display === 'none') {
      uploadVideoPath.style.display = 'block';
      btnToggleManualPath.textContent = 'Hide path input';
    } else {
      uploadVideoPath.style.display = 'none';
      btnToggleManualPath.textContent = 'Edit path manually';
    }
  });
}

// 3. Media Uploader Form
// 3. Media Uploader Form (Immediate Publish or Calendar Scheduling)
const uploadScheduleToggle = document.getElementById('uploadScheduleToggle');
const uploadScheduleFields = document.getElementById('uploadScheduleFields');

if (uploadScheduleToggle && uploadScheduleFields) {
  uploadScheduleToggle.addEventListener('change', () => {
    uploadScheduleFields.style.display = uploadScheduleToggle.checked ? 'block' : 'none';
    const submitBtn = document.getElementById('btnSubmitUpload');
    if (submitBtn) {
      submitBtn.innerHTML = uploadScheduleToggle.checked 
        ? `<span>📅 Add to Scheduled Planner Queue</span>` 
        : `<span>Publish Media to Instagram</span>`;
    }
  });
}

function openCreatePostModal() {
  populateUploaderAccountOptions();
  populateBrandSelects();
  openModal(modalUpload);
}

if (formQuickUpload) {
  formQuickUpload.addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('btnSubmitUpload');
  const feedback = document.getElementById('uploadFeedbackArea');
  const isScheduled = uploadScheduleToggle?.checked;
  const scheduleTime = document.getElementById('uploadScheduleTime')?.value;

  const rawMusicVol = parseFloat(document.getElementById('uploadMusicVolume')?.value);
  const musicVolume = isNaN(rawMusicVol) ? 10.0 : rawMusicVol;

  const mediaPath = document.getElementById('uploadVideoPath').value.trim();
  const caption = document.getElementById('uploadCaption').value.trim();
  const musicQuery = document.getElementById('uploadMusicQuery').value.trim() || null;
  const audioOffset = parseFloat(document.getElementById('uploadAudioOffset').value) || 0.0;
  const firstComment = document.getElementById('uploadFirstComment')?.value.trim() || null;
  const targetBrandId = document.getElementById('uploadBrandSelect')?.value || currentBrandId;
  const targetUsername = uploadAccountSelect.value;

  if (isScheduled && !scheduleTime) {
    showToast('Please select a scheduled date and time', 'error');
    return;
  }

  btn.disabled = true;
  feedback.style.display = 'block';

  // Branch A: Scheduled Post (Adds to Content Planner Database)
  if (isScheduled) {
    btn.innerHTML = `<span class="spinner"></span> <span>Scheduling Post...</span>`;
    feedback.innerHTML = `
      <div style="background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.3); border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #bae6fd;">
        ⏳ Adding post to calendar queue for ${scheduleTime}...
      </div>
    `;

    try {
      const isVideo = ['.mp4', '.mov', '.webm', '.mkv'].some(ext => mediaPath.toLowerCase().endsWith(ext));
      const res = await fetch('/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_id: targetBrandId,
          target_platforms: ['instagram'],
          post_type: isVideo ? 'reel' : 'post',
          media_paths: [mediaPath],
          caption: caption,
          first_comment: firstComment,
          scheduled_time: scheduleTime,
          music_query: musicQuery,
          audio_start_sec: audioOffset,
          music_volume: musicVolume
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to schedule post');

      feedback.innerHTML = `
        <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #6ee7b7;">
          🎉 <strong>Post Scheduled Successfully!</strong><br>
          Added to planner for <code>${data.scheduled_time}</code>.
        </div>
      `;
      showToast('Post scheduled successfully!');
      loadCalendarPosts();
      loadQueuePosts();
    } catch (err) {
      feedback.innerHTML = `
        <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #fca5a5;">
          ❌ Scheduling Error: ${err.message}
        </div>
      `;
      showToast(`Scheduling failed: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>📅 Add to Scheduled Planner Queue</span>`;
    }
    return;
  }

  // Branch B: Immediate Publishing
  btn.innerHTML = `<span class="spinner"></span> <span>Processing & Uploading to Instagram...</span>`;
  feedback.innerHTML = `
    <div style="background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.3); border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #bae6fd;">
      ⏳ Mixing audio & uploading to Instagram... This typically takes 15–30 seconds.
    </div>
  `;

  const payload = {
    username: targetUsername,
    video_path: mediaPath,
    caption: caption,
    music_query: musicQuery,
    audio_start_time_sec: audioOffset,
    music_volume: musicVolume,
    share_to_facebook: false
  };

  try {
    const isVideo = ['.mp4', '.mov', '.webm', '.mkv'].some(ext => mediaPath.toLowerCase().endsWith(ext));
    const endpoint = isVideo ? '/upload/reel' : '/upload/post';
    const bodyPayload = isVideo ? payload : {
      username: targetUsername,
      media_paths: [mediaPath],
      caption: caption,
      share_to_facebook: false
    };

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyPayload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to upload media');

    feedback.innerHTML = `
      <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #6ee7b7;">
        🎉 <strong>Published Successfully!</strong><br>
        <a href="${data.url}" target="_blank" style="color: #38bdf8; text-decoration: underline; margin-top: 6px; display: inline-block;">
          Open on Instagram: ${data.url} &rarr;
        </a>
      </div>
    `;
    showToast('Published successfully!');
    loadAnalytics();
  } catch (err) {
    feedback.innerHTML = `
      <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #fca5a5;">
        ❌ Upload Error: ${err.message}
      </div>
    `;
    showToast(`Upload failed: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Publish Media to Instagram</span>`;
  }
  });
}

// ==============================================================================
// SOCIAL HUB MULTI-BRAND & WORKSPACE ENGINE
// ==============================================================================

let allBrands = [];
let currentBrandId = null;
let currentCalendarDate = new Date();
let scheduledPostsCache = [];

const globalBrandSelect = document.getElementById('globalBrandSelect');
const uploadBrandSelect = document.getElementById('uploadBrandSelect');
const evergreenBrandSelect = document.getElementById('evergreenBrandSelect');
const modalAddBrand = document.getElementById('modalAddBrand');
const modalCsvImport = document.getElementById('modalCsvImport');
const modalAddEvergreen = document.getElementById('modalAddEvergreen');
const btnOpenAddBrand = document.getElementById('btnOpenAddBrand');
const btnOpenCsvModal = document.getElementById('btnOpenCsvModal');
const btnOpenAddEvergreen = document.getElementById('btnOpenAddEvergreen');
const btnMasterPostAll = document.getElementById('btnMasterPostAll');
const btnOpenAllFolders = document.getElementById('btnOpenAllFolders');
const btnAutoFillQueue = document.getElementById('btnAutoFillQueue');

// 1. Fetch Brands & Populate Dropdowns
async function fetchBrands() {
  try {
    const res = await fetch('/api/brands');
    if (!res.ok) throw new Error('Failed to load brands');
    allBrands = await res.json();
    populateBrandSelects();
  } catch (err) {
    console.error('Error fetching brands:', err);
  }
}

function updateWorkspaceDot() {
  const dot = document.getElementById('workspaceDotIndicator');
  if (!dot || !globalBrandSelect) return;
  const brand = allBrands.find(b => b.id === globalBrandSelect.value);
  if (brand && brand.color) {
    dot.style.background = brand.color;
    dot.style.boxShadow = `0 0 8px ${brand.color}`;
  } else {
    dot.style.background = '#10B981';
    dot.style.boxShadow = '0 0 8px rgba(16, 185, 129, 0.7)';
  }
}

function populateBrandSelects() {
  const selects = [globalBrandSelect, uploadBrandSelect].filter(Boolean);
  selects.forEach(sel => {
    const currentVal = sel.value;
    sel.innerHTML = allBrands.map(b => `
      <option value="${b.id}">${b.name}</option>
    `).join('');

    if (currentVal && allBrands.some(b => b.id === currentVal)) {
      sel.value = currentVal;
    } else if (allBrands.length > 0) {
      sel.value = allBrands[0].id;
    }
  });

  if (globalBrandSelect && globalBrandSelect.value) {
    currentBrandId = globalBrandSelect.value;
    updateWorkspaceDot();
  }
}

if (globalBrandSelect) {
  globalBrandSelect.addEventListener('change', () => {
    currentBrandId = globalBrandSelect.value;
    updateWorkspaceDot();
    const activeTab = document.querySelector('.tab-btn.active')?.getAttribute('data-tab');
    if (activeTab === 'folders') loadBrandFolders();
    else if (activeTab === 'planner') loadCalendarPosts();
    else if (activeTab === 'queue') loadQueuePosts();
    else if (activeTab === 'analytics') loadAnalytics();
    else if (activeTab === 'accounts') fetchAccounts();
  });
}

// 2. Navigation Tab Switcher & Browser Routing
function switchTab(tabName, updateHistory = true) {
  if (tabName === 'vault') tabName = 'folders';
  const validTabs = ['planner', 'analytics', 'folders', 'queue', 'accounts', 'engagement'];
  if (!validTabs.includes(tabName)) tabName = 'planner';

  // Toggle active class on navigation buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Toggle active class on view panels
  document.querySelectorAll('.view-panel').forEach(panel => {
    if (panel.id === `view-${tabName}`) {
      panel.classList.add('active');
    } else {
      panel.classList.remove('active');
    }
  });

  // Update browser URL bar
  const targetPath = '/' + tabName;
  if (updateHistory && window.location.pathname !== targetPath) {
    history.pushState({ tab: tabName }, '', targetPath);
  }

  // Trigger relevant data loader
  if (tabName === 'folders') loadBrandFolders();
  else if (tabName === 'planner') loadCalendarPosts();
  else if (tabName === 'queue') loadQueuePosts();
  else if (tabName === 'analytics') loadAnalytics();
  else if (tabName === 'accounts') fetchAccounts();
  else if (tabName === 'engagement') loadEngagementView();
}

// Attach click listeners to tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tabName = btn.getAttribute('data-tab');
    switchTab(tabName, true);
  });
});

// Handle browser Back / Forward buttons
window.addEventListener('popstate', () => {
  const currentPath = window.location.pathname.replace(/^\/+/, '').split('/')[0] || 'planner';
  switchTab(currentPath, false);
});

// 3. Brand Folders & Content Vault
async function loadBrandFolders() {
  const grid = document.getElementById('brandFoldersGrid');
  const statBrands = document.getElementById('statFolderBrandsCount');
  const statQueue = document.getElementById('statFolderQueueTotal');
  if (!grid) return;

  grid.innerHTML = '<div style="color: var(--text-secondary); padding: 20px;">Scanning brand folders...</div>';

  try {
    const res = await fetch('/api/folder-queue/status');
    if (!res.ok) throw new Error('Failed to load folder status');
    const brandsData = await res.json();

    let totalPending = 0;
    brandsData.forEach(b => totalPending += b.pending_count);

    if (statBrands) statBrands.textContent = brandsData.length;
    if (statQueue) statQueue.textContent = totalPending;

    if (brandsData.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No brand workspaces found.</div>';
      return;
    }

    grid.innerHTML = brandsData.map(b => {
      const itemsHtml = b.items.length === 0 
        ? '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 12px 0;">Folder is empty. Drop videos/photos into this brand folder.</div>'
        : b.items.map(item => `
          <div class="brand-queue-item">
            <div class="queue-item-thumb">
              ${item.thumbnail ? `<img src="/media/thumbnails/${item.thumbnail}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;">` : (item.media_type === 'video' ? '🎬' : '📷')}
            </div>
            <div class="queue-item-info">
              <div class="queue-item-name" title="${item.filename}">${item.filename}</div>
              <div class="queue-item-meta">${item.size_mb} MB &bull; ${item.caption ? item.caption.substring(0, 32) + '...' : 'No caption'}</div>
              ${item.music_query ? `<div style="font-size: 0.7rem; color: #38bdf8;">🎵 ${item.music_query.substring(0, 28)}</div>` : ''}
            </div>
          </div>
        `).join('');

      return `
        <div class="brand-folder-card">
          <div class="brand-card-header">
            <div class="brand-card-title-group">
              <span class="brand-badge-dot" style="background-color: ${b.color_badge};"></span>
              <span class="brand-card-name">${b.brand_name}</span>
            </div>
            <span class="brand-card-badge">${b.pending_count} Pending</span>
          </div>

          <div style="font-size: 0.75rem; color: var(--text-secondary); font-family: var(--font-mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            📂 ${b.folder_path}
          </div>

          <div class="brand-queue-preview-list">
            ${itemsHtml}
          </div>

          <div style="display: flex; gap: 8px; margin-top: auto;">
            <button type="button" class="btn btn-primary" style="flex: 2; font-size: 0.8rem;" onclick="publishBrandNext('${b.brand_id}')" ${b.pending_count === 0 ? 'disabled' : ''}>
              <span>🚀 Publish Next</span>
            </button>
            <button type="button" class="btn btn-secondary" style="flex: 1; font-size: 0.8rem;" onclick="openBrandFolder('${b.brand_id}')">
              <span>📂 Open</span>
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    grid.innerHTML = `<div style="color: var(--accent-red); padding: 20px;">Error: ${err.message}</div>`;
  }
}

async function publishBrandNext(brandId) {
  showToast('Publishing next media item to Instagram...');
  try {
    const res = await fetch(`/api/folder-queue/publish-brand/${brandId}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || 'Failed to publish');
    showToast(`Published ${data.media_name} successfully!`);
    loadBrandFolders();
  } catch (err) {
    showToast(`Publish error: ${err.message}`, 'error');
  }
}

async function openBrandFolder(brandId) {
  try {
    await fetch(`/api/folder-queue/open-folder/${brandId}`, { method: 'POST' });
  } catch (err) {
    showToast(`Could not open folder: ${err.message}`, 'error');
  }
}

if (btnMasterPostAll) {
  btnMasterPostAll.addEventListener('click', async () => {
    btnMasterPostAll.disabled = true;
    btnMasterPostAll.innerHTML = `<span class="spinner"></span> <span>Posting All...</span>`;
    showToast('Executing 1-click publishing across all brands...');
    try {
      const res = await fetch('/api/folder-queue/publish-all', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Master publish failed');
      showToast(`Master publish complete: ${data.published_count} brands posted!`);
      loadBrandFolders();
    } catch (err) {
      showToast(`Master publish error: ${err.message}`, 'error');
    } finally {
      btnMasterPostAll.disabled = false;
      btnMasterPostAll.innerHTML = `<span>🚀 Post All</span>`;
    }
  });
}

if (btnOpenAllFolders) {
  btnOpenAllFolders.addEventListener('click', async () => {
    try {
      await fetch('/api/folder-queue/open-all-folders', { method: 'POST' });
    } catch (err) {
      showToast(`Could not open root folder: ${err.message}`, 'error');
    }
  });
}

// 4. Visual Content Planner & Calendar
async function loadCalendarPosts() {
  try {
    const res = await fetch(`/api/posts${currentBrandId ? `?brand_id=${currentBrandId}` : ''}`);
    if (res.ok) {
      scheduledPostsCache = await res.json();
    }
  } catch (err) {
    console.error('Error fetching calendar posts:', err);
  }
  renderCalendar();
}

function renderCalendar() {
  const titleEl = document.getElementById('calCurrentMonthTitle');
  const gridEl = document.getElementById('calendarDaysGrid');
  if (!gridEl) return;

  const year = currentCalendarDate.getFullYear();
  const month = currentCalendarDate.getMonth();
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  if (titleEl) {
    titleEl.textContent = `${monthNames[month]} ${year}`;
  }

  // Calculate day cells
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  // Monday = 0, Sunday = 6
  let startingDayOfWeek = firstDay.getDay() - 1;
  if (startingDayOfWeek === -1) startingDayOfWeek = 6;

  const totalDays = lastDay.getDate();
  const prevMonthLastDay = new Date(year, month, 0).getDate();

  let cellsHtml = '';

  // Previous month trailing days
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    const dayNum = prevMonthLastDay - i;
    cellsHtml += `
      <div class="calendar-day-cell other-month">
        <div class="day-cell-header"><span class="day-number">${dayNum}</span></div>
      </div>
    `;
  }

  const today = new Date();
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;

  // Current month days
  for (let day = 1; day <= totalDays; day++) {
    const isToday = isCurrentMonth && today.getDate() === day;
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    // Filter posts on this day
    const dayPosts = scheduledPostsCache.filter(p => p.scheduled_time.startsWith(dateStr));
    const postsHtml = dayPosts.map(p => `
      <div class="cal-post-chip status-${p.status}" onclick="viewPostDetails('${p.id}')" title="${p.caption}">
        ${p.post_type === 'reel' ? '🎬' : '📷'} ${p.scheduled_time.substring(11, 16)} &bull; ${p.caption.substring(0, 16)}...
      </div>
    `).join('');

    cellsHtml += `
      <div class="calendar-day-cell ${isToday ? 'today' : ''}">
        <div class="day-cell-header">
          <span class="day-number">${day}</span>
          ${dayPosts.length > 0 ? `<span style="font-size: 0.65rem; color: #38bdf8; font-weight: 700;">${dayPosts.length}</span>` : ''}
        </div>
        ${postsHtml}
      </div>
    `;
  }

  gridEl.innerHTML = cellsHtml;
}

const btnCalPrev = document.getElementById('btnCalPrev');
const btnCalNext = document.getElementById('btnCalNext');
const btnCalToday = document.getElementById('btnCalToday');

if (btnCalPrev) btnCalPrev.addEventListener('click', () => {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
  renderCalendar();
});
if (btnCalNext) btnCalNext.addEventListener('click', () => {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
  renderCalendar();
});
if (btnCalToday) btnCalToday.addEventListener('click', () => {
  currentCalendarDate = new Date();
  renderCalendar();
});

// Post Details Inspector for Calendar Planner
window.viewPostDetails = async function(postId) {
  let post = scheduledPostsCache.find(p => p.id === postId);
  if (!post) {
    try {
      const res = await fetch(`/api/posts/${postId}`);
      if (res.ok) post = await res.json();
    } catch (e) {
      // ignore
    }
  }

  const modal = document.getElementById('modalPostDetail');
  const body = document.getElementById('postDetailBody');
  const title = document.getElementById('postDetailTitle');
  if (!modal || !body) return;

  if (!post) {
    showToast('Post details not found', 'error');
    return;
  }

  if (title) title.textContent = `${post.post_type.toUpperCase()} • ${post.status.toUpperCase()}`;

  const mediaFile = post.media_paths && post.media_paths[0] ? post.media_paths[0].split(/[\\\\/]/).pop() : 'No file';

  body.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 14px;">
      <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 1.6rem;">${post.post_type === 'reel' ? '🎬' : (post.post_type === 'story' ? '📱' : '📷')}</span>
          <div>
            <div style="font-weight: 700; color: #fff;">${post.account_handle ? '@' + post.account_handle : (post.brand_name || 'Brand Post')}</div>
            <div style="font-size: 0.75rem; color: var(--text-secondary); font-family: var(--font-mono);">${post.scheduled_time.replace('T', ' ')}</div>
          </div>
        </div>
        <span class="badge-status ${post.status}" style="font-size: 0.78rem; padding: 4px 10px;">${post.status}</span>
      </div>

      <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 12px;">
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 6px;">Caption</div>
        <div style="font-size: 0.88rem; color: #e2e8f0; white-space: pre-wrap; word-break: break-word;">${post.caption || '<em style="color: var(--text-muted);">No caption</em>'}</div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.8rem;">
        <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 10px;">
          <span style="color: var(--text-secondary); display: block; font-size: 0.72rem; margin-bottom: 2px;">MEDIA FILE</span>
          <span style="font-family: var(--font-mono); color: #38bdf8;" title="${post.media_paths?.[0] || ''}">${mediaFile}</span>
        </div>
        <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 10px;">
          <span style="color: var(--text-secondary); display: block; font-size: 0.72rem; margin-bottom: 2px;">AUDIO ATTACHMENT</span>
          <span style="color: #a7f3d0;">${post.music_query ? '🎵 ' + post.music_query : 'Original Audio'} ${post.music_volume !== null && post.music_volume !== undefined ? `(Vol: ${post.music_volume})` : ''}</span>
        </div>
      </div>

      ${post.first_comment ? `
        <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 10px; font-size: 0.8rem;">
          <strong style="color: #38bdf8; display: block; margin-bottom: 4px;">💬 Auto First Comment:</strong>
          <span>${post.first_comment}</span>
        </div>
      ` : ''}

      ${post.published_url ? `
        <div style="margin-top: 4px;">
          <a href="${post.published_url}" target="_blank" class="btn btn-primary" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none;">
            <span>Open on Instagram &rarr;</span>
          </a>
        </div>
      ` : ''}

      ${post.error_message ? `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 10px; color: #fca5a5; font-size: 0.8rem;">
          <strong>Error:</strong> ${post.error_message}
        </div>
      ` : ''}

      <div style="display: flex; gap: 10px; margin-top: 8px; border-top: 1px solid var(--border-subtle); padding-top: 14px;">
        ${post.status !== 'published' ? `
          <button type="button" class="btn btn-primary" style="flex: 2;" onclick="publishPostImmediately('${post.id}'); closeModal(document.getElementById('modalPostDetail'));">
            <span>🚀 Publish Now</span>
          </button>
        ` : ''}
        <button type="button" class="btn btn-danger-ghost" style="flex: 1;" onclick="deleteQueuePost('${post.id}'); closeModal(document.getElementById('modalPostDetail'));">
          🗑️ Delete
        </button>
      </div>
    </div>
  `;

  openModal(modal);
};

// 5. Visual Feed 9-Grid Preview
async function loadFeedPreview() {
  const container = document.getElementById('feedGridPreview');
  const handleEl = document.getElementById('feedMockHandle');
  if (!container) return;

  const brand = allBrands.find(b => b.id === currentBrandId) || allBrands[0];
  if (handleEl && brand) {
    const profile = brand.profiles[0];
    handleEl.textContent = profile ? `@${profile.account_handle}` : `@${brand.name}`;
  }

  try {
    const res = await fetch(`/api/posts${currentBrandId ? `?brand_id=${currentBrandId}` : ''}`);
    const posts = res.ok ? await res.json() : [];

    // Slice 9 latest
    const feedItems = posts.slice(0, 9);
    let tilesHtml = '';

    for (let i = 0; i < 9; i++) {
      const item = feedItems[i];
      if (item && item.media_paths && item.media_paths.length > 0) {
        const isVideo = item.post_type === 'reel';
        tilesHtml += `
          <div class="feed-tile">
            ${isVideo 
              ? `<div style="font-size: 2rem;">🎬</div>`
              : `<div style="font-size: 2rem;">📷</div>`
            }
            <span class="feed-tile-badge">${isVideo ? '▶' : '🖼'}</span>
          </div>
        `;
      } else {
        tilesHtml += `
          <div class="feed-tile" style="opacity: 0.25;">
            <span style="font-size: 0.8rem; color: #71717a;">Slot ${i + 1}</span>
          </div>
        `;
      }
    }

    container.innerHTML = tilesHtml;
  } catch (err) {
    container.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Could not load feed preview.</div>';
  }
}

// 6. Evergreen Content Pool
async function loadEvergreenPool() {
  const grid = document.getElementById('evergreenGrid');
  if (!grid) return;

  grid.innerHTML = '<div style="color: var(--text-secondary); padding: 20px;">Loading evergreen vault...</div>';

  try {
    const res = await fetch(`/api/evergreen${currentBrandId ? `?brand_id=${currentBrandId}` : ''}`);
    if (!res.ok) throw new Error('Failed to load evergreen pool');
    const items = await res.json();

    if (items.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Evergreen pool is empty. Click "+ Add Evergreen Post" to seed content.</div>';
      return;
    }

    grid.innerHTML = items.map(p => `
      <div class="brand-folder-card">
        <div class="brand-card-header">
          <span style="font-weight: 700; color: #fff;">♻️ Recycled Post</span>
          <span class="badge-status scheduled">${p.times_posted} / ${p.max_repeats} Used</span>
        </div>

        <p style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.4;">
          ${p.caption}
        </p>

        <div style="font-size: 0.75rem; color: var(--text-secondary); font-family: var(--font-mono);">
          Media: ${p.media_paths && p.media_paths[0] ? p.media_paths[0].split(/[\\\\/]/).pop() : 'None'}
        </div>

        <div style="margin-top: auto; display: flex; justify-content: flex-end;">
          <button type="button" class="btn btn-danger-ghost" style="font-size: 0.75rem;" onclick="deleteEvergreenPost('${p.id}')">
            Delete
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div style="color: var(--accent-red); padding: 20px;">Error: ${err.message}</div>`;
  }
}

async function deleteEvergreenPost(id) {
  if (!confirm('Remove this post from evergreen recycling?')) return;
  try {
    const res = await fetch(`/api/evergreen/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete');
    showToast('Removed from evergreen pool');
    loadEvergreenPool();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

if (btnAutoFillQueue) {
  btnAutoFillQueue.addEventListener('click', async () => {
    if (!currentBrandId) return;
    btnAutoFillQueue.disabled = true;
    showToast('Scanning schedule gaps and refilling with evergreen posts...');
    try {
      const res = await fetch('/api/evergreen/auto-fill-queue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_id: currentBrandId,
          days_ahead: 7,
          preferred_time: '19:30',
          min_cooldown_days: 14
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Auto-fill failed');
      showToast(`Auto-fill result: ${data.message}`);
      loadCalendarPosts();
    } catch (err) {
      showToast(`Auto-fill error: ${err.message}`, 'error');
    } finally {
      btnAutoFillQueue.disabled = false;
    }
  });
}

// 7. Queue Table
async function loadQueuePosts() {
  const container = document.getElementById('queueTableContainer');
  if (!container) return;

  container.innerHTML = '<div style="color: var(--text-secondary); padding: 20px;">Loading queue...</div>';

  try {
    const res = await fetch(`/api/posts${currentBrandId ? `?brand_id=${currentBrandId}` : ''}`);
    if (!res.ok) throw new Error('Failed to fetch posts');
    const posts = await res.json();

    if (posts.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No scheduled posts in queue.</div>';
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Caption</th>
            <th>Media</th>
            <th>Scheduled Time</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${posts.map(p => `
            <tr>
              <td><strong>${p.post_type.toUpperCase()}</strong></td>
              <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${p.caption}">
                ${p.caption || '<em>No caption</em>'}
              </td>
              <td style="font-family: var(--font-mono); font-size: 0.75rem;">
                ${p.media_paths && p.media_paths[0] ? p.media_paths[0].split(/[\\\\/]/).pop() : 'None'}
              </td>
              <td style="font-family: var(--font-mono); font-size: 0.78rem;">
                ${p.scheduled_time.replace('T', ' ')}
              </td>
              <td>
                <span class="badge-status ${p.status}">${p.status}</span>
              </td>
              <td>
                <div style="display: flex; gap: 6px;">
                  ${p.status !== 'published' ? `
                    <button type="button" class="btn btn-secondary" style="font-size: 0.72rem; padding: 4px 8px;" onclick="publishPostImmediately('${p.id}')">
                      🚀 Now
                    </button>
                  ` : ''}
                  ${p.status === 'failed' ? `
                    <button type="button" class="btn btn-secondary" style="font-size: 0.72rem; padding: 4px 8px;" onclick="retryQueuePost('${p.id}')">
                      🔄 Retry
                    </button>
                  ` : ''}
                  <button type="button" class="btn btn-danger-ghost" style="font-size: 0.72rem; padding: 4px 8px;" onclick="deleteQueuePost('${p.id}')">
                    ✕
                  </button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-red); padding: 20px;">Error: ${err.message}</div>`;
  }
}

async function publishPostImmediately(id) {
  showToast('Publishing post immediately...');
  try {
    const res = await fetch(`/api/posts/${id}/publish-now`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Publish failed');
    showToast('Post published successfully!');
    loadQueuePosts();
    loadCalendarPosts();
  } catch (err) {
    showToast(`Publish error: ${err.message}`, 'error');
  }
}

async function retryQueuePost(id) {
  try {
    const res = await fetch(`/api/posts/${id}/retry`, { method: 'POST' });
    if (!res.ok) throw new Error('Retry failed');
    showToast('Post reset to scheduled queue');
    loadQueuePosts();
  } catch (err) {
    showToast(`Retry error: ${err.message}`, 'error');
  }
}

async function deleteQueuePost(id) {
  if (!confirm('Delete this scheduled post?')) return;
  try {
    const res = await fetch(`/api/posts/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');
    showToast('Post deleted');
    loadQueuePosts();
    loadCalendarPosts();
  } catch (err) {
    showToast(`Delete error: ${err.message}`, 'error');
  }
}

// 8. Analytics Dashboard
async function loadAnalytics() {
  const kpiRow = document.getElementById('analyticsKpiRow');
  const recentLogs = document.getElementById('analyticsRecentLogs');

  try {
    const res = await fetch(`/api/analytics/summary${currentBrandId ? `?brand_id=${currentBrandId}` : ''}`);
    if (!res.ok) throw new Error('Failed to load analytics');
    const data = await res.json();
    const s = data.summary;

    if (kpiRow) {
      kpiRow.innerHTML = `
        <div class="hero-kpi-pill">
          <span class="kpi-icon">🚀</span>
          <div>
            <div class="kpi-val">${s.total_published}</div>
            <div class="kpi-title">Total Published</div>
          </div>
        </div>
        <div class="hero-kpi-pill">
          <span class="kpi-icon">🎬</span>
          <div>
            <div class="kpi-val">${s.reels_count}</div>
            <div class="kpi-title">Reels</div>
          </div>
        </div>
        <div class="hero-kpi-pill">
          <span class="kpi-icon">📸</span>
          <div>
            <div class="kpi-val">${s.posts_count}</div>
            <div class="kpi-title">Feed Posts</div>
          </div>
        </div>
        <div class="hero-kpi-pill">
          <span class="kpi-icon">⏳</span>
          <div>
            <div class="kpi-val">${s.scheduled_in_queue}</div>
            <div class="kpi-title">In Queue</div>
          </div>
        </div>
        <div class="hero-kpi-pill">
          <span class="kpi-icon">⚡</span>
          <div>
            <div class="kpi-val">${s.engagement_rate}%</div>
            <div class="kpi-title">Engagement Rate</div>
          </div>
        </div>
      `;
    }

    if (recentLogs) {
      if (!data.recent_posts || data.recent_posts.length === 0) {
        recentLogs.innerHTML = '<div style="color: var(--text-muted); padding: 16px;">No posts published yet.</div>';
      } else {
        recentLogs.innerHTML = `
          <table class="data-table">
            <thead>
              <tr>
                <th>Account</th>
                <th>Type</th>
                <th>Post URL</th>
                <th>Timestamp</th>
                <th>Proxy Used</th>
              </tr>
            </thead>
            <tbody>
              ${data.recent_posts.map(p => `
                <tr>
                  <td><strong>@${p.username}</strong></td>
                  <td>${p.media_type.toUpperCase()}</td>
                  <td>
                    <a href="${p.url}" target="_blank" style="color: #38bdf8; text-decoration: underline;">
                      ${p.url}
                    </a>
                  </td>
                  <td style="font-family: var(--font-mono); font-size: 0.75rem;">${p.created_at.substring(0, 19).replace('T', ' ')}</td>
                  <td style="font-family: var(--font-mono); font-size: 0.75rem;">${p.proxy_used ? p.proxy_used.substring(0, 24) + '...' : '<span style="color: #71717a;">Direct</span>'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }
    }
  } catch (err) {
    console.error('Analytics error:', err);
  }
}

// 9. Brand & Evergreen Modal Handlers
if (btnOpenAddBrand) btnOpenAddBrand.addEventListener('click', () => openModal(modalAddBrand));
if (btnOpenCsvModal) btnOpenCsvModal.addEventListener('click', () => openModal(modalCsvImport));
if (btnOpenAddEvergreen) btnOpenAddEvergreen.addEventListener('click', () => {
  populateBrandSelects();
  openModal(modalAddEvergreen);
});

const formCreateBrand = document.getElementById('formCreateBrand');
if (formCreateBrand) {
  formCreateBrand.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('brandNameInput').value.trim();
    const color = document.getElementById('brandColorInput').value;
    const desc = document.getElementById('brandDescInput').value.trim();

    try {
      const res = await fetch('/api/brands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, color_badge: color, description: desc })
      });
      if (!res.ok) throw new Error('Failed to create brand');
      showToast(`Brand '${name}' created!`);
      closeModal(modalAddBrand);
      formCreateBrand.reset();
      await fetchBrands();
      loadBrandFolders();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

const formAddEvergreen = document.getElementById('formAddEvergreen');
if (formAddEvergreen) {
  formAddEvergreen.addEventListener('submit', async (e) => {
    e.preventDefault();
    const brandId = document.getElementById('evergreenBrandSelect').value;
    const mediaPath = document.getElementById('evergreenMediaInput').value.trim();
    const caption = document.getElementById('evergreenCaption').value.trim();
    const maxRepeats = parseInt(document.getElementById('evergreenMaxRepeats').value) || 3;

    try {
      const res = await fetch('/api/evergreen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_id: brandId,
          caption: caption,
          media_paths: [mediaPath],
          max_repeats: maxRepeats
        })
      });
      if (!res.ok) throw new Error('Failed to save evergreen post');
      showToast('Added to evergreen pool!');
      closeModal(modalAddEvergreen);
      formAddEvergreen.reset();
      loadEvergreenPool();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// 10. CSV Bulk Importer Logic
const formCsvValidate = document.getElementById('formCsvValidate');
const csvTextInput = document.getElementById('csvTextInput');
const csvFileInput = document.getElementById('csvFileInput');
let validatedCsvPosts = [];

if (csvFileInput) {
  csvFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        csvTextInput.value = event.target.result;
      };
      reader.readAsText(file);
    }
  });
}

if (formCsvValidate) {
  formCsvValidate.addEventListener('submit', async (e) => {
    e.preventDefault();
    const reportArea = document.getElementById('csvValidationReportArea');
    const btnVal = document.getElementById('btnValidateCsv');
    reportArea.style.display = 'block';
    reportArea.innerHTML = '<div style="color: var(--text-secondary);"><span class="spinner"></span> Validating CSV schema and media paths...</div>';
    btnVal.disabled = true;

    try {
      const res = await fetch('/api/posts/csv-validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csv_text: csvTextInput.value,
          brand_id: currentBrandId
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Validation failed');

      validatedCsvPosts = data.posts;

      reportArea.innerHTML = `
        <div style="background: rgba(18, 20, 29, 0.9); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
            <div>
              <strong>Pre-Flight Report:</strong> Detected Schema: <code>${data.detected_format}</code> &bull; 
              <span style="color: #34d399;">${data.valid_rows}/${data.total_rows} Rows Valid</span>
            </div>
            <button type="button" class="btn btn-primary" id="btnExecuteCsvImport" ${data.valid_rows === 0 ? 'disabled' : ''}>
              <span>🚀 Import ${data.valid_rows} Valid Posts into Planner</span>
            </button>
          </div>

          <div class="table-responsive" style="max-height: 320px; overflow-y: auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Brand</th>
                  <th>Date & Time</th>
                  <th>Media</th>
                  <th>Caption</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${data.posts.map(p => `
                  <tr>
                    <td>#${p.row_index}</td>
                    <td><strong>${p.brand_name || 'Unassigned'}</strong></td>
                    <td style="font-family: var(--font-mono); font-size: 0.75rem;">${p.date} ${p.time}</td>
                    <td style="font-size: 0.75rem; font-family: var(--font-mono);">${p.media_path ? p.media_path.split(/[\\\\/]/).pop() : '<span style="color: #f87171;">Missing</span>'}</td>
                    <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${p.caption || '<em>None</em>'}</td>
                    <td>
                      <span class="badge-status ${p.status === 'success' ? 'published' : (p.status === 'warning' ? 'draft' : 'failed')}">
                        ${p.status}
                      </span>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;

      const btnExec = document.getElementById('btnExecuteCsvImport');
      if (btnExec) {
        btnExec.addEventListener('click', async () => {
          btnExec.disabled = true;
          btnExec.innerHTML = `<span class="spinner"></span> <span>Importing...</span>`;
          try {
            const impRes = await fetch('/api/posts/csv-import', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ posts: validatedCsvPosts })
            });
            const impData = await impRes.json();
            if (!impRes.ok) throw new Error(impData.detail || 'Import failed');
            showToast(`Imported ${impData.imported_count} posts successfully!`);
            closeModal(modalCsvImport);
            loadCalendarPosts();
            loadQueuePosts();
          } catch (iErr) {
            showToast(iErr.message, 'error');
            btnExec.disabled = false;
            btnExec.innerHTML = `<span>🚀 Import Valid Posts</span>`;
          }
        });
      }

    } catch (err) {
      reportArea.innerHTML = `<div style="color: var(--accent-red); padding: 12px;">Validation Error: ${err.message}</div>`;
    } finally {
      btnVal.disabled = false;
    }
  });
}

// ==========================================
// Search & Filter Listeners for Accounts
// ==========================================
if (searchInput) searchInput.addEventListener('input', () => renderAccounts());

document.querySelectorAll('.filter-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    currentFilter = pill.getAttribute('data-filter');
    renderAccounts();
  });
});

if (btnRefresh) btnRefresh.addEventListener('click', () => fetchAccounts());

// Initial Page Load
document.addEventListener('DOMContentLoaded', async () => {
  await fetchBrands();
  updateWorkspaceDot();
  initComposerLivePreview();

  // Resolve initial tab from current URL pathname
  let initialTab = window.location.pathname.replace(/^\/+/, '').split('/')[0] || 'planner';
  if (initialTab === 'vault') initialTab = 'folders';
  if (!['planner', 'analytics', 'folders', 'queue', 'accounts', 'engagement'].includes(initialTab)) {
    initialTab = 'planner';
  }

  // Switch to initial tab and sync URL
  switchTab(initialTab, window.location.pathname === '/' || window.location.pathname === '');
});

function initComposerLivePreview() {
  const captionInput = document.getElementById('uploadCaption');
  const accountSelect = document.getElementById('uploadAccountSelect');
  const musicQuery = document.getElementById('uploadMusicQuery');
  const mockHandle = document.getElementById('mockPreviewHandle');
  const mockCaption = document.getElementById('mockPreviewCaption');
  const mockAudio = document.getElementById('mockPreviewAudio');
  const mockMedia = document.getElementById('mockPreviewMedia');
  const fileInput = document.getElementById('mediaFileInput');

  function updatePreview() {
    if (mockHandle && accountSelect) {
      mockHandle.textContent = accountSelect.value ? `@${accountSelect.value}` : '@your_account';
    }
    if (mockCaption && captionInput) {
      const txt = captionInput.value.trim();
      mockCaption.textContent = txt || 'Your caption and hashtags will appear here in real-time...';
    }
    if (mockAudio && musicQuery) {
      const q = musicQuery.value.trim();
      mockAudio.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
        <span>${q ? q : 'Original Audio'}</span>
      `;
    }
  }

  if (captionInput) captionInput.addEventListener('input', updatePreview);
  if (accountSelect) accountSelect.addEventListener('change', updatePreview);
  if (musicQuery) musicQuery.addEventListener('input', updatePreview);

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      const file = fileInput.files?.[0];
      if (file && mockMedia) {
        if (file.type.startsWith('image/')) {
          const url = URL.createObjectURL(file);
          mockMedia.innerHTML = `<img src="${url}" style="width:100%;height:100%;object-fit:cover;">`;
        } else if (file.type.startsWith('video/')) {
          const url = URL.createObjectURL(file);
          mockMedia.innerHTML = `<video src="${url}" autoplay muted loop playsinline style="width:100%;height:100%;object-fit:cover;"></video>`;
        }
      }
    });
  }
}

// ==============================================================================
// 11. ENGAGEMENT FARMING SWARM CONTROLLER
// ==============================================================================
let engagementRecentPostsCache = [];
let engagementResolvedPost = null;
let engagementControlsInitialized = false;

async function loadEngagementView() {
  await loadRecentPostsDropdown();
  await renderSwarmAccountsList();
  initEngagementControls();
}

async function loadRecentPostsDropdown() {
  const select = document.getElementById('selectRecentPost');
  if (!select) return;
  try {
    const res = await fetch('/api/engagement/recent-posts');
    if (!res.ok) throw new Error('Failed to load recent posts');
    engagementRecentPostsCache = await res.json();

    if (engagementRecentPostsCache.length === 0) {
      select.innerHTML = '<option value="">-- No published posts in history yet --</option>';
      return;
    }

    select.innerHTML = '<option value="">-- Choose from recently published posts --</option>' +
      engagementRecentPostsCache.map(p => {
        const title = p.caption ? p.caption.slice(0, 48) + '...' : p.url;
        return `<option value="${p.url}">[${p.source}] ${p.username}: ${title}</option>`;
      }).join('');
  } catch (err) {
    console.error('Error fetching recent posts for engagement:', err);
  }
}

async function renderSwarmAccountsList() {
  const container = document.getElementById('swarmAccountsList');
  if (!container) return;

  if (allAccounts.length === 0) {
    try {
      const res = await fetch('/accounts', { headers: { 'Accept': 'application/json' } });
      if (res.ok) allAccounts = await res.json();
    } catch (e) {}
  }

  if (allAccounts.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); padding: 20px; text-align: center;">No connected Instagram accounts found.</div>';
    return;
  }

  container.innerHTML = allAccounts.map(acc => {
    const initial = (acc.full_name || acc.username).charAt(0).toUpperCase();
    const avatarHtml = acc.profile_pic_url
      ? `<img src="${acc.profile_pic_url}" alt="${acc.username}" class="swarm-account-avatar" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'avatar-fallback\\' style=\\'width:32px;height:32px;font-size:0.8rem;\\'>${initial}</div>'">`
      : `<div class="avatar-fallback" style="width:32px;height:32px;font-size:0.8rem;">${initial}</div>`;

    const proxyText = acc.proxy ? maskProxy(acc.proxy) : 'Direct IP';
    const isAuth = acc.is_authenticated;

    return `
      <label class="swarm-account-item">
        <div class="swarm-account-left">
          <input type="checkbox" class="swarm-account-checkbox" value="${acc.username}" ${isAuth ? 'checked' : ''}>
          ${avatarHtml}
          <div>
            <div class="swarm-account-name">@${acc.username}</div>
            <div class="swarm-account-proxy">
              <span>🌐</span>
              <span>${proxyText}</span>
              ${!isAuth ? '<span style="color:#ef4444; margin-left:4px;">(Offline)</span>' : ''}
            </div>
          </div>
        </div>
        <span class="session-status-badge ${isAuth ? 'active' : 'expired'}">${isAuth ? 'Ready' : 'Expired'}</span>
      </label>
    `;
  }).join('');
}

function initEngagementControls() {
  if (engagementControlsInitialized) return;
  engagementControlsInitialized = true;

  const selectRecent = document.getElementById('selectRecentPost');
  const inputUrl = document.getElementById('inputEngagementUrl');
  const btnResolve = document.getElementById('btnResolvePost');
  const btnRefreshRecent = document.getElementById('btnRefreshRecentPosts');
  const btnSelectAll = document.getElementById('btnSelectAllAccounts');
  const btnDeselectAll = document.getElementById('btnDeselectAllAccounts');
  const btnLaunch = document.getElementById('btnLaunchSwarm');
  const delaySlider = document.getElementById('inputSafetyDelay');
  const delayDisplay = document.getElementById('delayDisplay');

  // Action chips
  const actionCheckboxes = [
    { chip: 'chipLike', check: 'checkActionLike' },
    { chip: 'chipSave', check: 'checkActionSave' },
    { chip: 'chipComment', check: 'checkActionComment' },
    { chip: 'chipFollow', check: 'checkActionFollow' },
    { chip: 'chipRepost', check: 'checkActionRepost' }
  ];

  actionCheckboxes.forEach(({ chip, check }) => {
    const chipEl = document.getElementById(chip);
    const checkEl = document.getElementById(check);
    if (chipEl && checkEl) {
      checkEl.addEventListener('change', () => {
        if (checkEl.checked) chipEl.classList.add('active');
        else chipEl.classList.remove('active');

        // Toggle visibility of comment rotation box
        if (check === 'checkActionComment') {
          const comGroup = document.getElementById('commentsRotationGroup');
          if (comGroup) comGroup.style.display = checkEl.checked ? 'block' : 'none';
        }
        // Toggle visibility of repost caption box
        if (check === 'checkActionRepost') {
          const repGroup = document.getElementById('repostCaptionGroup');
          if (repGroup) repGroup.style.display = checkEl.checked ? 'block' : 'none';
        }
      });
    }
  });

  if (delaySlider && delayDisplay) {
    delaySlider.addEventListener('input', () => {
      delayDisplay.textContent = parseFloat(delaySlider.value).toFixed(1) + 's';
    });
  }

  if (btnRefreshRecent) {
    btnRefreshRecent.addEventListener('click', async () => {
      await loadRecentPostsDropdown();
      showToast('Refreshed published posts list');
    });
  }

  if (selectRecent) {
    selectRecent.addEventListener('change', () => {
      if (selectRecent.value && inputUrl) {
        inputUrl.value = selectRecent.value;
        resolvePostUrl(selectRecent.value);
      }
    });
  }

  if (btnResolve) {
    btnResolve.addEventListener('click', () => {
      const url = inputUrl ? inputUrl.value.trim() : '';
      if (!url) {
        showToast('Please enter an Instagram post or reel URL', 'error');
        return;
      }
      resolvePostUrl(url);
    });
  }

  if (btnSelectAll) {
    btnSelectAll.addEventListener('click', () => {
      document.querySelectorAll('.swarm-account-checkbox').forEach(cb => cb.checked = true);
    });
  }

  if (btnDeselectAll) {
    btnDeselectAll.addEventListener('click', () => {
      document.querySelectorAll('.swarm-account-checkbox').forEach(cb => cb.checked = false);
    });
  }

  if (btnLaunch) {
    btnLaunch.addEventListener('click', launchEngagementSwarm);
  }
}

async function resolvePostUrl(url) {
  const previewBox = document.getElementById('targetPostPreview');
  const btnResolve = document.getElementById('btnResolvePost');
  if (!previewBox) return;

  previewBox.style.display = 'flex';
  previewBox.innerHTML = `
    <div style="display:flex; align-items:center; gap:10px; padding:10px; color:var(--text-secondary);">
      <span class="spinner" style="width:20px;height:20px;border-width:2px;"></span>
      <span>Inspecting post metadata on Instagram...</span>
    </div>
  `;

  if (btnResolve) btnResolve.disabled = true;

  try {
    const res = await fetch('/api/engagement/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_url: url })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not resolve Instagram post');

    engagementResolvedPost = data;

    const thumbHtml = data.thumbnail_url
      ? `<img src="${data.thumbnail_url}" alt="Post thumbnail" class="preview-thumb">`
      : `<div class="preview-thumb-placeholder"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg></div>`;

    previewBox.innerHTML = `
      ${thumbHtml}
      <div class="preview-info">
        <div>
          <div class="preview-author-row">
            <span class="preview-author-handle">@${data.author_username}</span>
            <span class="preview-type-badge">${data.is_reel ? 'Reel / Video' : 'Photo Post'}</span>
          </div>
          <div class="preview-caption-snippet">${data.caption || '<em>No caption</em>'}</div>
        </div>
        <div class="preview-metrics-row">
          <span>❤️ ${formatNumber(data.like_count)} Likes</span>
          <span>💬 ${formatNumber(data.comment_count)} Comments</span>
          <span style="color:#6366f1;">PK: ${data.media_pk}</span>
        </div>
      </div>
    `;
  } catch (err) {
    engagementResolvedPost = null;
    previewBox.innerHTML = `
      <div style="color:var(--accent-red); font-size:0.85rem; padding:8px;">
        ⚠️ ${err.message}
      </div>
    `;
  } finally {
    if (btnResolve) btnResolve.disabled = false;
  }
}

async function launchEngagementSwarm() {
  const inputUrl = document.getElementById('inputEngagementUrl');
  const targetUrl = (inputUrl ? inputUrl.value : '').trim();
  if (!targetUrl) {
    showToast('Please enter or select a target Instagram post / reel URL.', 'error');
    return;
  }

  // Selected accounts
  const selectedAccounts = [];
  document.querySelectorAll('.swarm-account-checkbox:checked').forEach(cb => {
    selectedAccounts.push(cb.value);
  });

  if (selectedAccounts.length === 0) {
    showToast('Please select at least one account to perform engagement.', 'error');
    return;
  }

  // Selected actions
  const actions = [];
  if (document.getElementById('checkActionLike')?.checked) actions.push('like');
  if (document.getElementById('checkActionSave')?.checked) actions.push('save');
  if (document.getElementById('checkActionComment')?.checked) actions.push('comment');
  if (document.getElementById('checkActionFollow')?.checked) actions.push('follow');
  if (document.getElementById('checkActionRepost')?.checked) actions.push('repost');

  if (actions.length === 0) {
    showToast('Please select at least one action (Like, Save, Comment, Follow, or Repost).', 'error');
    return;
  }

  // Comments pool
  const commentsRaw = document.getElementById('textareaComments')?.value || '';
  const commentTexts = commentsRaw.split('\n').map(c => c.trim()).filter(Boolean);

  // Repost caption
  const repostCaption = document.getElementById('inputRepostCaption')?.value.trim() || null;

  // Delay
  const delaySlider = document.getElementById('inputSafetyDelay');
  const delaySeconds = delaySlider ? parseFloat(delaySlider.value) : 4.0;

  const btnLaunch = document.getElementById('btnLaunchSwarm');
  const reportSec = document.getElementById('engagementReportSection');

  btnLaunch.disabled = true;
  btnLaunch.innerHTML = `<span class="spinner" style="width:18px;height:18px;border-width:2.5px;"></span> <span>Running Swarm across ${selectedAccounts.length} accounts...</span>`;

  if (reportSec) {
    reportSec.style.display = 'block';
    reportSec.innerHTML = `
      <div class="report-card" style="text-align: center; padding: 40px 20px;">
        <div class="spinner" style="width: 32px; height: 32px; border-width: 3px; margin: 0 auto 16px auto;"></div>
        <h3 style="color: #fff; font-size: 1.1rem; margin-bottom: 8px;">Swarm Execution in Progress</h3>
        <p style="color: var(--text-secondary); font-size: 0.85rem; max-width: 500px; margin: 0 auto;">
          Executing ${actions.join(', ').toUpperCase()} with proxies and ${delaySeconds}s human pacing...
        </p>
      </div>
    `;
    reportSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  try {
    const res = await fetch('/api/engagement/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_url: targetUrl,
        accounts: selectedAccounts,
        actions: actions,
        comment_texts: commentTexts,
        repost_caption: repostCaption,
        delay_seconds: delaySeconds
      })
    });
    const report = await res.json();
    if (!res.ok) throw new Error(report.detail || 'Engagement swarm failed');

    renderEngagementReport(report);
    showToast(`Swarm completed: ${report.passed_count} passed, ${report.skipped_count} skipped, ${report.failed_count} failed.`);
  } catch (err) {
    showToast(`Swarm Error: ${err.message}`, 'error');
    if (reportSec) {
      reportSec.innerHTML = `
        <div class="report-card" style="border-color: rgba(239, 68, 68, 0.4);">
          <h3 style="color: var(--accent-red); margin-bottom: 8px;">Swarm Execution Encountered Error</h3>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">${err.message}</p>
        </div>
      `;
    }
  } finally {
    btnLaunch.disabled = false;
    btnLaunch.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      <span>Launch Engagement Swarm</span>
    `;
  }
}

function renderEngagementReport(report) {
  const container = document.getElementById('engagementReportSection');
  if (!container) return;

  const accReports = report.account_reports || [];

  container.innerHTML = `
    <div class="report-card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 800; color: #fff; margin-bottom: 4px;">Engagement Swarm Completion Report</h2>
          <div style="font-size: 0.8rem; color: var(--text-secondary);">
            Target: <a href="${report.target_url}" target="_blank" style="color: #6366f1; text-decoration: underline;">${report.target_url}</a> &bull; Author: <strong>@${report.author_username}</strong>
          </div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">
          ${new Date(report.completed_at).toLocaleTimeString()}
        </div>
      </div>

      <div class="report-summary-bar">
        <div class="report-kpi passed">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <span>${report.passed_count} Passed</span>
        </div>
        <div class="report-kpi skipped">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 4 15 12 5 20 5 4"></polygon><line x1="19" y1="5" x2="19" y2="19"></line></svg>
          <span>${report.skipped_count} Skipped (Smart Checks)</span>
        </div>
        <div class="report-kpi failed">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          <span>${report.failed_count} Failed</span>
        </div>
        <div style="margin-left: auto; font-size: 0.82rem; color: #94a3b8;">
          Total Participating Accounts: <strong>${report.total_accounts}</strong>
        </div>
      </div>

      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th>Account</th>
              <th>Assigned Proxy</th>
              <th>Actions Breakdown</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${accReports.map(ar => {
              const actionEntries = Object.entries(ar.actions || {});
              return `
                <tr>
                  <td>
                    <strong>@${ar.username}</strong>
                  </td>
                  <td style="font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8;">
                    ${ar.proxy ? maskProxy(ar.proxy) : 'Direct'}
                  </td>
                  <td>
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                      ${actionEntries.map(([act, res]) => {
                        const actName = act.toUpperCase();
                        let badgeClass = res.status === 'passed' ? 'passed' : (res.status === 'skipped' ? 'skipped' : 'failed');
                        let detailText = res.message || res.error || '';
                        if (res.new_url) {
                          detailText += ` &bull; <a href="${res.new_url}" target="_blank" style="color: #818cf8; text-decoration: underline;">View Reel</a>`;
                        }
                        return `
                          <div style="font-size: 0.77rem; display: flex; align-items: center; gap: 6px;">
                            <span class="report-pill ${badgeClass}">${actName}</span>
                            <span style="color: #cbd5e1;">${detailText}</span>
                          </div>
                        `;
                      }).join('')}
                    </div>
                  </td>
                  <td>
                    <span class="badge-status ${ar.overall_status === 'passed' ? 'published' : (ar.overall_status === 'partial' ? 'scheduled' : 'failed')}">
                      ${ar.overall_status}
                    </span>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


