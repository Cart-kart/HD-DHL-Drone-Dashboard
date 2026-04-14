# HD-DHL Drone Dashboard

Live drone mission dashboard — Photon 400 tracking at Harley Davidson / DHL.

- **Live:** https://cart-kart.github.io/HD-DHL-Drone-Dashboard/
- **Version:** V.0.7.5
- **Main file:** index.html (single-file, all JS/CSS embedded)
- **Data:** Google Sheets CSV (live) + baked static JSON
- **Bake script:** process_2026.py (runs daily at 18:00)

## Architecture
- `index.html` — entire app (JS, CSS, baked data)
- `process_2026.py` — fetches Google Sheets CSV, bakes into index.html + 2026-missions.json
- `STATIC_MISSIONS_2025/2026` — historical JSON baked in
- Live data deduped against static by `ts`

## Current State (as of last push)
- Latest: Drone Deployment Timeline card added
- Active battery/drone status persisted via static config (not localStorage)
- Click aisle in Flight Record → jumps to Aisle Overview

## Last Worked On
<!-- Update this section each session before pushing -->
- Date: 2026-04-08
- What was done: Drone Deployment Timeline card
- Next: (update this when you start next session)

## How to Start Each Session
1. `git pull` — get latest
2. Open Claude Code in this folder
3. Read this file for context, then describe what to work on
