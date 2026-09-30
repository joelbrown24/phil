"""List USGS earthquakes >= a magnitude since a UTC start (validated-feed sweep).

Usage: python3 strategy/tools/usgs.py 2026-09-28T04:00:00 [minmag=5.5]
"""
import datetime
import json
import sys
import urllib.request

start = sys.argv[1]
minmag = sys.argv[2] if len(sys.argv) > 2 else "5.5"
url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
       f"&starttime={start}&minmagnitude={minmag}&orderby=time-asc")
with urllib.request.urlopen(url, timeout=30) as r:
    data = json.load(r)
for f in data["features"]:
    p = f["properties"]
    t = datetime.datetime.fromtimestamp(p["time"] / 1000, datetime.timezone.utc)
    print(f"{t:%Y-%m-%dT%H:%MZ}  M{p['mag']}  {p['place']}")
print(f"count={len(data['features'])}")

# Empirical mode (captures aftershock clustering that Poisson misses):
# python3 strategy/tools/usgs.py <start> 5.5 <days_left> empirical
# Counts events in every sliding window of <days_left> over the past 365d
# (hourly steps) and reports the final-count distribution given the count so far.
if len(sys.argv) > 4 and sys.argv[4] == "empirical":
    have = len(data["features"])
    days = float(sys.argv[3])
    now = datetime.datetime.now(datetime.timezone.utc)
    hist_start = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
    hurl = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&starttime={hist_start}&minmagnitude={minmag}&orderby=time-asc")
    with urllib.request.urlopen(hurl, timeout=60) as r:
        times = sorted(f["properties"]["time"] / 1000 for f in json.load(r)["features"])
    t0, t1, w = now.timestamp() - 365 * 86400, now.timestamp() - days * 86400, days * 86400
    counts, t = {}, t0
    while t <= t1:
        n = sum(1 for x in times if t <= x < t + w)
        counts[n] = counts.get(n, 0) + 1
        t += 3600
    total = sum(counts.values())
    print(f"history events={len(times)} windows={total}")
    cum = 0.0
    for n in range(0, max(counts) + 1):
        p = counts.get(n, 0) / total
        cum += p
        print(f"final={have + n}  p={p:.3f}  cum<= {cum:.3f}")
    sys.exit(0)

# Optional: bracket probabilities for the final weekly count.
# python3 strategy/tools/usgs.py <start> 5.5 <days_left> <rate1,rate2,...>
if len(sys.argv) > 4:
    from math import exp, factorial
    have = len(data["features"])
    days = float(sys.argv[3])
    rates = [float(x) for x in sys.argv[4].split(",")]

    def pmf(k):
        # Equal-weight Poisson mixture over daily rates (crude overdispersion).
        return sum(exp(-r * days) * (r * days) ** k / factorial(k) for r in rates) / len(rates)

    for total in range(have, have + 16):
        print(f"final={total}  p={pmf(total - have):.3f}  cum<= {sum(pmf(j) for j in range(total - have + 1)):.3f}")
