# Iron Ledger

A block-periodised workout logger that runs as an installable web app on a phone.
Personal project — one user, no accounts, no backend.

## What it does

- **Prescribes the next session** from your own history: double progression inside
  a block, estimated-1RM re-anchoring when the rep range changes between blocks,
  and a layoff guard that holds the load after time off.
- **Logs sets** with steppers and a one-minute rest timer. Keeps the screen awake.
- **Autoregulates volume** from per-muscle pump / soreness / performance feedback
  after each session (Israetel / RP set-progression table).
- **Charts** estimated 1RM per lift, weekly hard sets against MEV/MRV landmarks,
  and bodyweight.
- **Works offline.** Service worker caches the whole app; the gym has no signal.

Rep ranges: strength 5–7 compound / 8–10 accessory, hypertrophy 8–10 / 10–12.
Mesocycle: 5 wk strength → 1 deload → 6 wk hypertrophy → 1 deload, repeating.

## Layout

```
index.html              generated — do not edit by hand
src/app.html            the actual source
src/build.py            wraps app.html into index.html (head, manifest, SW)
sw.js                   offline cache
manifest.webmanifest    install metadata
data/raw-log.txt        the original written training log
data/build.py           parses the log into sessions
data/emit.py            packs them into data/seed.json
```

The parsed history is embedded in `src/app.html` as `SEED.ARCH`, so the app
carries its own past and works on a fresh device with no import.

## Changing it

```bash
# edit src/app.html, then:
python3 src/build.py

# preview locally
python3 -m http.server 8731
```

Commit and push — GitHub Pages redeploys on its own.

## Re-parsing the log

```bash
cd data && python3 emit.py     # rewrites seed.json
```
Then splice `seed.json` back into the `const SEED = ...` line in `src/app.html`.
