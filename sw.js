/* Pundicci Investment Collective — service worker
   Strategy: network-first for the dashboard so a fresh push shows immediately,
   cache-first for icons and fonts. Offline falls back to the last good copy. */

const VERSION = 'pic-v4';
const SHELL = [
  './',
  './index.html',
  './PIC_Dashboard.html',
  './icon-180.png',
  './icon-192.png',
  './icon-512.png',
  './logo-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(VERSION).then(cache =>
      // cache individually: one 404 shouldn't fail the whole install
      Promise.all(SHELL.map(url =>
        cache.add(new Request(url, { cache: 'reload' })).catch(() => null)
      ))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const isDoc = req.mode === 'navigate' || req.destination === 'document';

  if (isDoc) {
    event.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() =>
          caches.match(req).then(hit => hit || caches.match('./PIC_Dashboard.html'))
        )
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req).then(res => {
        if (res && res.status === 200 && (res.type === 'basic' || res.type === 'cors')) {
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      });
    })
  );
});

// lets the page trigger an immediate update after a push
self.addEventListener('message', e => {
  if (e.data === 'skipWaiting') self.skipWaiting();
});
