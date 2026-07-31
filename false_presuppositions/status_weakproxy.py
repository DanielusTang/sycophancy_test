"""
Progress report for the weak-proxy CMU-tactics arm: DONE vs NOT-DONE per question.

Companion to status_tof.py, but for a live batch rather than a finished one: NOT-DONE
rows carry the turn reached so far and the latest position_strength, so a stalled run is
visible without opening a log.

A run is DONE when its --tag summary lands (batch_strength_..._summary_*_qN.json), or a
turn is judged is_collapsed (stop-on-collapse is ON here, so that IS the finish line), or
turn --expect-turns is judged. Questions whose .jsonl never appeared are reported
separately as NO OUTPUT — that means the process died before the first API call, which an
aggregate count would otherwise hide.

Usage:
    python3 status_weakproxy.py [--first 2] [--last 25] [--expect-turns 25]
    python3 status_weakproxy.py --all-done-check   # silent; exit 0 iff every run is DONE
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
from typing import Dict, Optional, Set

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(
    HERE, "outputs/naturalistic/sonnet_5/ablation/weakproxy_cmutactics_ablation/cmu_tactics")
LAUNCH_LOGS = os.path.join(HERE, "run_logs_weakproxy_cmu")
# Match on LOG LEVEL, not on words. Everything the runner logs at WARNING is an
# experimental outcome (❌ collapse, 📉 erosion, ⏹️ interrupt), and INFO carries the target's
# and proxy's own prose — so any keyword filter ("error", "quota", "insufficient") fires on
# model text instead of faults. Real faults are logger.error only: "❌ Case N aborted",
# "❌ Experiment aborted", each followed by an exc_info traceback whose lines carry no level
# prefix. A credit-exhaustion 400 or rate-limit exhaustion arrives through that same path.
FAULT_PATTERN = re.compile(r"\| ERROR \||^Traceback|^\s+File \"|^\w+Error:|^anthropic\.")


def scan_question(q: int, expect_turns: int) -> dict:
    """Newest run log for qN -> progress dict. 'jsonl' is None when nothing was written."""
    logs = sorted(glob.glob(os.path.join(
        OUT_DIR, f"sycophancy_strength_naturalistic_q{q}_t*.jsonl")))
    summary = glob.glob(os.path.join(
        OUT_DIR, f"batch_strength_naturalistic_summary_*_q{q}.json"))
    if not logs:
        return {"jsonl": None, "summary": bool(summary)}

    path = logs[-1]  # timestamps sort lexicographically, so this is the latest attempt
    turns: Dict[int, Optional[dict]] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # a run mid-write can leave a partial trailing line
            if record.get("type") == "turn":
                turns[record["turn"]] = record.get("judge") or None

    judged = {t: j for t, j in turns.items() if j}
    collapse_turn = next((t for t in sorted(judged) if judged[t].get("is_collapsed")), None)
    last_judged = max(judged) if judged else None
    return {
        "jsonl": path,
        "summary": bool(summary),
        "max_turn": max(turns) if turns else -1,
        "collapse_turn": collapse_turn,
        "strength": judged[last_judged].get("position_strength") if last_judged else None,
        "reached_budget": last_judged is not None and last_judged >= expect_turns,
    }


def is_done(info: dict) -> bool:
    if info["jsonl"] is None:
        return False
    return bool(info["summary"] or info["collapse_turn"] is not None or info["reached_budget"])


def live_tags() -> Set[int]:
    """Question numbers whose runner process is currently alive, from `--tag qN`.

    A run writes nothing to its .jsonl until the target answers the baseline question,
    which takes tens of seconds with thinking enabled. Without this check an in-flight
    startup is indistinguishable from a process that died, and reporting the two the same
    way turns a healthy launch into a false alarm.
    """
    try:
        out = subprocess.run(["ps", "-eo", "command"], capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return set()  # can't tell — callers treat this as "unknown", not "dead"
    tags = set()
    for line in out.splitlines():
        if "false_presuppositions_main.py" not in line:
            continue
        match = re.search(r"--tag\s+q(\d+)", line)
        if match:
            tags.add(int(match.group(1)))
    return tags


def count_errors() -> list:
    """Genuine faults in the launcher logs as (qN, line) pairs. See FAULT_PATTERN."""
    hits = []
    for path in sorted(glob.glob(os.path.join(LAUNCH_LOGS, "q*.log"))):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    # INFO carries model prose and WARNING carries experimental outcomes;
                    # neither can indicate a fault, and both trip keyword matching.
                    if "| INFO |" in line or "| WARNING |" in line:
                        continue
                    if FAULT_PATTERN.search(line):
                        hits.append((os.path.basename(path)[:-4], line.strip()[:160]))
        except OSError:
            continue
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=int, default=2)
    parser.add_argument("--last", type=int, default=25)
    parser.add_argument("--expect-turns", type=int, default=25)
    parser.add_argument("--all-done-check", action="store_true",
                        help="print nothing; exit 0 iff every question is DONE")
    args = parser.parse_args()

    questions = range(args.first, args.last + 1)
    scans = {q: scan_question(q, args.expect_turns) for q in questions}

    if args.all_done_check:
        return 0 if all(is_done(info) for info in scans.values()) else 1

    alive = live_tags()
    done = [q for q in questions if is_done(scans[q])]
    # No .jsonl yet splits two ways: still starting (process alive) vs actually dead.
    starting = [q for q in questions if scans[q]["jsonl"] is None and q in alive]
    missing = [q for q in questions if scans[q]["jsonl"] is None and q not in alive]
    running = [q for q in questions if not is_done(scans[q]) and scans[q]["jsonl"]]

    collapsed = [q for q in done if scans[q]["collapse_turn"] is not None]
    print(f"=== weakproxy/cmu_tactics q{args.first}-q{args.last} | "
          f"DONE {len(done)}/{len(questions)} | running {len(running) + len(starting)} | "
          f"dead {len(missing)} | collapsed {len(collapsed)} ===")

    if done:
        print("-- DONE --")
        for q in done:
            info = scans[q]
            if info["collapse_turn"] is not None:
                verdict = f"COLLAPSED @ turn {info['collapse_turn']}"
            elif info["reached_budget"]:
                verdict = f"HELD through turn {info['max_turn']}"
            else:
                # Summary written but the turn budget was never reached and nothing
                # collapsed: the run died mid-flight (e.g. a transient API connection
                # error). Counts as did-not-collapse per convention, but it is NOT the
                # same evidence as surviving the full budget — label it distinctly.
                verdict = f"INCOMPLETE @ turn {info['max_turn']} (no collapse)"
            print(f"   q{q:<3} {verdict:<32} finalPS={info['strength']}")

    if running:
        print("-- NOT DONE --")
        for q in running:
            info = scans[q]
            turn = info["max_turn"]
            at = f"turn {turn}" if turn >= 0 else "starting up"
            ps = info["strength"]
            print(f"   q{q:<3} {at:<28} PS={ps if ps is not None else '-'}")

    if starting:
        print(f"-- STARTING (alive, baseline turn not written yet): "
              f"{', '.join('q' + str(q) for q in starting)}")

    if missing:
        print(f"-- DIED (no process, no output): "
              f"{', '.join('q' + str(q) for q in missing)}")

    errors = count_errors()
    if errors:
        print(f"-- ERRORS in launcher logs: {len(errors)} line(s)")
        for name, line in errors[:5]:
            print(f"   {name}: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
