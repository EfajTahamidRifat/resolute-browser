// Resolute Home. Copyright (c) 2026 Dewan Efaj Tahamid Rifat (The Code Bros). All rights reserved.
// Resolute's new tab page, shipped inside the browser as a component extension.
// Everything (XP, streak, quests) is stored on this device only. Nothing here is
// money or a token. Partner list: bundled partners.json, refreshed from GitHub.
'use strict';

const CONFIG_URL =
  'https://raw.githubusercontent.com/EfajTahamidRifat/resolute-browser/main/config/partners.json';
const ICON_BASE =
  'https://raw.githubusercontent.com/EfajTahamidRifat/resolute-browser/main/config/';

const hasChrome = typeof chrome !== 'undefined';
const $ = (id) => document.getElementById(id);

// ---------- storage (chrome.storage.local, or localStorage when previewed outside) ----------
const store = {
  async get() {
    try {
      if (hasChrome && chrome.storage && chrome.storage.local) {
        const r = await chrome.storage.local.get('home');
        return r.home || {};
      }
      return JSON.parse(localStorage.getItem('home') || '{}');
    } catch (e) { return {}; }
  },
  async set(v) {
    try {
      if (hasChrome && chrome.storage && chrome.storage.local) {
        await chrome.storage.local.set({ home: v });
      } else {
        localStorage.setItem('home', JSON.stringify(v));
      }
    } catch (e) { /* storage unavailable: page still works */ }
  },
};

// ---------- levels ----------
const LEVELS = [0, 50, 150, 300, 500, 800, 1200, 1700, 2300, 3000];
function levelFor(xp) {
  let lv = 1;
  for (let i = 0; i < LEVELS.length; i++) if (xp >= LEVELS[i]) lv = i + 1;
  if (xp >= LEVELS[LEVELS.length - 1]) lv += Math.floor((xp - LEVELS[LEVELS.length - 1]) / 1000);
  return lv;
}
function levelStart(lv) {
  return lv <= LEVELS.length ? LEVELS[lv - 1] : LEVELS[LEVELS.length - 1] + (lv - LEVELS.length) * 1000;
}
function rankFor(lv) {
  if (lv >= 10) return 'Legend';
  if (lv >= 6) return 'Captain';
  if (lv >= 3) return 'Navigator';
  return 'Explorer';
}

// ---------- dates ----------
function dayKey(d = new Date()) {
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}
function yesterdayKey() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return dayKey(d);
}

// ---------- quests ----------
const WALLET_IDS = new Set([
  'nkbihfbeogaeaoehlefnkodbefgpgknn', // MetaMask
  'bfnaelmomeimhlpmgjnjophhpkkoljpa', // Phantom
  'acmacodkjbdgmoleebolmdjonilkdbch', // Rabby
  'mcohilncbfahbmgdjkbpemcciiolgcge', // OKX Wallet
  'hnfanknocfeofbddgcijnmhnfnkdnaad', // Coinbase Wallet
  'egjidjbpglichdcondbcbdnbeeppgdph', // Trust Wallet
  'aflkmfhebedbjioipglgcbcmnbpgliof', // Backpack
  'bhhhlbepdkbapadjdnnojkbgioiodbic', // Solflare
]);
const ICONS = {
  sun: 'M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-3.5-3.5',
  compass: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM15.5 8.5l-2 5-5 2 2-5z',
  puzzle: 'M14 4h4v4h2v4h-2v6H6v-6H4V8h2V4h4v2h4z',
  wallet: 'M20 7H5a2 2 0 0 1 0-4h13v4M3 5v14a2 2 0 0 0 2 2h15V7M16 14h.01',
  check: 'm5 12 5 5 9-10',
  play: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM10 8.5v7l6-3.5z',
  makers: 'M8 9 4 12l4 3M16 9l4 3-4 3M13.5 6l-3 12',
  bulb: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z',
};
// The Code Bros links carry UTM tags so thecodebros.xyz can count visits from Resolute.
// Resolute itself tracks nothing (privacy policy).
const MAKERS_URL = 'https://thecodebros.xyz/?utm_source=resolute&utm_medium=app&utm_campaign=';
const QUESTS = [
  { id: 'open', daily: true, xp: 10, icon: 'sun', name: 'Open Resolute today', desc: 'Keeps your streak alive' },
  { id: 'search', daily: true, xp: 10, icon: 'search', name: 'Search the web', desc: 'From here or the address bar' },
  { id: 'pick', daily: true, xp: 20, icon: 'compass', name: 'Visit a Resolute Pick', desc: 'Any partner below' },
  { id: 'tour', daily: false, xp: 20, icon: 'play', name: 'Take the tour', desc: 'Four quick cards, under 20 seconds', action: 'tour' },
  { id: 'tips', daily: false, xp: 20, icon: 'bulb', name: 'Learn the buttons', desc: 'Four quick tips: wallet, extensions, workspaces, Shield', action: 'tips' },
  { id: 'extension', daily: false, xp: 100, icon: 'puzzle', name: 'Install your first extension', desc: 'From the Chrome Web Store' },
  { id: 'wallet', daily: false, xp: 150, icon: 'wallet', name: 'Add a wallet', desc: 'MetaMask, Phantom, Rabby and more' },
  { id: 'makers', daily: false, xp: 50, icon: 'makers', name: 'Meet the makers', desc: 'The Code Bros built Resolute', action: 'makers' },
];

let state = {};

function questDone(q) {
  const done = state.done || {};
  return q.daily ? done[q.id] === dayKey() : !!done[q.id];
}

async function complete(id) {
  const q = QUESTS.find((x) => x.id === id);
  if (!q || questDone(q)) return false;
  const before = levelFor(state.xp || 0);
  state.done = state.done || {};
  state.done[id] = q.daily ? dayKey() : true;
  state.xp = (state.xp || 0) + q.xp;
  await store.set(state);
  render();
  const after = levelFor(state.xp);
  if (after > before) showLevelUp(after);
  return true;
}

// ---------- rendering ----------
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function svgIcon(path) {
  const ns = 'http://www.w3.org/2000/svg';
  const s = document.createElementNS(ns, 'svg');
  s.setAttribute('viewBox', '0 0 24 24');
  s.setAttribute('aria-hidden', 'true');
  const p = document.createElementNS(ns, 'path');
  p.setAttribute('d', path);
  s.appendChild(p);
  return s;
}

function render() {
  const xp = state.xp || 0;
  const lv = levelFor(xp);
  const start = levelStart(lv);
  const next = levelStart(lv + 1);
  const pct = Math.max(0, Math.min(100, Math.round(((xp - start) / (next - start)) * 100)));
  $('level').textContent = lv;
  $('rank').textContent = `Level ${lv} · ${rankFor(lv)}`;
  $('xp-now').textContent = xp.toLocaleString();
  $('xp-next').textContent = `${(next - xp).toLocaleString()} to level ${lv + 1}`;
  $('bar').setAttribute('aria-valuenow', String(pct));
  requestAnimationFrame(() => { $('bar-fill').style.width = pct + '%'; });
  $('streak-days').textContent = state.streak || 1;
  $('streak').setAttribute('aria-label', `${state.streak || 1} day streak`);

  const list = $('quests');
  list.replaceChildren();
  let doneCount = 0;
  for (const q of QUESTS) {
    const done = questDone(q);
    if (done) doneCount++;
    const li = el('li', 'quest' + (done ? ' done' : ''));
    const ic = el('span', 'q-icon');
    ic.appendChild(svgIcon(done ? ICONS.check : ICONS[q.icon]));
    const body = el('span', 'q-body');
    body.append(el('span', 'q-name', q.name), el('span', 'q-desc', done ? (q.daily ? 'Done today' : 'Done') : q.desc));
    const parts = [ic, body, el('span', 'q-xp', `+${q.xp} XP`)];
    if (q.action) {
      // Quests you finish by tapping them: a real link or button inside the row.
      const hit = q.action === 'makers' ? el('a', 'q-hit') : el('button', 'q-hit');
      if (q.action === 'makers') {
        hit.href = MAKERS_URL + 'quest';
        hit.rel = 'noopener';
        hit.addEventListener('click', (ev) => {
          ev.preventDefault();
          complete('makers').finally(() => { location.href = hit.href; });
        });
      } else {
        hit.type = 'button';
        hit.addEventListener('click', () => (q.action === 'tips' ? openTips(true) : openTour(0, true)));
      }
      hit.append(...parts);
      li.appendChild(hit);
    } else {
      li.append(...parts);
    }
    list.appendChild(li);
  }
  $('quests-count').textContent = `${doneCount} of ${QUESTS.length} done`;
}

function showLevelUp(lv) {
  $('lu-level').textContent = lv;
  $('lu-title').textContent = rankFor(lv);
  $('lu-text').textContent = `You reached level ${lv}. Keep exploring safely to reach the next rank.`;
  $('levelup').hidden = false;
  try { navigator.vibrate && navigator.vibrate([20, 40, 30]); } catch (e) { /* no vibration */ }
  $('lu-ok').focus();
}
$('lu-ok').addEventListener('click', () => { $('levelup').hidden = true; });

// ---------- search ----------
function looksLikeUrl(s) {
  return /^[a-z][a-z0-9+.-]*:\/\//i.test(s) || /^[^\s]+\.[a-z]{2,}(\/\S*)?$/i.test(s);
}
$('search').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const text = $('q').value.trim();
  if (!text) return;
  await complete('search');
  if (looksLikeUrl(text)) {
    location.href = /^[a-z][a-z0-9+.-]*:\/\//i.test(text) ? text : 'https://' + text;
  } else if (hasChrome && chrome.search && chrome.search.query) {
    chrome.search.query({ text, disposition: 'CURRENT_TAB' });
  } else {
    location.href = 'https://www.google.com/search?q=' + encodeURIComponent(text);
  }
});

// ---------- shortcuts (most visited) ----------
function faviconUrl(pageUrl) {
  if (!hasChrome || !chrome.runtime || !chrome.runtime.id) return '';
  return `chrome-extension://${chrome.runtime.id}/_favicon/?pageUrl=${encodeURIComponent(pageUrl)}&size=32`;
}
async function renderShortcuts() {
  if (!hasChrome || !chrome.topSites) return;
  let sites = [];
  try { sites = await chrome.topSites.get(); } catch (e) { return; }
  sites = sites.filter((s) => /^https?:/.test(s.url)).slice(0, 8);
  if (!sites.length) return;
  const box = $('shortcuts');
  box.replaceChildren();
  for (const s of sites) {
    const a = el('a', 'tile');
    a.href = s.url;
    const mark = el('span', 'tile-mark');
    const host = new URL(s.url).hostname.replace(/^www\./, '');
    const img = el('img');
    img.alt = '';
    img.src = faviconUrl(s.url);
    img.onerror = () => { mark.replaceChildren(document.createTextNode(host[0].toUpperCase())); };
    mark.appendChild(img);
    a.append(mark, el('span', 'tile-name', s.title || host));
    box.appendChild(a);
  }
  $('shortcuts-section').hidden = false;
}

// ---------- Resolute Picks ----------
const SHORT = { trade: 'Trade', cards: 'Cards', tools: 'Tools' };
const SAFE_ICON = /^icons\/[a-z0-9_-]+\.(png|webp|jpg|svg)$/i;
function validPartner(p) {
  return p && typeof p.name === 'string' && typeof p.url === 'string' &&
    /^https:\/\//.test(p.url) && p.enabled !== false;
}
function iconFor(p, bundled) {
  if (!p.icon || !SAFE_ICON.test(p.icon)) return '';
  return bundled ? p.icon : ICON_BASE + p.icon;
}
function mono(p) { return el('span', 'mono', p.name.trim()[0].toUpperCase()); }
function partnerImage(p, bundled) {
  const src = iconFor(p, bundled);
  if (!src) return mono(p);
  const img = el('img');
  img.alt = '';
  img.loading = 'lazy';
  img.src = src;
  img.onerror = () => img.replaceWith(mono(p));
  return img;
}
function openPartner(ev, url) {
  ev.preventDefault();
  complete('pick').finally(() => { location.href = url; });
}

let config = null;
let configBundled = true;
function renderPicks() {
  if (!config) return;
  const groups = Object.fromEntries((config.groups || []).map((g) => [g.id, g]));
  const partners = (config.partners || []).filter(validPartner);
  const tiles = partners.filter((p) => p.newtab_tile).slice(0, 8);
  const box = $('picks');
  box.replaceChildren();
  for (const p of tiles) {
    const a = el('a', 'pick');
    a.href = p.url;
    a.rel = 'noopener';
    a.addEventListener('click', (ev) => openPartner(ev, p.url));
    a.append(partnerImage(p, configBundled), el('b', null, p.name),
      el('small', null, p.own ? 'Resolute team' : (SHORT[p.group] || 'Pick')));
    box.appendChild(a);
  }
  $('disclosure').textContent = config.disclosure || '';

  const ex = $('explore');
  ex.replaceChildren();
  for (const g of config.groups || []) {
    const items = partners.filter((p) => p.group === g.id);
    if (!items.length) continue;
    const sec = el('div', 'group');
    sec.appendChild(el('h3', null, g.title));
    if (g.risk_warning) sec.appendChild(el('p', 'warn', g.risk_warning));
    for (const p of items) {
      const a = el('a', 'row');
      a.href = p.url;
      a.rel = 'noopener';
      a.addEventListener('click', (ev) => openPartner(ev, p.url));
      const t = el('span');
      t.append(el('b', null, p.name), el('small', null, p.description || ''));
      a.append(partnerImage(p, configBundled), t);
      sec.appendChild(a);
    }
    ex.appendChild(sec);
  }
}
$('see-all').addEventListener('click', () => {
  const ex = $('explore');
  ex.hidden = !ex.hidden;
  $('see-all').textContent = ex.hidden ? 'See all' : 'Show less';
  $('see-all').setAttribute('aria-expanded', String(!ex.hidden));
});

async function loadConfig() {
  // 1. What shipped with this version (always works offline).
  try {
    config = await (await fetch('partners.json')).json();
    configBundled = true;
    renderPicks();
  } catch (e) { /* bundled file missing: wait for the network copy */ }
  // 2. Last good copy from GitHub, then a fresh one (new partners without an app update).
  if (state.config && state.config.partners) {
    config = state.config;
    configBundled = false;
    renderPicks();
  }
  try {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 5000);
    const r = await fetch(CONFIG_URL, { signal: ctl.signal, cache: 'no-cache' });
    clearTimeout(timer);
    if (!r.ok) return;
    const fresh = await r.json();
    if (fresh && fresh.schema && Array.isArray(fresh.partners)) {
      config = fresh;
      configBundled = false;
      state.config = fresh;
      await store.set(state);
      renderPicks();
    }
  } catch (e) { /* offline: keep what we have */ }
}

// ---------- journey quests from installed extensions ----------
async function checkExtensions() {
  if (!hasChrome || !chrome.management) return;
  let all = [];
  try { all = await chrome.management.getAll(); } catch (e) { return; }
  const mine = all.filter((x) => x.type === 'extension' && x.id !== chrome.runtime.id &&
    x.installType !== 'admin' && x.installType !== 'other');
  if (mine.length) await complete('extension');
  if (mine.some((x) => WALLET_IDS.has(x.id))) await complete('wallet');
}

// ---------- searches made from the address bar count too ----------
// Looks at today's browsing history (on this device only, nothing leaves the phone) for a search
// results page of a common search engine.
const SEARCH_PAGES = [
  /^https:\/\/(www\.)?google\.[a-z.]+\/search\?/,
  /^https:\/\/(www\.)?bing\.com\/search\?/,
  /^https:\/\/(duckduckgo\.com|html\.duckduckgo\.com)\/.*[?&]q=/,
  /^https:\/\/search\.brave\.com\/search\?/,
  /^https:\/\/search\.yahoo\.com\/search/,
  /^https:\/\/(www\.)?ecosia\.org\/search\?/,
  /^https:\/\/yandex\.[a-z]+\/search/,
];
async function checkSearches() {
  if (!hasChrome || !chrome.history || !chrome.history.search) return;
  if (state.done && state.done.search === dayKey()) return;
  const midnight = new Date();
  midnight.setHours(0, 0, 0, 0);
  let items = [];
  try {
    items = await chrome.history.search({ text: '', startTime: midnight.getTime(), maxResults: 500 });
  } catch (e) { return; }
  if (items.some((h) => SEARCH_PAGES.some((re) => re.test(h.url || '')))) await complete('search');
}

// ---------- welcome tour ----------
// Shown once on the first visit (Chromium's own first-run screens are removed by patch 0013).
// Skip on every card; finishing or skipping both count as seen. Swipe or use the button.
const tour = { i: 0, n: 4, opener: null };
function showSlide(i) {
  tour.i = Math.max(0, Math.min(tour.n - 1, i));
  $('tour-track').style.transform = `translateX(${-100 * tour.i}%)`;
  const slides = $('tour-track').children;
  for (let k = 0; k < slides.length; k++) slides[k].setAttribute('aria-hidden', String(k !== tour.i));
  const dots = $('tour-dots').children;
  for (let k = 0; k < dots.length; k++) dots[k].className = k === tour.i ? 'on' : '';
  $('tour-next').textContent = tour.i === tour.n - 1 ? 'Start exploring' : 'Next';
}
function openTour(i, byUser) {
  tour.opener = document.activeElement;
  $('tour').hidden = false;
  document.body.classList.add('touring');
  showSlide(i);
  // Move keyboard focus only when the person opened the tour. When it opens by itself on
  // the first launch, a focus call while Android was rebuilding the browser screen left
  // the app frozen ("isn't responding"; E2E bisect 2026-11-22: froze from the build that
  // added the tour, rc5).
  if (byUser) $('tour-next').focus();
}
async function closeTour(finished) {
  $('tour').hidden = true;
  document.body.classList.remove('touring');
  state.toured = true;
  await store.set(state);
  if (finished) await complete('tour');
  // Quick tips come on the next visit, not straight after the tour (one thing at a time).
  if (!state.tipsSeen && !state.tipsDue) { state.tipsDue = true; await store.set(state); }
  if (tour.opener && tour.opener.focus) tour.opener.focus();
}
$('tour-next').addEventListener('click', () => {
  if (tour.i === tour.n - 1) closeTour(true); else showSlide(tour.i + 1);
});
$('tour-skip').addEventListener('click', () => closeTour(false));
$('tour').addEventListener('keydown', (ev) => {
  if (ev.key === 'Escape') closeTour(false);
  if (ev.key === 'ArrowRight') showSlide(tour.i + 1);
  if (ev.key === 'ArrowLeft') showSlide(tour.i - 1);
});
(function swipe() {
  let x0 = null;
  const t = $('tour-track');
  t.addEventListener('touchstart', (ev) => { x0 = ev.touches[0].clientX; }, { passive: true });
  t.addEventListener('touchend', (ev) => {
    if (x0 == null) return;
    const dx = ev.changedTouches[0].clientX - x0;
    x0 = null;
    if (Math.abs(dx) < 40) return;
    showSlide(tour.i + (dx < 0 ? 1 : -1));
  }, { passive: true });
})();
$('tour-makers').addEventListener('click', (ev) => {
  ev.preventDefault();
  const url = $('tour-makers').href;
  closeTour(tour.i === tour.n - 1).finally(() => { location.href = url; });
});

// ---------- share my idea (X post tagging @et_rifat, with a level card image) ----------
// Nothing is sent by Resolute: the phone's share sheet or X opens with a ready post the
// person edits and posts themselves.
function cardImage() {
  const lv = levelFor(state.xp || 0);
  const c = document.createElement('canvas');
  c.width = 1200; c.height = 675;
  const g = c.getContext('2d');
  const bg = g.createLinearGradient(0, 0, 1200, 675);
  bg.addColorStop(0, '#22100F'); bg.addColorStop(0.55, '#0D0D0F'); bg.addColorStop(1, '#0F1318');
  g.fillStyle = bg; g.fillRect(0, 0, 1200, 675);
  const glow = g.createRadialGradient(300, 330, 20, 300, 330, 330);
  glow.addColorStop(0, 'rgba(225,6,0,.45)'); glow.addColorStop(1, 'rgba(225,6,0,0)');
  g.fillStyle = glow; g.fillRect(0, 0, 700, 675);
  // crest
  const hex = (cx, cy, r) => { g.beginPath(); for (let k = 0; k < 6; k++) { const a = Math.PI / 3 * k - Math.PI / 2; g.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a)); } g.closePath(); };
  hex(300, 330, 170); g.fillStyle = '#1A0F10'; g.fill(); g.lineWidth = 8; g.strokeStyle = '#E10600'; g.stroke();
  hex(300, 330, 128); g.lineWidth = 3; g.strokeStyle = 'rgba(124,196,255,.5)'; g.stroke();
  g.fillStyle = '#F2F2F4'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '700 120px "Space Grotesk", sans-serif'; g.fillText(String(lv), 300, 338);
  g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  g.fillStyle = '#FF6B5E'; g.font = '700 30px "Space Grotesk", sans-serif'; g.fillText(`LEVEL ${lv} · ${rankFor(lv).toUpperCase()}`, 560, 250);
  g.fillStyle = '#F2F2F4'; g.font = '700 76px "Space Grotesk", sans-serif'; g.fillText(`${(state.xp || 0).toLocaleString()} XP`, 556, 340);
  g.fillStyle = '#B4B4BE'; g.font = '500 32px system-ui, sans-serif'; g.fillText(`${state.streak || 1} day streak on Resolute Browser`, 560, 400);
  g.fillStyle = '#8C8C97'; g.font = '500 26px system-ui, sans-serif'; g.fillText('Web3 browser with real desktop extensions', 560, 560);
  g.fillStyle = '#F2F2F4'; g.font = '700 30px "Space Grotesk", sans-serif'; g.fillText('Resolute', 560, 610);
  return new Promise((res) => c.toBlob(res, 'image/png'));
}
$('share-idea').addEventListener('click', async () => {
  const lv = levelFor(state.xp || 0);
  const text = `I'm Level ${lv} ${rankFor(lv)} on Resolute Browser. @et_rifat I have a SaaS idea: `;
  try {
    const blob = await cardImage();
    const file = blob && new File([blob], 'resolute-card.png', { type: 'image/png' });
    if (file && navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], text });
      return;
    }
  } catch (e) {
    if (e && e.name === 'AbortError') return; // closed the share sheet
  }
  location.href = 'https://x.com/intent/post?text=' + encodeURIComponent(text);
});

// ---------- quick tips ----------
// Four tips about the toolbar buttons (the real toolbar sits right under this sheet). Shown once,
// on the first visit after the welcome tour; replay with the "Learn the buttons" quest.
const TIPS = [
  { k: 'wallet', title: 'Your wallet, one tap away',
    text: 'The red button opens your wallet on any site. Connect, sign and approve right here, without leaving the page.',
    noWallet: 'Add a wallet like MetaMask and it appears here as the red button. Connect and approve on any site without leaving the page.' },
  { k: 'ext', title: 'All your extensions',
    text: 'Tap the puzzle to turn an extension on or off for the site you are on, or pin your favourite next to the wallet.' },
  { k: 'tabs', title: 'Keep projects apart',
    text: 'Tap your tabs, then the grid icon, to see your workspaces. In the menu, "Add tab to workspace" files the page you are on.' },
  { k: 'url', title: 'Resolute Shield has your back',
    text: 'Before a known crypto scam or look-alike site opens, Resolute stops and warns you. The list updates by itself.' },
];
const tips = { i: 0, opener: null, hasWallet: true };
function showTip(i) {
  tips.i = Math.max(0, Math.min(TIPS.length - 1, i));
  const t = TIPS[tips.i];
  $('tip-step').textContent = `Tip ${tips.i + 1} of ${TIPS.length}`;
  $('tip-title').textContent = t.title;
  $('tip-text').textContent = (t.k === 'wallet' && !tips.hasWallet) ? t.noWallet : t.text;
  if (t.k === 'url') $('tip-text').textContent += shieldSentence();
  for (const b of document.querySelectorAll('.mini .mb')) b.classList.toggle('on', b.dataset.k === t.k);
  document.querySelector('.mini').classList.toggle('url-on', t.k === 'url');
  const act = $('tip-action');
  act.hidden = !(t.k === 'wallet' && !tips.hasWallet);
  if (!act.hidden) {
    act.textContent = 'Add MetaMask';
    act.href = 'https://chromewebstore.google.com/detail/metamask/nkbihfbeogaeaoehlefnkodbefgpgknn';
  }
  const dots = $('tip-dots').children;
  for (let k = 0; k < dots.length; k++) dots[k].className = k === tips.i ? 'on' : '';
  $('tip-next').textContent = tips.i === TIPS.length - 1 ? 'Got it' : 'Next';
}
async function openTips(byUser) {
  tips.opener = document.activeElement;
  try {
    const all = hasChrome && chrome.management ? await chrome.management.getAll() : [];
    tips.hasWallet = all.some((x) => WALLET_IDS.has(x.id));
  } catch (e) { tips.hasWallet = true; }
  showTip(0);
  $('tips').hidden = false;
  document.body.classList.add('tipping');
  if (byUser) $('tip-next').focus();
}
async function closeTips(finished) {
  $('tips').hidden = true;
  document.body.classList.remove('tipping');
  state.tipsSeen = true;
  state.tipsDue = false;
  await store.set(state);
  if (finished) await complete('tips');
  if (tips.opener && tips.opener.focus) tips.opener.focus();
}
$('tip-next').addEventListener('click', () => {
  if (tips.i === TIPS.length - 1) closeTips(true); else showTip(tips.i + 1);
});
$('tips-skip').addEventListener('click', () => closeTips(false));
$('tips').addEventListener('click', (ev) => { if (ev.target === $('tips')) closeTips(false); });
$('tips').addEventListener('keydown', (ev) => {
  if (ev.key === 'Escape') closeTips(false);
  if (ev.key === 'ArrowRight') showTip(tips.i + 1);
  if (ev.key === 'ArrowLeft') showTip(tips.i - 1);
});
$('tip-action').addEventListener('click', (ev) => {
  ev.preventDefault();
  const url = $('tip-action').href;
  closeTips(false).finally(() => { location.href = url; });
});

// ---------- Resolute Shield status (filled in by shield.js, the background worker) ----------
let shieldInfo = null;
function ago(ms) {
  const h = Math.round((Date.now() - ms) / 3600000);
  if (h < 1) return 'less than an hour ago';
  if (h < 48) return `${h} hour${h === 1 ? '' : 's'} ago`;
  return `${Math.round(h / 24)} days ago`;
}
function shieldSentence() {
  if (!shieldInfo || !shieldInfo.sites) return '';
  return ` It knows ${shieldInfo.sites.toLocaleString()} scam sites right now.`;
}
async function renderShield() {
  if (!hasChrome || !chrome.storage) return;
  try { shieldInfo = (await chrome.storage.local.get('shieldInfo')).shieldInfo || null; } catch (e) { return; }
  if (!shieldInfo || !shieldInfo.sites) return;
  let line = `It knows ${shieldInfo.sites.toLocaleString()} scam sites (updated ${ago(shieldInfo.updated)})`;
  if (shieldInfo.stopped) line += ` and has stopped ${shieldInfo.stopped.toLocaleString()} so far`;
  $('shield-line').textContent = line + '.';
}

// ---------- start ----------
(async function start() {
  state = await store.get();
  const today = dayKey();
  if (state.lastDay !== today) {
    state.streak = state.lastDay === yesterdayKey() ? (state.streak || 1) + 1 : 1;
    state.lastDay = today;
    await store.set(state);
  }
  render();
  await complete('open');
  if (!state.toured) openTour(0);
  else if (!state.tipsSeen) openTips(false); // also shows once for people who toured before tips existed
  renderShield();
  renderShortcuts();
  loadConfig();
  checkExtensions();
  checkSearches();
})();

// Coming back to an open Resolute Home tab (after browsing) re-checks the quests.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible' || !state) return;
  checkExtensions();
  checkSearches();
});
