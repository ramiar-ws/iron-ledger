/* Iron Ledger service worker.

   The page itself is NETWORK-FIRST: online you always get the build that is
   actually deployed, no "close and reopen" dance. Offline it falls straight
   back to the cached copy, so the gym still works with no signal.

   Fonts and icons stay CACHE-FIRST — they're large and almost never change. */
const CACHE = 'iron-ledger-v3';
const ASSETS = [
  './', './index.html', './manifest.webmanifest',
  './icon-192.png', './icon-512.png', './icon-180.png', './icon-maskable-512.png',
  './fonts/OpenDyslexic-Regular.woff2', './fonts/OpenDyslexic-Bold.woff2'
];

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(CACHE)
      .then(function(c){ return c.addAll(ASSETS); })
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys()
      .then(function(keys){
        return Promise.all(keys.filter(function(k){ return k !== CACHE; })
                               .map(function(k){ return caches.delete(k); }));
      })
      .then(function(){ return self.clients.claim(); })
  );
});

function isPage(req){
  return req.mode === 'navigate' ||
         (req.destination === '' && req.url.endsWith('/')) ||
         req.url.endsWith('.html');
}

self.addEventListener('fetch', function(e){
  const req = e.request;
  if(req.method !== 'GET') return;
  if(new URL(req.url).origin !== self.location.origin) return;

  if(isPage(req)){
    // network first — the deployed build wins whenever it is reachable
    e.respondWith(
      fetch(req, { cache:'no-store' })
        .then(function(res){
          const copy = res.clone();
          caches.open(CACHE).then(function(c){ c.put('./index.html', copy); });
          return res;
        })
        .catch(function(){
          return caches.match('./index.html').then(function(hit){
            return hit || caches.match('./');
          });
        })
    );
    return;
  }

  // everything else: cache first, refresh in the background
  e.respondWith(
    caches.match(req).then(function(hit){
      const net = fetch(req).then(function(res){
        if(res && res.ok){
          const copy = res.clone();
          caches.open(CACHE).then(function(c){ c.put(req, copy); });
        }
        return res;
      }).catch(function(){ return hit; });
      return hit || net;
    })
  );
});
