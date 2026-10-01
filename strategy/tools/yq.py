"""Yahoo chart quote: last price, session high/low and month high/low for touch rungs.

Usage: python3 strategy/tools/yq.py OPEN EWY SI=F
"""
import json
import subprocess
import sys

for sym in sys.argv[1:]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d"
    raw = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url], capture_output=True, text=True).stdout
    try:
        r = json.loads(raw)["chart"]["result"][0]
    except Exception:
        print(sym, "ERR", raw[:200])
        continue
    q = r["indicators"]["quote"][0]
    hi = [x for x in q["high"] if x is not None]
    lo = [x for x in q["low"] if x is not None]
    meta = r["meta"]
    print(sym, "last", meta.get("regularMarketPrice"), "dayHigh", meta.get("regularMarketDayHigh"),
          "dayLow", meta.get("regularMarketDayLow"), "1moHigh", round(max(hi), 3), "1moLow", round(min(lo), 3))
    if "--bars" in sys.argv:
        import datetime
        for t, h, l, c in zip(r["timestamp"], q["high"], q["low"], q["close"]):
            d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")
            print("  ", d, "H", h and round(h, 3), "L", l and round(l, 3), "C", c and round(c, 3))
