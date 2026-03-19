"""
process_2026.py
Fetches 2026 live GAS data, processes completed days into static mission objects,
saves to 2026-missions.json and embeds into index.html as STATIC_MISSIONS_2026.

Run after each flight day ends (or on a schedule).
Only bakes dates BEFORE today — today's data stays live.
"""
import csv, json, re, sys, io
from datetime import datetime, date
from pathlib import Path
from urllib.request import urlopen, Request

CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSPOCAMFEhkGWvUwpK1TPf2amqxxL5vN-rgEPjBqpifzZ34CG8kVNNjppMOvhmau5NM4w-BkgDsUTYb/pub?output=csv'
# Paths relative to this script's location
_HERE = Path(__file__).parent
INDEX_HTML = str(_HERE / 'index.html')
OUTPUT_JSON = str(_HERE / 'data' / '2026-missions.json')

# Column mapping (0-indexed) — matches JS C = {...}
C_TIMESTAMP  = 0
C_PERSON     = 1
C_TYPE       = 2
C_COMPLETED  = 3
C_REASON     = 4
C_ARM_TIME   = 5
C_DISARM_TIME= 6
C_BATT_NAME  = 7   # type3: battery name
C_BATT_LAND  = 8   # type3: landing voltage
C_DRONE      = 9
C_RC_OP      = 10
C_BATT_COL_L = 11  # type2: battery name (2nd occurrence)
C_LOG_ID     = 22
C_IN_PLANT   = 29
C_BATT_CHARGE= 31

AISLE_MAP = {
    1:'N01_PAK_PAL',2:'N02_PAI_PAJ',3:'N03_PAG_PAH',4:'N04_PAE_PAF',
    5:'N05_PAC_PAD',6:'N06_PAA_PAB',7:'N07_VBK_VBL',8:'N08_VBI_VBJ',
    9:'N09_VBG_VBH',10:'N10_VBE_VBF',11:'N11_VBC_VBD',12:'N12_VBA_VBB',
    13:'N13_VAQ_VAR',14:'N14_VAO_VAP',15:'N15_VAM_VAN',16:'N16_VAK_VAL',
    17:'N17_VAI_VAJ',18:'N18_VAG_VAH',19:'N19_VAE_VAF',20:'N20_VAC_VAD',
    21:'N21_VAA_VAB',22:'N22_VDE_VDF_P1',23:'N23_VDE_VDF_P2',
    24:'N24_VDG_P1',25:'N25_VDG_P2',26:'N26_VDH_VDI_P1',27:'N27_VDH_VDI_P2',
    28:'N28_VDL_VDM_P1',29:'N29_VDL_VDM_P2',30:'N30_VDO',
    31:'N31_VDP_P1',32:'N32_VDP_P2',33:'N33_VDQ_VDP',34:'N34_VDL_P3',
}
AISLE_MAP_E = {
    1:'E01_EBA_P1',2:'E02_EBA_P2',3:'E03_EBA_P3',4:'E04_EBA_P4',
    5:'E05_EBB_P1',6:'E06_EBB_P2',7:'E07_EBC_EBD_P1',8:'E08_EBC_EBD_P2',
    9:'E09_EBE_EBF_P1',10:'E10_EBE_EBF_P2',11:'E11_EBG_P1',12:'E12_EBG_P2',
    13:'E13_EBH_EBI_P1',14:'E14_EBH_EBI_P2',15:'E15_EBJ_EBK_P1',16:'E16_EBJ_EBK_P2',
    17:'E17_EBL_EBM_P1',18:'E18_EBL_EBM_P2',19:'E19_EBN_EBO_P1',20:'E20_EBN_EBO_P2',
    21:'E21_EBP_EBQ_P1',22:'E22_EBP_EBQ_P2',23:'E23_EBR_P1',24:'E24_EBR_P2',
    25:'E25_EBS_P1',26:'E26_EBS_P2',27:'E27_EAA_EAB_P1',28:'E28_EAA_EAB_P2',
    29:'E29_EAC_EAD_P1',30:'E30_EAC_EAD_P2',31:'E31_EAE_EAF_P1',32:'E32_EAE_EAF_P2',
    33:'E33_EAG_P1',34:'E34_EAG_P2',35:'E35_EAH_EAI_P1',36:'E36_EAH_EAI_P2',
    37:'E37_EAI_P3',38:'E38_EAJ_EAK_P1',39:'E39_EAJ_EAK_P2',
    40:'E40_EAL_EAM_P1',41:'E41_EAL_EAM_P2',42:'E42_EAN_EAO_P1',43:'E43_EAN_EAO_P2',
    44:'E44_EAP_EAQ_P1',45:'E45_EAP_EAQ_P2',46:'E46_EAR_EAS_P1',47:'E47_EAR_EAS_P2',
    48:'E48_EAS_P3',49:'E49_EAS_P4',
}

# Battery 71→79 remap window: Feb 13 2026 00:00 – Mar 18 2026 20:00
REMAP_START = datetime(2026, 2, 13, 0, 0)
REMAP_END   = datetime(2026, 2, 18, 20, 0)  # corrected: Mar 18 in code but Feb 13 start

# Actually from the JS: start = new Date(2026, 1, 13) = Feb 13, end = new Date(2026, 2, 18, 20) = Mar 18 20:00
REMAP_START = datetime(2026, 2, 13, 0, 0)
REMAP_END   = datetime(2026, 3, 18, 20, 0)

# Type3 battery column window: 3/18 20:00 – 3/19 15:00 → use col L (index 11) primary
WIN_COL_L_START = datetime(2026, 3, 18, 20, 0)
WIN_COL_L_END   = datetime(2026, 3, 19, 15, 0)


def parse_ts(ts_str):
    """Parse timestamp string to datetime, or None."""
    if not ts_str:
        return None
    try:
        # formats: "3/19/2026 9:24:41" or "3/19/2026"
        parts = ts_str.strip().split(' ')
        d_part = parts[0]
        t_part = parts[1] if len(parts) > 1 else '0:0:0'
        mo, dd, yy = map(int, d_part.split('/'))
        h, mn, *s = map(int, t_part.split(':'))
        return datetime(yy, mo, dd, h, mn, s[0] if s else 0)
    except:
        return None


def remap_batt(raw_id, ts_dt):
    """Remap battery 71 to 79 within the error window."""
    if raw_id != '71':
        return raw_id
    if ts_dt and REMAP_START <= ts_dt < REMAP_END:
        return '79'
    return '71'


def normalize_aisle(raw):
    if not raw or raw.strip() in ('', '—'):
        return '—'
    s = raw.strip()
    m = re.match(r'^[Ee][Oo]?\.?\s*0*(\d+)', s)
    if m:
        num = int(m.group(1))
        return AISLE_MAP_E.get(num, 'E' + str(num).zfill(2))
    m = re.match(r'[Nn][Oo]?\.?\s*0*(\d+)', s)
    if not m:
        return s
    num = int(m.group(1))
    return AISLE_MAP.get(num, 'N' + str(num).zfill(2))


def parse_landing_v(s):
    """Parse landing voltage — handles "(03)22.4" style annotations."""
    if not s:
        return None
    try:
        v = float(s)
        return v
    except:
        pass
    m = re.search(r'(\d+\.?\d*)$', s)
    return float(m.group(1)) if m else None


def norm_total(v):
    if v is None or v <= 1:
        return None
    return v * 6 if v < 6 else v


def parse_time_mins(t_str):
    """Parse time string to minutes since midnight. Returns -1 on failure."""
    if not t_str:
        return -1
    m = re.match(r'(\d{1,2}):(\d{2})(?::\d+)?\s*(AM|PM)?', str(t_str).strip(), re.I)
    if not m:
        return -1
    h = int(m.group(1))
    mn = int(m.group(2))
    ap = m.group(3)
    if ap:
        if ap.upper() == 'PM' and h != 12:
            h += 12
        if ap.upper() == 'AM' and h == 12:
            h = 0
    return h * 60 + mn


def fmt_time(t_str):
    """Normalize time to HH:MM format."""
    mins = parse_time_mins(t_str)
    if mins < 0:
        return '—'
    h = mins // 60
    mn = mins % 60
    return f'{h:02d}:{mn:02d}'


def mission_duration(arm_str, disarm_str):
    """Compute duration in minutes, handling midnight crossing. Cap at 60."""
    a = parse_time_mins(arm_str)
    d = parse_time_mins(disarm_str)
    if a < 0 or d < 0:
        return None
    dd = d - a
    if dd < 0:
        dd += 1440
    return dd if dd <= 60 else None


def get_col(row, idx):
    """Safely get column value."""
    return row[idx].strip() if idx < len(row) else ''


def fetch_csv():
    """Fetch CSV from published Google Sheet URL."""
    print(f'Fetching {CSV_URL} ...')
    req = Request(CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urlopen(req, timeout=30)
    content = resp.read()
    text = content.decode('utf-8-sig')
    print(f'Fetched {len(text)} bytes')
    return text


def process_rows(rows, cutoff_date):
    """
    Process 2026 form rows into mission objects.
    Only includes missions from dates strictly before cutoff_date.
    """
    # Pad rows to at least 32 columns
    rows = [r + [''] * max(0, 32 - len(r)) for r in rows]

    # Filter to past dates only
    past_rows = []
    for r in rows:
        ts_dt = parse_ts(get_col(r, C_TIMESTAMP))
        if ts_dt and ts_dt.date() < cutoff_date:
            past_rows.append(r)

    print(f'Rows before today: {len(past_rows)} / {len(rows)}')

    # Build type3 lookup
    type3_rows = [r for r in past_rows if 'type' in get_col(r, C_TYPE).lower() or '3.' in get_col(r, C_TYPE)]
    type3_rows = [r for r in past_rows if get_col(r, C_TYPE).startswith('3.') or 'After Disarm' in get_col(r, C_TYPE)]
    type2_rows = [r for r in past_rows if get_col(r, C_TYPE).startswith('2.') or 'Take-off' in get_col(r, C_TYPE)]

    print(f'Type2: {len(type2_rows)}, Type3: {len(type3_rows)}')

    # Build type3 map keyed by date_battId
    t3map = {}
    t3datemap = {}
    for r in type3_rows:
        ts_dt = parse_ts(get_col(r, C_TIMESTAMP))
        if not ts_dt:
            continue
        date_str = f'{ts_dt.month}/{ts_dt.day}/{ts_dt.year}'

        # Battery column window: 3/18 20:00 – 3/19 15:00 → use col L primary
        use_l_primary = WIN_COL_L_START <= ts_dt < WIN_COL_L_END
        col_l = get_col(r, C_BATT_COL_L).split()[0] if get_col(r, C_BATT_COL_L) else ''
        col_h = re.sub(r'\s.*', '', get_col(r, C_BATT_NAME)).strip()
        raw_batt = (col_l or col_h) if use_l_primary else (col_h or col_l)
        batt_id = remap_batt(raw_batt, ts_dt)

        arm_min = parse_time_mins(get_col(r, C_ARM_TIME))
        key = f'{date_str}_{batt_id}'
        entry = {'row': r, 'armMin': arm_min if arm_min >= 0 else -1, 'used': False}
        t3map.setdefault(key, []).append(entry)
        t3datemap.setdefault(date_str, []).append(entry)

    missions = []
    for r in type2_rows:
        ts_dt = parse_ts(get_col(r, C_TIMESTAMP))
        if not ts_dt:
            continue
        ts_str = get_col(r, C_TIMESTAMP)
        date_str = f'{ts_dt.month}/{ts_dt.day}/{ts_dt.year}'

        # Battery: col L (index 11) primary, col H (index 7) fallback
        raw_batt = re.sub(r'\s.*', '', get_col(r, C_BATT_COL_L)).strip() or \
                   re.sub(r'\s.*', '', get_col(r, C_BATT_NAME)).strip()
        batt = remap_batt(raw_batt, ts_dt) if raw_batt else '?'

        aisle = normalize_aisle(get_col(r, C_IN_PLANT) or get_col(r, 28))
        drone = get_col(r, C_DRONE).strip() or '—'
        rc_op = get_col(r, C_RC_OP) or '—'
        log_id = get_col(r, C_LOG_ID) or '—'
        person = get_col(r, C_PERSON)

        charge_raw = get_col(r, C_BATT_CHARGE)
        charge = None
        try:
            charge = norm_total(float(charge_raw))
        except:
            pass

        ts_min = ts_dt.hour * 60 + ts_dt.minute

        # Match type3 by date+battery key, then by arm time proximity
        key = f'{date_str}_{batt}'
        candidates = t3map.get(key, [])
        best = None
        best_diff = 9999
        for c in candidates:
            if c['used']:
                continue
            diff = abs(c['armMin'] - ts_min) if c['armMin'] >= 0 and ts_min >= 0 else 9999
            if diff < best_diff and diff <= 90:
                best_diff = diff
                best = c

        # Fallback: search all unused type3 on same date by arm time
        if not best:
            for c in t3datemap.get(date_str, []):
                if c['used']:
                    continue
                diff = abs(c['armMin'] - ts_min) if c['armMin'] >= 0 and ts_min >= 0 else 9999
                if diff < best_diff and diff <= 30:
                    best_diff = diff
                    best = c

        if best:
            best['used'] = True
        t3 = best['row'] if best else None

        arm_time = fmt_time(get_col(t3, C_ARM_TIME)) if t3 else fmt_time(ts_str.split(' ')[1] if ' ' in ts_str else '')
        disarm_time = fmt_time(get_col(t3, C_DISARM_TIME)) if t3 else '—'
        completed = get_col(t3, C_COMPLETED) if t3 else ''
        reason = get_col(t3, C_REASON) if t3 else ''
        has_result = bool(t3)

        landing_v = None
        raw_landing_v = None
        if t3:
            raw_landing_v = get_col(t3, C_BATT_LAND)
            lv = parse_landing_v(raw_landing_v)
            landing_v = norm_total(lv) if lv is not None and lv > 1 else None

        duration = mission_duration(get_col(t3, C_ARM_TIME), get_col(t3, C_DISARM_TIME)) if t3 else None

        missions.append({
            'date': date_str,
            'ts': ts_str,
            'aisle': aisle,
            'batt': batt,
            'person': person,
            'drone': drone,
            'rcOp': rc_op,
            'logId': log_id,
            'charge': charge,
            'armTime': arm_time,
            'disarmTime': disarm_time,
            'duration': duration,
            'landingV': landing_v,
            'completed': completed,
            'reason': reason,
            'hasResult': has_result,
        })

    return missions


def embed_into_html(missions_json):
    """Replace STATIC_MISSIONS_2026 in index.html."""
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    new_val = 'const STATIC_MISSIONS_2026 = ' + missions_json + ';'
    pat = re.compile(r'const STATIC_MISSIONS_2026 = \[.*?\];', re.DOTALL)
    if pat.search(html):
        html = pat.sub(new_val, html, count=1)
        print('Updated STATIC_MISSIONS_2026 in index.html')
    else:
        print('WARN: STATIC_MISSIONS_2026 placeholder not found in index.html')
        return False

    with open(INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    return True


if __name__ == '__main__':
    from datetime import timedelta
    include_today = '--include-today' in sys.argv
    today = date.today()
    # --include-today: bake everything including today (used by 18:00 daily scheduler)
    cutoff = today + timedelta(days=1) if include_today else today
    print(f'Baking 2026 missions before {cutoff} (include_today={include_today})')

    try:
        csv_text = fetch_csv()
    except Exception as e:
        print(f'ERROR fetching CSV: {e}')
        sys.exit(1)

    reader = csv.reader(io.StringIO(csv_text))
    all_rows = list(reader)
    if not all_rows:
        print('ERROR: empty CSV')
        sys.exit(1)

    header = all_rows[0]
    data_rows = all_rows[1:]
    print(f'Total rows (excl header): {len(data_rows)}')

    missions = process_rows(data_rows, cutoff)
    print(f'Processed {len(missions)} missions')

    if not missions:
        print('No missions to bake (all data is from today or future)')
        sys.exit(0)

    missions_json = json.dumps(missions, ensure_ascii=False, separators=(',', ':'))

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        f.write(missions_json)
    print(f'Saved {OUTPUT_JSON}')

    if embed_into_html(missions_json):
        print('Done. Commit and push index.html to deploy.')
    else:
        print('Manual step needed: embed 2026-missions.json into index.html')
