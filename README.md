# Drone Mission Dashboard — V.0.5

Live dashboard for Photon 400 drone operations at Harley Davidson · DHL.

🔗 **[View Live Dashboard](https://cart-kart.github.io/HD-DHL-Drone-Dashboard/)**

---

## Changelog

### 2026-03-20 — V.0.5
- Version label added below dashboard title
- **Flight Log** renamed to **Flight Record**
- Live flight timer in Duration column for in-flight missions (counts up from arm time, with `est. ~Xm` bracket)
- Click a Daily Flight Log row to jump to the matching row in Flight Record
- Battery Voltage shows **Pending** for in-flight missions
- Overnight landing times labeled `(next day)` in amber
- Midnight crossover fix: type3 disarm rows submitted after midnight now correctly match night-shift type2 from prior date
- 90-minute proximity window added to primary type3 key match (prevents wrong matches)
- Daily bake (`process_2026.py`) switched to published Google Sheets CSV — faster and more up-to-date than GAS endpoint
- Voltage cap at 26V filters bad operator entries (e.g. 78V, 149V)
- Aisle `21` → `N21_VAA_VAB` normalization in live feed
- Aisle Overview defaults to top-first sort
- `no data` display replacing `—` across Battery History, Aisle History, Battery Health Summary

### 2026-03-19
- `STATIC_MISSIONS_2026`: previous days baked to static JSON; today served live only
- Battery 71 → 79 remap for 2/13/2026–3/18/2026 20:00 window
- Aisle duration estimates from 2025 historical median data
- 2025 operator / drone / aisle normalization (Photon 001–006 names, canonical aisle codes)
- Estimated landing time for no-disarm rows using per-aisle median
- Paginated Flight Log (20/page, most recent first) with drone filter
- Battery Voltage column: stacked ↑/↓ layout with battery#, V/cell, %
- Battery Health Summary: active batteries on top, dead/inactive hidden by default, clickable rows → Battery History
- Section renames: Flight Log Calendar, Aisle Flight Time, Aisle Overview, Battery Log, Daily Flight Log
- Aisle Overview: By Name sort (N→E→X order)
- Column reorder in Flight Log
- Col 28 aisle fallback for COL_2026 format
- Arm time fallback from form submission timestamp when no type3 matched
- Dual battery key indexing (col H + col L) for type3 matching
- Note column in Flight Log: editable textarea, persists via localStorage

### 2026-03-17
- Calendar heatmap replacing Missions per Day bar chart (click date → Daily Flight Log)
- Daily Flight Log panel with live In Flight status
- Battery History panel (pre-flight and landing voltage)
- Aisle Overview heatmap table + Aisle History panel
- Aisle sort controls (least/top first, by name)
- 5-minute auto-refresh with countdown timer + stale data detection
- Total Flight Time stat card
- Mission Log: time-proximity type2/type3 matching (replaces FIFO)
- Battery Health: Total Flight Time and Avg per Flight columns

### 2026-03-14
- Initial dashboard release
- Google Apps Script proxy for live data
- Drone column + filter dropdown
- Log ID and Take-off V columns
- 24-hour time format
- Day-banded Mission Log rows
- Battery % scale (3.10V–4.20V)

---

## Architecture

- **Single-file HTML** (`index.html`) — all JS, CSS, and baked data embedded
- `STATIC_MISSIONS_2025` + `STATIC_MISSIONS_2026` — JSON arrays baked by Python scripts
- Live GAS fetch appends today's missions; deduplicated against static by `ts`
- `process_static.py` — processes local CSV files (multi-format), embeds into index.html
- `process_2026.py` — fetches live Google Sheets CSV, bakes into 2026-missions.json + index.html
- `bake_daily.bat` — scheduled at 18:00 daily via Windows Task Scheduler

## Data Source

Live data from Google Sheets (published CSV). Static historical data baked at 18:00 daily.
