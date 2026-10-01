"""Parcl home-value bracket helper (playbook 'New benchmark: Parcl Labs daily index').

Usage:
  python3 strategy/tools/parcl.py find "<search text>"      # gamma public-search, open markets
  python3 strategy/tools/parcl.py hist <parcl_id> [<id>...]  # last 10 daily prints per id
  python3 strategy/tools/parcl.py moves <parcl_id> <days> <delta_idx> [<prior2d>]
      # empirical frequency (2020-) of a <days>-horizon index move >= delta (sign-aware),
      # unconditional and conditioned on a prior-2d trend of the same sign as <prior2d>
Parcl ids (from the Sep 30 set): NYC 5372594, Chicago 2899845, LA 2900078,
DC 2900475, SF 2900336, US 5826765.
"""
import json
import subprocess
import sys


def curl(url, body=None):
    cmd = ["curl", "-s", "-A", "Mozilla/5.0", url]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)


def history(pid):
    r = curl("https://api-app-service.parcllabs.com/v1/price-feeds/history",
             {"parcl_ids": [int(pid)], "start_date": "2020-01-01"})
    rows = r["series"][str(pid)]["data"]
    out = []
    for x in rows:
        d = x.get("date") or x.get("as_of_date")
        v = x.get("price_feed") or x.get("value") or x.get("price")
        if d is not None and v is not None:
            out.append((d[:10], float(v)))
    return sorted(out)


def main():
    cmd = sys.argv[1]
    if cmd == "find":
        # open gamma markets ending in [min, max] whose question contains "home value"
        lo, hi = sys.argv[2], sys.argv[3]
        for off in range(0, 5000, 500):
            ms = curl("https://gamma-api.polymarket.com/markets?closed=false&limit=500&offset=%d"
                      "&end_date_min=%s&end_date_max=%s" % (off, lo, hi))
            for m in ms:
                if "home value" in (m.get("question") or ""):
                    print(m.get("id"), m.get("endDate", "")[:10], m.get("bestBid"), m.get("bestAsk"),
                          m.get("liquidity", "")[:7], m.get("question"))
            if len(ms) < 500:
                break
    elif cmd == "event":
        # list a gamma event's open markets by event slug (e.g. from a sibling market's events[0].slug)
        for ev in curl("https://gamma-api.polymarket.com/events?slug=" + sys.argv[2]):
            print(ev.get("id"), ev.get("slug"), ev.get("endDate"))
            for m in ev.get("markets", []):
                if not m.get("closed"):
                    print(" ", m.get("id"), m.get("bestBid"), m.get("bestAsk"), m.get("question"))
    elif cmd == "series":
        # open events of a series (e.g. median-home-price-nyc), with their open markets
        for s in sys.argv[2:]:
            for ser in curl("https://gamma-api.polymarket.com/series?slug=" + s):
                evs = ser.get("events", [])
                print(s, "events:", len(evs), [(e.get("slug", "")[:70], e.get("closed")) for e in evs[-4:]])
                for e in evs:
                    if e.get("closed"):
                        continue
                    for ev in curl("https://gamma-api.polymarket.com/events?slug=" + e["slug"]):
                        print(s, ev.get("slug"), ev.get("endDate"))
                        for m in ev.get("markets", []):
                            if not m.get("closed"):
                                print(" ", m.get("id"), m.get("bestBid"), m.get("bestAsk"),
                                      str(m.get("liquidity"))[:7], m.get("question"))
    elif cmd == "eventof":
        for mid in sys.argv[2:]:
            for m in curl("https://gamma-api.polymarket.com/markets?closed=true&id=" + mid):
                print(mid, [(e.get("slug"), e.get("seriesSlug"), [t.get("slug") for t in e.get("tags") or []])
                            for e in m.get("events", [])])
    elif cmd == "hist":
        for pid in sys.argv[2:]:
            h = history(pid)
            print(pid, h[-10:])
    elif cmd == "moves":
        pid, days, delta = sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
        prior = float(sys.argv[5]) if len(sys.argv) > 5 else None
        v = [x[1] for x in history(pid)]
        n = hit = cn = chit = 0
        for i in range(2, len(v) - days):
            mv = v[i + days] - v[i]
            h = mv >= delta if delta >= 0 else mv <= delta
            n += 1
            hit += h
            if prior is not None and (v[i] - v[i - 2]) * prior > 0:
                cn += 1
                chit += h
        print(json.dumps({"pid": pid, "days": days, "delta": delta, "uncond": f"{hit}/{n}",
                          "uncond_rate": round(hit / n, 4) if n else None,
                          "cond_same_trend": f"{chit}/{cn}" if prior is not None else None}))


if __name__ == "__main__":
    main()
