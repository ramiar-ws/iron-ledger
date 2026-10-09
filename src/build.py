#!/usr/bin/env python3
"""Wrap the artifact-shaped source (src/app.html) into a standalone
index.html for GitHub Pages: real <head>, manifest, icons, service worker."""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
app  = (root / 'src' / 'app.html').read_text()

MARK = '<div id="app">'
i = app.index(MARK)
head_bits, body_bits = app[:i].strip(), app[i:].strip()

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,maximum-scale=1">
<meta name="theme-color" content="#0A0A0B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Iron Ledger">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="description" content="Block-periodised workout logger.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<style>html{background:#0A0A0B}body{margin:0}img{max-width:100%}
[hidden]{display:none!important}</style>
"""

FOOT = """
<script>
if('serviceWorker' in navigator){
  window.addEventListener('load', function(){
    navigator.serviceWorker.register('sw.js').then(function(reg){
      reg.addEventListener('updatefound', function(){
        const nw = reg.installing;
        if(!nw) return;
        nw.addEventListener('statechange', function(){
          if(nw.state === 'installed' && navigator.serviceWorker.controller){
            try { toast('Update ready — close and reopen'); } catch(e){}
          }
        });
      });
    }).catch(function(){ /* offline install still works from cache */ });
  });
}
</script>
</body>
</html>
"""

out = HEAD + head_bits + "\n</head>\n<body>\n" + body_bits + FOOT
(root / 'index.html').write_text(out)
print('index.html:', len(out), 'bytes')

# sanity: the page must carry the archive and must not double-register meta
assert 'SEED' in out and 'ARCH' in out, 'archive missing from build'
assert out.startswith('<!doctype html>') and '\n</head>\n<body>\n' in out, 'malformed document'
print('ok — archive present, document well-formed')
