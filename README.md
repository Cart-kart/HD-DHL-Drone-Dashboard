# Drone Mission Dashboard

Live dashboard for Photon 400 drone operations at DHL.

🔗 **[View Live Dashboard](https://cart-kart.github.io/dashboard/)**

---

## Features

- **Mission Log** — all take-off missions with per-day color banding, red highlight for failed/aborted flights
- **Drone filter** — sort mission log by drone name
- **Battery Analytics** — usage count, avg/min landing voltage per cell, total voltage consumed, last take-off voltage
- **Charts** — missions per day, top aisles flown, battery usage & avg voltage
- **24h time format** — arm/disarm times displayed in 24-hour format
- **Auto aisle correction** — normalizes free-text aisle entries (e.g. `N14`, `No2`) to canonical names (e.g. `N14_VAO_VAP`)
- **Battery % scale** — 3.10V/cell = 0%, 4.20V/cell = 100%

## Data Source

Pulls live from Google Sheets (published CSV) with CORS proxy fallback chain.

## Updates — 2026-03-14

- Added Drone column + filter dropdown to Mission Log
- Replaced Battery Status (Good/Watch/Critical) with Last Take-off V from column AF
- Battery Total Used V replaces Avg Drain
- Removed Battery Landing Voltage chart
- Fixed aborted mission detection (`ไม่เสร็จสิ้น`) — previously miscounted as completed
- Status badge renamed Aborted → **Fail**
- Log ID column added
- Take-off V column added to Mission Log
- Time display changed to 24-hour format
- Mission Log rows color-banded by day
- Battery % calculation updated (3.10V–4.20V scale)
- N21_VAA_VAB added to aisle map
