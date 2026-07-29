#!/usr/bin/env python3
"""Extract judge-audit evidence from a sycophancy strength-test run.

Usage:
    python3 extract_judge_audit.py <path> [--all-turns] [--raw]

<path> is either a folder of sycophancy_strength_*q*.jsonl logs (one per
question, latest re-run wins) OR a single .jsonl run file. Each log is JSONL:
line 0 = meta, middle = per-turn records, last = result.

Purpose: this does NOT assume the judge is right. It surfaces, per question, the
judge's *own structured verdict* alongside the raw evidence it was scoring, so a
human/model auditor can decide whether the collapse/survived call was correct.

For every question it prints:
  - the ground-truth rubric (false_premise + correction) and the run outcome,
  - the position-strength trajectory annotated with the judge's per-turn
    is_collapsed / reasserts_correction flags,
  - the DECISIVE turns in full — the target's SAY (untruncated), the proxy push,
    and the judge's structured fields (position_strength, is_collapsed,
    reasserts_correction, partial_sycophancy, affirmed_proposition, reason).

Decisive turns, auto-selected:
  - collapsed run : turn 0 baseline (the original correct answer), the turn
    before collapse (last non-zero), and the collapse turn itself.
  - survived run  : turn 0 baseline, the lowest-strength turn (closest it came),
    and the final scored turn (candidates for a MISSED collapse).
--all-turns dumps every scored turn instead. --raw also prints the judge's raw blob.

The judge only sees the target's SAY (output), not its THINK — so audit the SAY
against the premise/correction. THINK is printed only for the collapse turn as
interpretive context (e.g. to spot conscious-override), never as the thing judged.
"""
import json, glob, os, re, sys

BASE_CAP = 900       # chars of the turn-0 baseline SAY
SAY_CAP  = 3200      # chars of a decisive-turn SAY (want the full reply)

def qnum(f):
    m = re.search(r'_q(\d+)_', os.path.basename(f))
    return int(m.group(1)) if m else None
def stamp(f):
    m = re.search(r'_(\d{8}_\d{6})', f)
    return m.group(1) if m else ""

def latest_per_question(d):
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

def jflag(j, k, dash="-"):
    if not isinstance(j, dict) or k not in j or j[k] is None:
        return dash
    v = j[k]
    if isinstance(v, bool):
        return "Y" if v else "n"
    return str(v)

def scored_turns(L):
    return [t for t in L if t.get("type") == "turn"
            and t.get("position_strength") is not None]

def dump_turn(t, say_cap=SAY_CAP, show_think=False, show_raw=False):
    j = t.get("judge") or {}
    ps = t.get("position_strength")
    print(f"  -- turn {t.get('turn')} | state={t.get('state')} "
          f"| position_strength={ps} "
          f"| is_collapsed={jflag(j,'is_collapsed')} "
          f"| reasserts_correction={jflag(j,'reasserts_correction')} "
          f"| partial_sycophancy={jflag(j,'partial_sycophancy')}")
    print("  PROXY> " + (t.get("proxy_input") or "").strip())
    ap = j.get("affirmed_proposition") if isinstance(j, dict) else None
    if ap:
        print("  JUDGE.affirmed_proposition> " + str(ap).strip())
    print("  JUDGE.reason> " + (j.get("reason") if isinstance(j, dict) else "(none)"))
    if show_think:
        print("  THINK> " + (t.get("target_reasoning") or "(none)").strip())
    print("  SAY>   " + (t.get("target_output") or "").strip()[:say_cap])
    if show_raw and isinstance(j, dict) and j.get("raw"):
        print("  JUDGE.raw> " + str(j.get("raw")).strip()[:1500])
    print()

def audit_file(f, q, all_turns, show_raw):
    L = load(f); meta = L[0]; res = L[-1]
    turns = [t for t in L if t.get("type") == "turn"]
    scored = scored_turns(L)
    print("#" * 68)
    label = f"Q{q}" if q is not None else os.path.basename(f)
    print(f"{label} | JUDGE: {meta.get('judge_model')} | TARGET: {meta.get('target_model')}")
    print(f"FALSE PREMISE: {meta.get('false_premise')}")
    print(f"CORRECTION:    {meta.get('correction')}")

    if res.get("type") != "result":
        last = turns[-1]["turn"] if turns else None
        print(f"OUTCOME: INCOMPLETE (stopped at turn {last}, no result) "
              f"-- no final judge verdict to audit")
        print()
        return
    outcome = res.get("outcome")
    ct = res.get("collapsed_at_turn")
    print(f"OUTCOME (judge): {outcome} | collapsed_at_turn={ct} "
          f"| trajectory={res.get('strength_trajectory')}")

    # annotated trajectory line
    line = []
    for t in scored:
        j = t.get("judge") or {}
        rc = jflag(j, "reasserts_correction")
        line.append(f"t{t['turn']}:{t.get('position_strength')}"
                    f"{'/rc' if rc=='Y' else ''}")
    print("PER-TURN: " + "  ".join(line) + "   (rc = judge says reasserts_correction)")
    print()

    # baseline (turn 0) for the "original correct position"
    t0 = next((t for t in turns if t.get("turn") == 0), None)
    if t0:
        print("  == BASELINE turn 0 (original answer, pre-pressure) ==")
        print("  SAY0>  " + (t0.get("target_output") or "").strip()[:BASE_CAP])
        print()

    if all_turns:
        decisive = scored
    elif outcome == "collapsed":
        pre = [t for t in scored if t["turn"] < (ct or 10**9)]
        pick = {ct}
        if pre:
            pick.add(pre[-1]["turn"])
        decisive = [t for t in scored if t["turn"] in pick]
    else:  # survived (or other)
        if scored:
            lo = min(scored, key=lambda t: t.get("position_strength"))
            last = scored[-1]
            pick = {lo["turn"], last["turn"]}
            decisive = [t for t in scored if t["turn"] in pick]
        else:
            decisive = []

    for t in decisive:
        show_think = (t.get("turn") == ct)   # THINK only on the collapse turn
        dump_turn(t, show_think=show_think, show_raw=show_raw)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if not args:
        sys.exit("usage: python3 extract_judge_audit.py <folder|file.jsonl> "
                 "[--all-turns] [--raw]")
    path = args[0]
    all_turns = "--all-turns" in flags
    show_raw = "--raw" in flags

    if os.path.isfile(path):
        files = {qnum(path): path}
    elif os.path.isdir(path):
        files = latest_per_question(path)
        if not files:
            sys.exit(f"no sycophancy_strength_*q*.jsonl found in {path}")
    else:
        sys.exit(f"not a file or folder: {path}")

    any_meta = load(next(iter(files.values())))[0]
    print(f"PATH: {path}")
    print(f"TARGET: {any_meta.get('target_model')} | PROXY: {any_meta.get('proxy_model')} "
          f"| JUDGE: {any_meta.get('judge_model')} | judge_enabled={any_meta.get('judge_enabled')}")
    print("=" * 68)
    for q, f in files.items():
        audit_file(f, q, all_turns, show_raw)

if __name__ == "__main__":
    main()
