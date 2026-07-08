#!/usr/bin/env python3
"""Print a q1-q25 x 4-condition progress table for the ablation runs."""
import glob, os, subprocess, re

conds = ["qwen8b_off", "qwen8b_on", "qwen235b_off", "qwen235b_on"]
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ablasion_qwen_outputs")
ps = subprocess.run("ps aux | grep '[f]alse_presuppositions_naturalistic.py'",
                    shell=True, capture_output=True, text=True).stdout

def live(cond, q):
    return any(f"--tag {cond}" in l and f"--start {q-1} " in l for l in ps.splitlines())

import json

def parse(jf):
    """Return (n_turns, last_strength, outcome) by parsing JSONL lines."""
    turns, last, outcome = 0, None, None
    for line in open(jf):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if "turn" in d and isinstance(d["turn"], int):
            turns = max(turns, d["turn"])
        if "position_strength" in d and d["position_strength"] is not None:
            last = d["position_strength"]
        if d.get("outcome"):
            outcome = d["outcome"]
    return turns, last, outcome

def cell(cond, q):
    jfs = sorted(glob.glob(f"{BASE}/{cond}/sycophancy_strength_naturalistic_q{q}_*.jsonl"),
                 key=os.path.getmtime)
    if not jfs and not live(cond, q):
        return "·", None
    t, last, _ = parse(jfs[-1]) if jfs else (0, None, None)
    if live(cond, q):
        return f"⏳t{t}", "run"
    if last is None:
        return "·", None
    if last == 0:                       # full collapse
        return f"💥t{t}", "coll"
    return f"🛡{t}t", "surv"             # finished without collapse (reached cap)

W = 8
now = subprocess.run("date +%H:%M:%S", shell=True, capture_output=True, text=True).stdout.strip()
grid = {(c, q): cell(c, q) for c in conds for q in range(1, 26)}
maxq = max([q for (c, q), v in grid.items() if v[0] != "·"] + [1])
hi = min(25, maxq + 1)

print("progress @", now)
print(f"{'cond':<13}" + "".join(f"{'q'+str(q):<{W}}" for q in range(1, hi + 1)))
print("-" * (13 + W * hi))
tally = {"coll": 0, "surv": 0, "run": 0}
for c in conds:
    print(f"{c:<13}" + "".join(f"{grid[(c,q)][0]:<{W}}" for q in range(1, hi + 1)))
    for q in range(1, 26):
        k = grid[(c, q)][1]
        if k:
            tally[k] = tally.get(k, 0) + 1
print("-" * (13 + W * hi))
print(f"collapsed={tally['coll']}  survived={tally['surv']}  running={tally['run']}  "
      f"done={tally['coll']+tally['surv']}/100")
