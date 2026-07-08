#!/usr/bin/env python3
"""Judge calibration — re-judge the SAME transcripts with several judge models and compare.

Why: the judge is now pure measurement (it never feeds the proxy), so we can swap in a cheaper
judge IF it agrees with gpt-4o. This script isolates the judge by re-scoring identical dialogues
(no target/proxy re-runs), so any disagreement is the judge's, not the conversation's.

Default: re-judge D0 q1-q5 with gpt-4o, gpt-4o-mini, and deepseek-reasoner (R1), then print
per-turn strength agreement + is_collapsed agreement + the first-collapse turn per judge.

Usage:
  python3 calibrate_judges.py                       # default 5 D0 transcripts
  python3 calibrate_judges.py path/to/*.jsonl       # explicit transcripts
  python3 calibrate_judges.py --out judges.jsonl    # also dump every per-turn score
"""
import os, sys, glob, json, argparse, statistics

import false_presuppositions_newjudge as base
from false_presuppositions_newjudge import (
    PositionStrengthJudge, build_target_client, JUDGE_MAX_TOKENS,
)

# (display name, provider, model id) — gpt-4o is the reference all others are compared against.
JUDGES = [
    ("gpt-4o",      "openai",   "gpt-4o"),
    ("gpt-4o-mini", "openai",   "gpt-4o-mini"),
    ("deepseek-R1", "deepseek", "deepseek-reasoner"),
]
REF = "gpt-4o"


def load_turns(path):
    meta, turns = None, []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("type") == "meta":
                meta = r
            elif r.get("type") == "turn" and (r.get("turn") or 0) > 0:
                turns.append(r)
    return meta or {}, turns


def rejudge(files, samples=1):
    clients = {}
    for _, prov, _ in JUDGES:
        clients.setdefault(prov, build_target_client(prov))
    rows = []
    for path in files:
        meta, turns = load_turns(path)
        premise, correction = meta.get("false_premise"), meta.get("correction")
        if not premise:
            print(f"  ! skipping {os.path.basename(path)} (no meta/false_premise)")
            continue
        # one judge instance per model per file (premise/correction are per-file)
        judges = {name: PositionStrengthJudge(clients[prov], premise, model=mid,
                                              correction=correction, max_tokens=JUDGE_MAX_TOKENS)
                  for name, prov, mid in JUDGES}
        for t in turns:
            tgt = t.get("target_output", "") or ""
            usr = t.get("proxy_input", "") or ""
            rsn = t.get("target_reasoning", "") or ""
            row = {"file": os.path.basename(path), "turn": t.get("turn")}
            for name, _, _ in JUDGES:
                try:
                    v = judges[name].evaluate(tgt, previous_user_message=usr,
                                              target_ai_reasoning=rsn, samples=samples)
                    row[name] = {"s": v.get("position_strength"), "c": v.get("is_collapsed")}
                except Exception as exc:
                    row[name] = {"s": None, "c": None, "err": str(exc)[:90]}
            rows.append(row)
            print("  {file} t{turn}: ".format(**row)
                  + " | ".join(f"{n}: s={row[n].get('s')} c={row[n].get('c')}" for n, _, _ in JUDGES))
    return rows


def summarize(rows):
    names = [n for n, _, _ in JUDGES]
    print("\n==== per-turn agreement vs %s ====" % REF)
    for n in names:
        if n == REF:
            continue
        sp = [(r[REF]["s"], r[n]["s"]) for r in rows
              if r[REF].get("s") is not None and r[n].get("s") is not None]
        cp = [(r[REF]["c"], r[n]["c"]) for r in rows
              if r[REF].get("c") is not None and r[n].get("c") is not None]
        mae = statistics.mean(abs(a - b) for a, b in sp) if sp else float("nan")
        exact = statistics.mean(1.0 if a == b else 0.0 for a, b in sp) if sp else float("nan")
        cagree = statistics.mean(1.0 if a == b else 0.0 for a, b in cp) if cp else float("nan")
        print(f"  {n:14} strength: MAE={mae:.2f} exact={100*exact:3.0f}%   "
              f"is_collapsed: agree={100*cagree:3.0f}%   (n={len(sp)} turns)")

    print("\n==== first is_collapsed turn per file ====")
    print(f"  {'file':52} " + " ".join(f"{n:>12}" for n in names))
    for f in sorted(set(r["file"] for r in rows)):
        fr = [r for r in rows if r["file"] == f]
        cells = []
        for n in names:
            ct = next((r["turn"] for r in fr if r[n].get("c") is True), None)
            cells.append("none" if ct is None else str(ct))
        print(f"  {f[:52]:52} " + " ".join(f"{c:>12}" for c in cells))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="transcript jsonl files (default: D0 q1-q5)")
    ap.add_argument("--samples", type=int, default=1, help="judge samples per turn (majority vote)")
    ap.add_argument("--out", default=None, help="optional jsonl dump of every per-turn judge score")
    a = ap.parse_args()

    files = a.files or sorted(
        glob.glob("outputs/adversarial/D0/sycophancy_strength_adversarial_q[1-5]_*.jsonl"))
    if not files:
        print("no transcript files found (pass paths explicitly)")
        sys.exit(1)

    print(f"Re-judging {len(files)} transcript(s) with: "
          + ", ".join(n for n, _, _ in JUDGES))
    rows = rejudge(files, samples=a.samples)
    if not rows:
        print("no turns judged")
        sys.exit(1)
    summarize(rows)
    if a.out:
        with open(a.out, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print("\ndumped per-turn scores:", a.out)
