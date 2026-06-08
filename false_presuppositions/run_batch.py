#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch sycophancy runner
=======================

Runs the sycophancy stress test (see sycophancy_pipeline.py) over a *set* of
false-presupposition cases instead of a single hard-coded one.

Each case is one (question, presupposition, correction) triple, read line-by-line
from three parallel files in a folder:

    false_presuppositions/questions/
        questions.txt        # line N: the opening question for case N
        presuppositions.txt  # line N: the false premise the proxy pushes for case N
        corrections.txt      # line N: the correct position the judge should defend

The three files MUST be line-aligned: line N of each file describes the same case.
Blank lines are ignored, but keep the files aligned (don't leave a gap in one only).

For each case it runs a full Orchestrator session and writes into the output
folder (false_presuppositions/outputs/ by default):
    sycophancy_q<N>_<batch-timestamp>.jsonl   # one real-time log per case
    batch_summary_<batch-timestamp>.json      # aggregate: collapse turn per case

Run:
    export DEEPSEEK_API_KEY=sk-xxxx
    python run_batch.py                       # all cases in the folder
    python run_batch.py --limit 5             # only the first 5 cases
    python run_batch.py --max-turns 20 --seed 42
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

from false_presuppositions.sycophancy_pipeline import (
    DEFAULT_MODEL,
    DEFAULT_TARGET_MODEL,
    HumanProxyAgent,
    JudgeAgent,
    Orchestrator,
    TargetAgent,
    build_client,
    logger,
)
import random

DEFAULT_CASES_DIR = "false_presuppositions/questions"
DEFAULT_OUTPUT_DIR = "false_presuppositions/outputs"


def _read_lines(path: str) -> list[str]:
    """Read a file into a list of stripped, non-empty lines."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_cases(cases_dir: str) -> list[dict]:
    """Load line-aligned (question, presupposition, correction) triples from cases_dir."""
    questions = _read_lines(os.path.join(cases_dir, "questions.txt"))
    presuppositions = _read_lines(os.path.join(cases_dir, "presuppositions.txt"))
    corrections = _read_lines(os.path.join(cases_dir, "corrections.txt"))

    counts = {"questions": len(questions),
              "presuppositions": len(presuppositions),
              "corrections": len(corrections)}
    if len(set(counts.values())) != 1:
        raise ValueError(
            "The three files are not line-aligned (different number of non-empty lines): "
            f"{counts}. Make sure line N of each file describes the same case."
        )
    if questions == []:
        raise ValueError(
            f"No cases found in {cases_dir}. Fill questions.txt / presuppositions.txt / "
            "corrections.txt with one item per line (line N aligned across all three files)."
        )

    return [
        {"index": i, "question": q, "presupposition": p, "correction": c}
        for i, (q, p, c) in enumerate(zip(questions, presuppositions, corrections), start=1)
    ]


def run_case(client, case: dict, *, target_model: str, support_model: str,
             max_turns: int, no_judge: bool, seed: int | None, batch_ts: str,
             output_dir: str) -> dict:
    """Run one full sycophancy session for a single case and return its summary."""
    idx = case["index"]
    # Per-case RNG: derived from seed so the whole batch is reproducible, yet each
    # case gets a distinct FSM stream.
    rng = random.Random(None if seed is None else seed + idx)

    target = TargetAgent(client, model=target_model, opening_question=case["question"])
    proxy = HumanProxyAgent(client, case["presupposition"], model=support_model, rng=rng)
    judge = None if no_judge else JudgeAgent(
        client, case["presupposition"], model=support_model, correction=case["correction"]
    )

    output_path = os.path.join(output_dir, f"sycophancy_q{idx}_{batch_ts}.jsonl")
    orch = Orchestrator(
        target=target,
        proxy=proxy,
        judge=judge,
        max_turns=max_turns,
        output_path=output_path,
        opening_question=case["question"],
        correction=case["correction"],
        topic=f"q{idx}",
    )

    logger.info("#" * 70)
    logger.info("### CASE %d/%s", idx, case.get("total", "?"))
    logger.info("#" * 70)

    summary = orch.run()
    summary.update({
        "index": idx,
        "question": case["question"],
        "presupposition": case["presupposition"],
        "correction": case["correction"],
    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch sycophancy stress test over a folder of false-presupposition cases."
    )
    parser.add_argument("--cases-dir", default=DEFAULT_CASES_DIR,
                        help=f"folder with questions/presuppositions/corrections .txt (default {DEFAULT_CASES_DIR})")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"folder for per-case .jsonl logs and the batch summary .json (default {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--limit", type=int, default=None,
                        help="only run the first N cases (default: all)")
    parser.add_argument("--max-turns", type=int, default=99, help="max pressure turns per case (default 99)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"model for the Proxy and Judge (default {DEFAULT_MODEL})")
    parser.add_argument("--target-model", default=DEFAULT_TARGET_MODEL,
                        help=f"model under test (default {DEFAULT_TARGET_MODEL})")
    parser.add_argument("--no-judge", action="store_true", help="disable the real-time judge and early stopping")
    parser.add_argument("--seed", type=int, default=None, help="base random seed (per-case seed = seed + case index)")
    args = parser.parse_args()

    try:
        cases = load_cases(args.cases_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    if args.limit is not None:
        cases = cases[: args.limit]
    for c in cases:
        c["total"] = len(cases)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Please enter your DeepSeek API Key (or set the DEEPSEEK_API_KEY environment variable):")
        api_key = input().strip()
    if not api_key:
        print("❌ API Key cannot be empty")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    client = build_client(api_key)
    batch_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 70)
    logger.info("BATCH sycophancy run | %d case(s) | target=%s | proxy/judge=%s",
                len(cases), args.target_model, args.model)
    logger.info("=" * 70)

    summaries: list[dict] = []
    for case in cases:
        try:
            summary = run_case(
                client, case,
                target_model=args.target_model,
                support_model=args.model,
                max_turns=args.max_turns,
                no_judge=args.no_judge,
                seed=args.seed,
                batch_ts=batch_ts,
                output_dir=args.output_dir,
            )
        except Exception as exc:  # one failing case should not kill the whole batch
            logger.error("❌ Case %d aborted: %s", case["index"], exc, exc_info=True)
            summary = {
                "index": case["index"],
                "outcome": "error",
                "collapsed_at_turn": None,
                "reason": str(exc),
                "question": case["question"],
                "presupposition": case["presupposition"],
                "correction": case["correction"],
                "output_path": None,
            }
        summaries.append(summary)

    # ---- Aggregate summary ----
    summary_path = os.path.join(args.output_dir, f"batch_summary_{batch_ts}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "batch_timestamp": batch_ts,
            "target_model": args.target_model,
            "support_model": args.model,
            "max_turns": args.max_turns,
            "num_cases": len(summaries),
            "num_collapsed": sum(1 for s in summaries if s.get("outcome") == "collapsed"),
            "cases": summaries,
        }, f, ensure_ascii=False, indent=2)

    logger.info("=" * 70)
    logger.info("BATCH COMPLETE — %d/%d collapsed",
                sum(1 for s in summaries if s.get("outcome") == "collapsed"), len(summaries))
    for s in summaries:
        logger.info("  q%-2s | %-9s | collapsed_at_turn=%s | %s",
                    s.get("index"), s.get("outcome"), s.get("collapsed_at_turn"),
                    (s.get("question") or "")[:60])
    logger.info("Summary saved: %s", summary_path)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
