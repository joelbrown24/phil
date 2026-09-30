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
    mkt = r.get("market_prob", r.get("market_mid", r.get("market_prob_at_entry")))
    status = r.get("status") or r.get("result") or r.get("settled_outcome")
    print(r.get("id"), r.get("category"), r.get("skip_reason", r.get("edge_class")),
          repr(r.get("outcome")), r.get("est_prob"), mkt, status, r.get("question", "")[:90])
