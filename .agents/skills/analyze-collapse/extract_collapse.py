#!/usr/bin/env python3
"""Extract collapse data from a sycophancy strength-test output folder.

Usage:
    python extract_collapse.py <outputs_dir> [--turn]

<outputs_dir> holds sycophancy_strength_q*.jsonl run logs (one per question).
Each log is JSONL: line 0 = meta, middle = per-turn records, last = result.

Default mode prints the run config + an outcome table for every question.
--turn additionally dumps the collapse-turn detail (false premise, proxy input,
target reasoning/THINK, target output/SAY, judge reason) for COLLAPSED runs only
— the input the per-question mechanism analysis is written from.

When a question has several log files (re-runs), the latest by timestamp wins.
Runs that end on a 'turn' record (no 'result') are INCOMPLETE and excluded from
the collapsed set — they crashed mid-conversation, they did not survive.
"""
import json, glob, os, re, sys

def qnum(f):
    m = re.search(r'_q(\d+)_', os.path.basename(f))
    return int(m.group(1)) if m else None
def stamp(f):
    m = re.search(r'_(\d{8}_\d{6})', f)
    return m.group(1) if m else ""

def latest_per_question(d):
    # match both sycophancy_strength_q*.jsonl and prefixed variants
    # (e.g. sycophancy_strength_llmdecide_q*.jsonl); qnum() filters non-matches.
    best = {}
    for f in glob.glob(os.path.join(d, "sycophancy_strength_*q*.jsonl")):
        q = qnum(f)
        if q is None:
            continue
        if q not in best or stamp(f) > stamp(best[q]):
            best[q] = f
    return dict(sorted(best.items()))

def load(f):
    return [json.loads(l) for l in open(f) if l.strip()]

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python extract_collapse.py <outputs_dir> [--turn]")
    d = sys.argv[1]
    dump_turn = "--turn" in sys.argv[2:]
    files = latest_per_question(d)
    if not files:
        sys.exit(f"no sycophancy_strength_q*.jsonl found in {d}")

    m = load(files[next(iter(files))])[0]
    ap = m.get("adaptive_pressure", {})
    print(f"DIR: {d}")
    print(f"MODE: {ap.get('mode')} | TARGET: {m.get('target_model')} "
          f"| PROXY: {m.get('proxy_model')} | JUDGE: {m.get('judge_model')}")
    print("=" * 72)

    collapsed = []
    n_coll = n_surv = n_inc = 0
    for q, f in files.items():
        L = load(f); res = L[-1]
        turns = [d for d in L if d.get("type") == "turn"]
        if res.get("type") != "result":
            n_inc += 1
            last = turns[-1]["turn"] if turns else None
            print(f"q{q:<2} INCOMPLETE        (stopped at turn {last}, no result)")
            continue
        o = res.get("outcome")
        if o == "collapsed":
            n_coll += 1; collapsed.append((q, f, res))
        elif o == "survived":
            n_surv += 1
        print(f"q{q:<2} {str(o):18s} t={res.get('collapsed_at_turn')} "
              f"state={res.get('collapsed_state')} traj={res.get('strength_trajectory')}")
    print("=" * 72)
    print(f"collapsed={n_coll}  survived={n_surv}  incomplete(excluded)={n_inc}  "
          f"total={len(files)}")

    if not dump_turn:
        return
    print("\n" + "#" * 72)
    print("COLLAPSE-TURN DETAIL (collapsed runs only)")
    print("#" * 72)
    for q, f, res in collapsed:
        L = load(f); meta = L[0]; ct = res.get("collapsed_at_turn")
        tr = next((t for t in L if t.get("type") == "turn" and t["turn"] == ct), None)
        print("\n" + "#" * 60)
        print(f"Q{q} | FALSE PREMISE: {meta.get('false_premise')}")
        print(f"CORRECTION: {meta.get('correction')}")
        print(f"collapse t{ct} [{tr.get('state') if tr else '?'}] "
              f"| JUDGE: {res.get('reason')}")
        if tr:
            print("PROXY> " + (tr.get("proxy_input") or "")[:400])
            print("THINK> " + (tr.get("target_reasoning") or "(none)").strip())
            print("SAY>   " + (tr.get("target_output") or "")[:400])

if __name__ == "__main__":
    main()
