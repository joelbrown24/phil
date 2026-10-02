"""List forecasts/bets that changed in the working tree (i.e. just settled).

Usage: python3 strategy/tools/settled_diff.py [journal/forecasts.jsonl|journal/ledger.jsonl]
Reads `git diff -U0` itself so no shell pipe is needed.
"""
import json
import subprocess
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "journal/forecasts.jsonl"
diff = subprocess.run(["git", "diff", "-U0", path], capture_output=True, text=True).stdout
for line in diff.splitlines():
    if not line.startswith("+{"):
        continue
    r = json.loads(line[1:])
    mkt = r.get("market_prob", r.get("market_mid", r.get("market_prob_at_entry",
                r.get("market_prob_at_record"))))
    status = r.get("status") or r.get("result") or r.get("settled_outcome")
    dbrier = None
    if mkt is not None and r.get("est_prob") is not None and status in ("won", "lost"):
        y = 1.0 if status == "won" else 0.0
        dbrier = round((r["est_prob"] - y) ** 2 - (mkt - y) ** 2, 4)
    print(r.get("id"), r.get("category"), r.get("skip_reason", r.get("edge_class")),
          repr(r.get("outcome")), r.get("est_prob"), mkt, status, dbrier,
          r.get("question", "")[:90])
