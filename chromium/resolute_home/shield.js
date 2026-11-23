// Resolute Shield. Copyright (c) 2026 Dewan Efaj Tahamid Rifat (The Code Bros). All rights reserved.
// Resolute Home's background worker: before a page opens, its address is checked on the
// phone against public lists of crypto scam and phishing sites. A match opens Resolute's
// warning page instead. Nothing about the pages you visit leaves the phone; the lists are
// only downloaded.
//
// Lists:
//  * MetaMask's eth-phishing-detect list (github.com/MetaMask/eth-phishing-detect,
//    DBAD licence, credited in NOTICE): blacklist, whitelist, fuzzylist (look-alikes).
//  * Resolute's own additions and exceptions: config/shield.json in the Resolute repo.
// A copy of MetaMask's list is bundled at build time (shield-list.json.gz, when the build could
// download it), so Shield works before the first download.
'use strict';

const LIST_URL = 'https://raw.githubusercontent.com/MetaMask/eth-phishing-detect/main/src/config.json';
const OWN_URL = 'https://raw.githubusercontent.com/EfajTahamidRifat/resolute-browser/main/config/shield.json';
const REFRESH_MIN = 12 * 60;
const TEST_HOST = 'scam-test.resolute.invalid'; // always blocked: lets tests check Shield
const WARNING = chrome.runtime.getURL('warning.html');

let lists = null; // { block: Set, allow: Set, fuzzy: [], tolerance }
let loading = null;

function hostOf(url) {
  try {
    const u = new URL(url);
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return '';
    return u.hostname.toLowerCase().replace(/\.$/, '');
  } catch (e) { return ''; }
}

// a.b.example.com -> [a.b.example.com, b.example.com, example.com]
function suffixes(host) {
  const parts = host.split('.');
  const out = [];
  for (let i = 0; i < parts.length - 1; i++) out.push(parts.slice(i).join('.'));
  return out;
}

function build(meta, own) {
  const block = new Set((meta && meta.blacklist) || []);
  const allow = new Set((meta && meta.whitelist) || []);
  for (const d of (own && own.block) || []) block.add(String(d).toLowerCase());
  for (const d of (own && own.allow) || []) { allow.add(String(d).toLowerCase()); block.delete(String(d).toLowerCase()); }
  block.add(TEST_HOST);
  return {
    block, allow,
    fuzzy: ((meta && meta.fuzzylist) || []).map((d) => String(d).toLowerCase()),
    tolerance: Math.min(2, Number((meta && meta.tolerance) || 1)),
  };
}

async function fetchJson(url) {
  const r = await fetch(url, { cache: 'no-store' });
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

async function bundled() {
  try {
    const r = await fetch(chrome.runtime.getURL('shield-list.json.gz'));
    const text = await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text();
    return JSON.parse(text);
  } catch (e) { return null; }
}

async function load() {
  if (lists) return lists;
  if (!loading) {
    loading = (async () => {
      const s = await chrome.storage.local.get(['shieldList', 'shieldOwn']);
      const meta = s.shieldList || (await bundled());
      lists = build(meta, s.shieldOwn);
      return lists;
    })().finally(() => { loading = null; });
  }
  return loading;
}

async function refresh() {
  let meta = null;
  let own = null;
  try { meta = await fetchJson(LIST_URL); } catch (e) { /* offline: keep the old list */ }
  try { own = await fetchJson(OWN_URL); } catch (e) { /* keep the old one */ }
  const old = await chrome.storage.local.get(['shieldList', 'shieldOwn', 'shieldInfo']);
  const save = {};
  if (meta && Array.isArray(meta.blacklist) && meta.blacklist.length > 1000) save.shieldList = meta;
  if (own && typeof own === 'object') save.shieldOwn = own;
  if (save.shieldList || save.shieldOwn) {
    const m = save.shieldList || old.shieldList || (await bundled());
    const o = save.shieldOwn || old.shieldOwn;
    lists = build(m, o);
    save.shieldInfo = { ...(old.shieldInfo || {}), sites: lists.block.size - 1, updated: Date.now() };
    await chrome.storage.local.set(save);
  }
}

function distance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    let best = i;
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (cur[j] < best) best = cur[j];
    }
    if (best > max) return max + 1;
    prev = cur;
  }
  return prev[b.length];
}

// Returns null (safe) or { kind: 'listed' | 'lookalike', like }.
function check(l, host) {
  const sfx = suffixes(host);
  if (sfx.some((d) => l.allow.has(d))) return null;
  if (sfx.some((d) => l.block.has(d))) return { kind: 'listed' };
  // Look-alikes of well-known Web3 sites (metamsk.io for metamask.io): compare the last
  // two labels with the fuzzy list, a small spelling distance but not the same name.
  const base = sfx[sfx.length - 1] || host;
  for (const f of l.fuzzy) {
    if (base === f || sfx.includes(f)) continue;
    if (distance(base, f, l.tolerance) <= l.tolerance) return { kind: 'lookalike', like: f };
  }
  return null;
}

async function allowedThisSession(host) {
  try {
    const s = await chrome.storage.session.get('shieldPass');
    return !!(s.shieldPass || {})[host];
  } catch (e) { return false; }
}

chrome.webNavigation.onBeforeNavigate.addListener(async (d) => {
  if (d.frameId !== 0 || d.tabId < 0) return;
  const host = hostOf(d.url);
  if (!host) return;
  const l = await load();
  const hit = check(l, host);
  if (!hit || (await allowedThisSession(host))) return;
  const q = new URLSearchParams({ url: d.url, kind: hit.kind });
  if (hit.like) q.set('like', hit.like);
  try { await chrome.tabs.update(d.tabId, { url: `${WARNING}?${q}` }); } catch (e) { return; }
  const s = await chrome.storage.local.get('shieldInfo');
  const info = s.shieldInfo || {};
  info.stopped = (info.stopped || 0) + 1;
  await chrome.storage.local.set({ shieldInfo: info });
});

// The warning page's "Continue anyway": let this site open for the rest of the session.
chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (!msg || msg.type !== 'shield-pass' || !sender.url || !sender.url.startsWith(WARNING)) return;
  const host = hostOf(msg.url);
  if (!host) return;
  chrome.storage.session.get('shieldPass').then((s) => {
    const pass = s.shieldPass || {};
    pass[host] = true;
    return chrome.storage.session.set({ shieldPass: pass });
  }).then(() => reply({ ok: true }), () => reply({ ok: false }));
  return true;
});

chrome.alarms.onAlarm.addListener((a) => { if (a.name === 'shield-refresh') refresh(); });

async function schedule() {
  const a = await chrome.alarms.get('shield-refresh');
  if (!a) chrome.alarms.create('shield-refresh', { delayInMinutes: 1, periodInMinutes: REFRESH_MIN });
  const s = await chrome.storage.local.get('shieldInfo');
  if (!s.shieldInfo || !s.shieldInfo.updated || Date.now() - s.shieldInfo.updated > REFRESH_MIN * 60000) refresh();
}
chrome.runtime.onInstalled.addListener(schedule);
chrome.runtime.onStartup.addListener(schedule);
