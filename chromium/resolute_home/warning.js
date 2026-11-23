// Resolute Shield warning page. Copyright (c) 2026 Dewan Efaj Tahamid Rifat (The Code Bros). All rights reserved.
'use strict';

const $ = (id) => document.getElementById(id);
const q = new URLSearchParams(location.search);
const target = q.get('url') || '';
let host = '';
try { host = new URL(target).hostname; } catch (e) { /* bad link: nothing to open */ }

$('w-host').textContent = host || 'Unknown site';
if (q.get('kind') === 'lookalike' && q.get('like')) {
  $('w-kicker').textContent = 'Look-alike address';
  $('w-title').textContent = `This is not ${q.get('like')}`;
  $('w-why').textContent = `The address is spelled almost like ${q.get('like')}. Scammers copy famous Web3 sites `
    + 'with one letter changed to steal wallets. Check the spelling, or open the real site yourself.';
}

$('w-back').addEventListener('click', async () => {
  if (history.length > 1) { history.back(); return; }
  try {
    const tab = await chrome.tabs.getCurrent();
    await chrome.tabs.update(tab.id, { url: 'chrome://newtab/' });
  } catch (e) { location.href = 'index.html'; }
});

let armed = false;
$('w-continue').addEventListener('click', async () => {
  if (!host) return;
  // Two taps: the first one asks again, so it is never opened by accident.
  if (!armed) {
    armed = true;
    $('w-continue').textContent = `Tap again to open ${host}`;
    $('w-continue').classList.add('armed');
    return;
  }
  try { await chrome.runtime.sendMessage({ type: 'shield-pass', url: target }); } catch (e) { /* still open */ }
  location.replace(target);
});


