"""Print a gamma market's rules, end date, outcomes, prices and token ids.

Usage: python3 strategy/tools/gamma.py <market_id> [<market_id> ...]
"""
import json
import subprocess
import sys

for mid in sys.argv[1:]:
    # curl, not urllib: same fingerprint issue quote.py documents for the CLOB.
    raw = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0",
                          f"https://gamma-api.polymarket.com/markets/{mid}"],
                         capture_output=True, text=True).stdout
    m = json.loads(raw)
    print(json.dumps({k: m.get(k) for k in (
        "id", "question", "createdAt", "startDate", "endDate", "outcomes", "outcomePrices", "bestBid", "bestAsk",
        "clobTokenIds", "resolutionSource", "description")}, indent=1))
