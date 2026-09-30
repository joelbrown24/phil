#!/usr/bin/env python3
"""Binance spot + measured realized vol for crypto ladder/touch forecasts.

Usage: python3 strategy/tools/spot.py BTCUSDT [days=30]

Prints last price and annualized realized vol from daily closes over the past
<days> days, labelled so touch.py's --vol-source can quote it verbatim
(touch-family ruling DEEP-2026-09-01: no guessed vol inputs).
"""
import datetime
import json
import math
import sys
import urllib.request

sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
base = "https://api.binance.com/api/v3"
with urllib.request.urlopen(f"{base}/ticker/price?symbol={sym}", timeout=20) as r:
    price = float(json.load(r)["price"])
with urllib.request.urlopen(f"{base}/klines?symbol={sym}&interval=1d&limit={days + 1}", timeout=20) as r:
    closes = [float(k[4]) for k in json.load(r)]
rets = [math.log(b / a) for a, b in zip(closes, closes[1:])]
mu = sum(rets) / len(rets)
sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / (len(rets) - 1))
now = datetime.datetime.now(datetime.timezone.utc)
print(f"{sym} spot={price:.2f} at {now:%Y-%m-%dT%H:%MZ}")
print(f"realized vol {days}d daily closes: daily={sd:.4f} ann={sd * math.sqrt(365):.4f} "
      f"(source: Binance {sym} 1d klines, {now:%Y-%m-%d})")
