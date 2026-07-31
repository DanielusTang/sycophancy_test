"""
Progress report for the two-arm ToF/NoF batch: DONE vs NOT-DONE per question.

A run is DONE when turn `--expect-turns` carries a judge verdict (with
--no-stop-on-collapse nothing exits early, so the last turn is the finish line).
NOT-DONE rows show the highest turn reached so far.

Usage:
    python3 status_tof.py [--expect-turns 4] [--first 2] [--last 25]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
from typing import Dict, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = {
    "A cmu_fixed": os.path.join(
        HERE, "outputs/naturalistic/sonnet_5/tactics_ablation/cmu_fixed/deepseek-v4-pro"),
    "B mafalda": os.path.join(
        HERE, "outputs/naturalistic/sonnet_5/tactics_ablation/naturalistic_tof/deepseek-v4-pro"),
}


def scan_arm(directory: str) -> Dict[int, dict]:
    """Newest log per question -> {max_turn, judged_turns, strengths}."""
    by_q: Dict[int, Tuple[str, dict]] = {}
    for path in sorted(glob.glob(os.path.join(directory, "sycophancy_strength_*.jsonl"))):
        match = re.search(r"_q(\d+)_", os.path.basename(path))
        if not match:
            continue
        q = int(match.group(1))
        turns: Dict[int, Optional[dict]] = {}
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue  # a run still writing may leave a partial last line
                    if record.get("type") == "turn":
                        turns[record["turn"]] = record.get("judge")
        except FileNotFoundError:
            continue
        info = {
            "max_turn": max(turns) if turns else -1,
            "judged": sorted(t for t, j in turns.items() if j),
            "strengths": [(t, (turns[t] or {}).get("position_strength"))
                          for t in sorted(turns)],
        }
        # sorted() puts the newest timestamp last, so this keeps the latest attempt
        by_q[q] = (path, info)
    return {q: info for q, (path, info) in by_q.items()}


def live_runs() -> int:
    try:
        out = subprocess.run(["ps", "ax"], capture_output=True, text=True, check=False).stdout
    except OSError:
        return -1
    return sum(1 for line in out.splitlines() if "false_presuppositions_main.py" in line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--expect-turns", type=int, default=4)
    parser.add_argument("--first", type=int, default=2)
    parser.add_argument("--last", type=int, default=25)
    args = parser.parse_args()

    wanted = list(range(args.first, args.last + 1))
    scans = {name: scan_arm(path) for name, path in ARMS.items()}

    print(f"live run processes: {live_runs()}")
    for name in ARMS:
        scan = scans[name]
        done = [q for q in wanted if args.expect_turns in scan.get(q, {}).get("judged", [])]
        notdone = [q for q in wanted if q not in done]
        print()
        print(f"--- ARM {name} --- DONE {len(done)}/{len(wanted)}")
        print(f"  DONE     : {'none' if not done else ', '.join('q%d' % q for q in done)}")
        if notdone:
            parts = []
            for q in notdone:
                info = scan.get(q)
                if info is None:
                    parts.append(f"q{q}(no log)")
                else:
                    parts.append(f"q{q}(turn {info['max_turn']})")
            print(f"  NOT DONE : {', '.join(parts)}")
        else:
            print("  NOT DONE : none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
