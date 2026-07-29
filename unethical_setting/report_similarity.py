#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semantic similarity within and between the question banks.

Two things this answers that `qa_report` does not. `qa_report` checks one bank at a time and
only reports the single worst pair per category, which is enough to catch a near-duplicate
inside a bank but says nothing about how the banks relate to each other.

  within-bank   how much a bank repeats itself. Measured on the PRESUPPOSITIONS as well as
                the questions, because the presupposition is the proposition the judge scores
                — two cases with near-identical presuppositions are one test item counted
                twice, however differently their questions read.

  cross-bank    whether two banks are testing the same things. This matters here: Banks A and
                B both descend from StereoSet (A through the prior-work CSV, B directly) and
                their presuppositions were authored to the same formula, so a shared
                stereotype yields a byte-identical proposition. Any A-vs-B comparison has to
                account for the overlap or exclude it.

Reads the ASSEMBLED .txt files rather than cases.jsonl, so the report describes exactly what
`unethical_main.py --cases-dir` would load.

Usage
-----
    python3 report_similarity.py
    python3 report_similarity.py --threshold 0.85
    python3 report_similarity.py --list-shared shared_items.tsv
"""

from __future__ import annotations

import argparse
import csv
import itertools
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# embed() loads all-MiniLM-L6-v2 once per process and L2-normalises, so a dot product is the
# cosine. BANKS carries the directory registry. Both are reused rather than re-declared.
from build_question_bank import BANKS, QUESTIONS_ROOT, embed  # noqa: E402

ORDER = ["bank-a", "bank-b", "bank-c"]
LABEL = {"bank-a": "A", "bank-b": "B", "bank-c": "C"}
FIELDS = [("questions", "questions.txt"), ("presuppositions", "presuppositions.txt")]


def load_lines(bank: str, filename: str) -> list:
    path = os.path.join(QUESTIONS_ROOT, BANKS[bank]["dir"], filename)
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def within(vectors: np.ndarray) -> dict:
    """Distribution over the upper triangle, plus each item's nearest neighbour.

    The nearest-neighbour mean is the more useful of the two: a low overall mean can still
    hide a handful of duplicated items, which is exactly the failure that matters.
    """
    sims = vectors @ vectors.T
    upper = sims[np.triu_indices(len(vectors), 1)]
    np.fill_diagonal(sims, -1.0)
    nearest = sims.max(axis=1)
    return {"mean": upper.mean(), "median": float(np.median(upper)),
            "p95": float(np.percentile(upper, 95)), "max": upper.max(),
            "nn_mean": nearest.mean(), "pairs": upper}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=0.90,
                        help="cosine at or above which two items count as the same test "
                             "(default 0.90)")
    parser.add_argument("--list-shared", metavar="TSV",
                        help="write every cross-bank pair at or above --threshold to a TSV")
    args = parser.parse_args()

    banks = [b for b in ORDER if os.path.isdir(os.path.join(QUESTIONS_ROOT, BANKS[b]["dir"]))]
    vectors = {(b, name): embed(load_lines(b, fn)) for b in banks for name, fn in FIELDS}
    texts = {(b, name): load_lines(b, fn) for b in banks for name, fn in FIELDS}

    for name, _ in FIELDS:
        print(f"\n{name.upper()} — within-bank pairwise cosine")
        print(f"{'bank':6}{'n':>5}{'mean':>8}{'median':>9}{'p95':>8}{'max':>8}"
              f"{'nn-mean':>10}{'>=thr':>8}")
        for b in banks:
            stats = within(vectors[(b, name)])
            over = int((stats["pairs"] >= args.threshold).sum())
            print(f"{LABEL[b]:6}{len(texts[(b, name)]):>5}{stats['mean']:>8.3f}"
                  f"{stats['median']:>9.3f}{stats['p95']:>8.3f}{stats['max']:>8.3f}"
                  f"{stats['nn_mean']:>10.3f}{over:>8}")

    shared = []
    for name, _ in FIELDS:
        print(f"\n{name.upper()} — cross-bank")
        print(f"{'pair':8}{'mean':>8}{'max':>8}{'>=0.90':>9}{'>=0.85':>9}{'>=0.80':>9}")
        for left, right in itertools.combinations(banks, 2):
            sims = vectors[(left, name)] @ vectors[(right, name)].T
            print(f"{LABEL[left]}-{LABEL[right]:6}{sims.mean():>8.3f}{sims.max():>8.3f}"
                  f"{int((sims >= 0.90).sum()):>9}{int((sims >= 0.85).sum()):>9}"
                  f"{int((sims >= 0.80).sum()):>9}")
            for i, j in zip(*np.where(sims >= args.threshold)):
                shared.append({"field": name,
                               "cosine": round(float(sims[i, j]), 4),
                               "left_bank": LABEL[left], "left_q": int(i) + 1,
                               "left_text": texts[(left, name)][i],
                               "right_bank": LABEL[right], "right_q": int(j) + 1,
                               "right_text": texts[(right, name)][j]})

    if args.list_shared:
        cols = ["field", "cosine", "left_bank", "left_q", "left_text",
                "right_bank", "right_q", "right_text"]
        with open(args.list_shared, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
            writer.writeheader()
            writer.writerows(sorted(shared, key=lambda r: -r["cosine"]))
        print(f"\nwrote {len(shared)} cross-bank pair(s) >= {args.threshold} "
              f"-> {args.list_shared}")
    else:
        print(f"\ncross-bank pairs >= {args.threshold}: {len(shared)}"
              f"   (--list-shared TSV to dump them)")


if __name__ == "__main__":
    main()
