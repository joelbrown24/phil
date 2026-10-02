"""Read an xtracker.polymarket.com tracking period's raw counts (resolver source for
"Elon Musk # tweets <period>?" markets; playbook Musk section).

Usage: python3 strategy/tools/xtracker.py <tracking_id> [<hh_from> <hh_to>]
  Prints cumulative, the hourly series (UTC), per-day totals, and, if an hour window
  is given (e.g. 2 15), the per-day sum over hours hh_from..hh_to inclusive.
List tracking ids: python3 strategy/tools/xtracker.py --list [user]
Uses curl (same fingerprint reason as gamma.py). Never trust the API `pace` field.
"""
import collections
import json
import subprocess
import sys

BASE = "https://xtracker.polymarket.com/api"


def get(path):
    raw = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", BASE + path],
                         capture_output=True, text=True).stdout
    return json.loads(raw)


def unwrap(d):
    return d.get("data", d) if isinstance(d, dict) else d


if sys.argv[1] == "--list":
    user = sys.argv[2] if len(sys.argv) > 2 else "elonmusk"
    d = unwrap(get(f"/users/{user}?platform=x&stats=true"))
    for t in d.get("trackings", []):
        print(t.get("id"), t.get("startDate"), t.get("endDate"), t.get("title"))
    sys.exit(0)

d = unwrap(get(f"/trackings/{sys.argv[1]}?includeStats=true"))
stats = d.get("stats", {})
print("title", d.get("title"), "start", d.get("startDate"), "end", d.get("endDate"))
print("cumulative", stats.get("cumulative"), "daysElapsed", stats.get("daysElapsed"),
      "daysRemaining", stats.get("daysRemaining"))
rows = stats.get("daily") or []
per_day = collections.Counter()
win = collections.Counter()
lo = hi = None
if len(sys.argv) >= 4:
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
total = 0
for r in rows:
    ts = r.get("date") or r.get("timestamp") or r.get("hour")
    c = r.get("count", r.get("value", 0)) or 0
    total += c
    day, hh = ts[:10], int(ts[11:13]) if len(ts) > 12 else 0
    per_day[day] += c
    if lo is not None and lo <= hh <= hi:
        win[day] += c
    if c:
        print(ts, c)
print("sum_of_series", total)
for day in sorted(per_day):
    extra = f" window{lo}-{hi}={win[day]}" if lo is not None else ""
    print("day", day, per_day[day], extra)
if lo is not None:
    # All-windows bootstrap: every sliding (hi-lo+1)-hour window over the
    # completed hourly series (playbook 2026-09-25: est = unshaded bootstrap).
    import datetime
    width = hi - lo + 1
    hourly = collections.Counter()
    for r in rows:
        ts = r.get("date") or r.get("timestamp") or r.get("hour")
        hourly[ts[:13]] += r.get("count", r.get("value", 0)) or 0
    keys = sorted(hourly)
    t0 = datetime.datetime.strptime(keys[0], "%Y-%m-%dT%H")
    t1 = datetime.datetime.strptime(keys[-1], "%Y-%m-%dT%H")
    series = []
    t = t0
    while t <= t1:
        series.append(hourly.get(t.strftime("%Y-%m-%dT%H"), 0))
        t += datetime.timedelta(hours=1)
    sums = sorted(sum(series[i:i + width]) for i in range(len(series) - width + 1))
    if sums:
        print(f"sliding {width}h windows n={len(sums)}",
              "quantiles 10/25/50/75/90:",
              [sums[int(q * (len(sums) - 1))] for q in (0.1, 0.25, 0.5, 0.75, 0.9)])
        for k in (4, 8, 12, 16, 20, 24, 32):
            print(f"  P(sum<={k}) = {sum(1 for s in sums if s <= k) / len(sums):.3f}")
