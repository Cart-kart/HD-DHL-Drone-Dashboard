import csv, json, re
from datetime import datetime

with open('D:/Claude Agent/Claude Project/RAW_DATA/H-D Checklist V.10NOV25 (Responses) 8_26_25-2_4_26 - Form Responses 1.csv', encoding='utf-8-sig') as f:
    rows = list(csv.reader(f))[1:]

rows = [r + [''] * (58 - len(r)) for r in rows if any(c.strip() for c in r)]

def norm_batt(raw):
    s = raw.strip()
    m = re.match(r'[Bb]ypass\s*0*(\d+)', s)
    if m: return 'B' + m.group(1).zfill(2)
    s2 = re.sub(r'\s.*', '', s).strip()
    return s2 if s2 else None

def parse_time_mins(t):
    if not t: return -1
    m = re.match(r'(\d{1,2}):(\d{2})(?::\d+)?\s*(AM|PM)', str(t), re.I)
    if not m: return -1
    h = int(m.group(1))
    if m.group(3).upper() == 'PM' and h != 12: h += 12
    if m.group(3).upper() == 'AM' and h == 12: h = 0
    return h * 60 + int(m.group(2))

def fmt_time(t):
    if not t: return None
    m = re.match(r'(\d{1,2}):(\d{2})(?::\d+)?\s*(AM|PM)', str(t), re.I)
    if not m: return str(t) if t else None
    return m.group(1) + ':' + m.group(2) + ' ' + m.group(3).upper()

def fmt_ts_time(ts_str):
    """Extract HH:MM from timestamp like '9/17/2025 13:48:45'."""
    if not ts_str or ' ' not in ts_str: return None
    t = ts_str.split(' ')[1]
    m = re.match(r'(\d{1,2}):(\d{2})', t)
    return f'{int(m.group(1)):02d}:{m.group(2)}' if m else None

def to_date_ms(date_str):
    try:
        parts = date_str.split('/')
        return datetime(int(parts[2]), int(parts[0]), int(parts[1])).timestamp()
    except:
        return 0

type2 = [r for r in rows if r[9].strip()]
type3 = [r for r in rows if r[3].strip() and not r[9].strip()]

t3map = {}
t3datemap = {}
for r in type3:
    date = r[0].split()[0]
    batt = norm_batt(r[7])
    key = date + '_' + (batt or '')
    mins = parse_time_mins(r[5])
    entry = {'row': r, 'armMin': mins, 'used': False}
    t3map.setdefault(key, []).append(entry)
    t3datemap.setdefault(date, []).append(entry)

missions = []
for r in type2:
    ts = r[0]
    date = ts.split()[0]
    batt = norm_batt(r[11])
    aisle = r[26].strip() or '—'
    person = r[1].replace(' DHL', '').strip()
    raw_drone = r[9].strip()
    # Normalize drone name to "Photon XXX" format
    dm = re.match(r'^0*(\d+)', raw_drone.split('(')[0].strip())
    drone = ('Photon ' + dm.group(1).zfill(3)) if dm else (raw_drone or '—')
    charge = None
    try: charge = round(float(r[28]), 2)
    except: pass
    log_id = r[18].strip() or '—'
    rc_op = r[10].strip() or '—'

    ts_mins = -1
    ts_part = ts.split(' ')[1] if ' ' in ts else ''
    hms = re.match(r'(\d{1,2}):(\d{2}):\d+\s*(AM|PM)?', ts_part, re.I)
    if hms:
        h = int(hms.group(1)); mn = int(hms.group(2)); ap = hms.group(3)
        if ap:
            if ap.upper() == 'PM' and h != 12: h += 12
            if ap.upper() == 'AM' and h == 12: h = 0
        ts_mins = h * 60 + mn

    key = date + '_' + (batt or '')
    best = None; bestDiff = 9999
    for c in t3map.get(key, []):
        if c['used']: continue
        diff = abs(c['armMin'] - ts_mins) if c['armMin'] >= 0 and ts_mins >= 0 else 9999
        if diff < bestDiff: bestDiff = diff; best = c
    if not best:
        for c in t3datemap.get(date, []):
            if c['used']: continue
            diff = abs(c['armMin'] - ts_mins) if c['armMin'] >= 0 and ts_mins >= 0 else 9999
            if diff < bestDiff and diff <= 30: bestDiff = diff; best = c
    if best: best['used'] = True
    t3 = best['row'] if best else None

    completed = t3[3].strip() if t3 else ''
    arm_t = (fmt_time(t3[5]) if t3 and t3[5].strip() else None) or fmt_ts_time(ts)
    disarm_t = fmt_time(t3[6]) if t3 else None
    landing_v = None
    if t3:
        try: landing_v = round(float(t3[8].strip()), 2)
        except: pass
    dur = None
    if t3:
        a = parse_time_mins(t3[5]); d = parse_time_mins(t3[6])
        if a >= 0 and d >= 0:
            dd = d - a
            if dd < 0: dd += 1440
            dur = dd if dd <= 60 else None  # cap: flights never exceed 60 min

    has_result = bool(t3)
    missions.append({
        'date': date, 'ts': ts, 'aisle': aisle,
        'batt': batt or '?', 'person': person, 'drone': drone,
        'armTime': arm_t, 'disarmTime': disarm_t,
        'duration': dur, 'charge': charge, 'landingV': landing_v,
        'completed': completed, 'hasResult': has_result,
        'logId': log_id, 'rcOp': rc_op
    })

done_star = sum(1 for m in missions if not m['hasResult'])
dates_sorted = sorted(set(m['date'] for m in missions), key=to_date_ms)
print(f'Total missions: {len(missions)}, Done*: {done_star}')
print(f'Date range: {dates_sorted[0]} to {dates_sorted[-1]}')
print(f'Sample: {json.dumps(missions[0], ensure_ascii=False)}')

with open('C:/Users/A/AppData/Local/Temp/dashboard-repo/data/old-missions.json', 'w', encoding='utf-8') as f:
    json.dump(missions, f, ensure_ascii=False, separators=(',', ':'))
print('Saved.')
