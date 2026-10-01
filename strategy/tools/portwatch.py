"""IMF PortWatch daily chokepoint transits (validated-feed list, playbook 2026-09-30).

Usage: python3 strategy/tools/portwatch.py <name-like> [<since YYYY-MM-DD>]
  e.g. python3 strategy/tools/portwatch.py Hormuz 2026-09-10
Prints date, n_total and the trailing 7-day MA of n_total.
"""
import json
import subprocess
import sys
import urllib.parse

name = sys.argv[1]
since = sys.argv[2] if len(sys.argv) > 2 else "2026-08-01"
where = f"portname like '%{name}%' AND date >= DATE '{since}'"
url = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/"
       "FeatureServer/0/query?" + urllib.parse.urlencode({
           "where": where, "outFields": "date,portname,n_total", "orderByFields": "date",
           "resultRecordCount": 2000, "f": "json"}))
raw = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url], capture_output=True, text=True).stdout
feats = json.loads(raw).get("features", [])
import datetime
vals = []
for f in feats:
    a = f["attributes"]
    d = a["date"]
    if isinstance(d, (int, float)):
        d = datetime.datetime.fromtimestamp(d / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")
    vals.append((d, a["portname"], a["n_total"]))
quiet = "--summary" in sys.argv
for i, (d, p, n) in enumerate(vals):
    w = [x[2] for x in vals[max(0, i - 6):i + 1]]
    if not quiet or n <= 1:
        print(d, p, n, round(sum(w) / len(w), 2) if len(w) == 7 else "")
print("rows", len(vals), "zero_days", sum(1 for v in vals if v[2] == 0),
      "le1_days", sum(1 for v in vals if v[2] <= 1),
      "mean", round(sum(v[2] for v in vals) / max(1, len(vals)), 2))
