import json, re

path = "C:/Users/A/AppData/Local/Temp/dashboard-repo/index.html"
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

with open('C:/Users/A/AppData/Local/Temp/old-missions.json', encoding='utf-8') as f:
    missions_js = f.read()

# Replace just the static missions array
old_pat = re.compile(r'const STATIC_MISSIONS_2025 = \[.*?\];', re.DOTALL)
new_val = 'const STATIC_MISSIONS_2025 = ' + missions_js + ';'

if old_pat.search(html):
    html = old_pat.sub(new_val, html, count=1)
    print("Updated STATIC_MISSIONS_2025")
else:
    print("FAIL: STATIC_MISSIONS_2025 not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Done. File length: {len(html)}")
