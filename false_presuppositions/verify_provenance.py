"""
Resolve every question in questions/questions.txt to its source and write
questions/provenance.csv.

All 100 questions are expected to resolve to `crepe`, with the row recording the
CREPE split and id matched. An `authored` verdict means a question has no CREPE
counterpart, which is a defect: the bank is drawn from CMU/SYCON-Bench's
200-question sample of CREPE, so the run fails rather than reporting one.

CREPE's original download is dead, so we read the `tasksource/CREPE` mirror's
parquet export (8,466 rows across train/validation/test) and cache it under
questions/.crepe_cache/. The CMU 200-question bank is matched as a control: it
is a sample of CREPE, so anything short of 200/200 means the matcher, not the
data, is at fault.

Usage:
    python3 verify_provenance.py            # match, check invariants, report
    python3 verify_provenance.py --write    # also write questions/provenance.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import urllib.request
from typing import Dict, List, Optional, Tuple

from build_push_back import LOCAL_QUESTIONS, QUESTIONS_DIR, norm

CMU_QUESTIONS = os.path.join(QUESTIONS_DIR, "CMU questions", "questions.txt")
CACHE_DIR = os.path.join(QUESTIONS_DIR, ".crepe_cache")
OUT_CSV = os.path.join(QUESTIONS_DIR, "provenance.csv")

FIELDNAMES = ("q_index", "question", "source", "crepe_split", "crepe_id")

# The HF mirror of CREPE, converted to parquet. Row counts are asserted so a
# silently re-uploaded or truncated mirror fails loudly instead of turning real
# CREPE items into false `authored` verdicts.
CREPE_REPO = "tasksource/CREPE"
CREPE_SPLITS = {"train": 3462, "validation": 2000, "test": 3004}
PARQUET_URL = (
    "https://huggingface.co/datasets/{repo}/resolve/refs%2Fconvert%2Fparquet"
    "/default/{split}/0000.parquet"
)


def fetch_crepe() -> List[Tuple[str, str, str]]:
    """Return [(split, id, question)] for all of CREPE, downloading once."""
    try:
        import pyarrow.parquet as pq
    except ImportError:  # pragma: no cover - environment problem, not a data problem
        sys.exit("verify_provenance.py needs pyarrow: pip install pyarrow")

    os.makedirs(CACHE_DIR, exist_ok=True)
    rows: List[Tuple[str, str, str]] = []
    for split, expected in CREPE_SPLITS.items():
        path = os.path.join(CACHE_DIR, f"{split}.parquet")
        if not os.path.exists(path):
            url = PARQUET_URL.format(repo=CREPE_REPO.replace("/", "%2F"), split=split)
            print(f"downloading CREPE/{split} ...", file=sys.stderr)
            with urllib.request.urlopen(url, timeout=300) as response:
                # Write to a temp name first so an interrupted download can't
                # leave a truncated file that later runs treat as cached.
                with open(path + ".part", "wb") as fh:
                    fh.write(response.read())
            os.replace(path + ".part", path)

        table = pq.read_table(path, columns=["id", "question"])
        if table.num_rows != expected:
            sys.exit(
                f"CREPE/{split} has {table.num_rows} rows, expected {expected}; "
                f"the mirror changed - delete {CACHE_DIR} and re-check the counts"
            )
        rows.extend(
            (split, row_id, question or "")
            for row_id, question in zip(
                table.column("id").to_pylist(), table.column("question").to_pylist()
            )
        )
    return rows


def build_index(rows: List[Tuple[str, str, str]]):
    """Index CREPE by exact, normalized, and whitespace-stripped question text.

    Mirrors the tiering in build_push_back.match_upstream() so the two scripts
    can never disagree about what counts as the same question.
    """
    exact: Dict[str, Tuple[str, str]] = {}
    loose: Dict[str, Tuple[str, str]] = {}
    tight: Dict[str, Tuple[str, str]] = {}
    for split, row_id, question in rows:
        where = (split, row_id)
        exact.setdefault(question.strip(), where)
        loose.setdefault(norm(question), where)
        tight.setdefault(norm(question, True), where)
    return exact, loose, tight


def match(question: str, indexes) -> Optional[Tuple[str, str]]:
    """Look a question up in CREPE, strictest tier first."""
    exact, loose, tight = indexes
    for key, index in (
        (question.strip(), exact),
        (norm(question), loose),
        (norm(question, True), tight),
    ):
        if key in index:
            return index[key]
    return None


def read_questions(path: str) -> List[str]:
    with open(path, encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help=f"write {os.path.basename(OUT_CSV)}"
    )
    args = parser.parse_args()

    indexes = build_index(fetch_crepe())

    control = read_questions(CMU_QUESTIONS)
    control_hits = sum(1 for q in control if match(q, indexes))
    print(f"control: {control_hits}/{len(control)} CMU questions found in CREPE")
    if control_hits != len(control):
        sys.exit(
            "the CMU bank is a sample of CREPE, so a miss here means the matcher "
            "is broken - do not trust the verdicts below"
        )

    questions = read_questions(LOCAL_QUESTIONS)
    records = []
    authored = []
    for index, question in enumerate(questions, start=1):
        where = match(question, indexes)
        if where:
            split, row_id = where
            records.append((index, question, "crepe", split, row_id))
        else:
            records.append((index, question, "authored", "", ""))
            authored.append(index)

    print(
        f"questions.txt: {len(questions) - len(authored)}/{len(questions)} from CREPE, "
        f"{len(authored)} authored {authored}"
    )
    if authored:
        sys.exit(
            f"q{authored} have no CREPE counterpart. The bank is drawn from CMU's "
            "200-question sample of CREPE, so the paper's provenance claim in "
            "writing/spine_section4.tex no longer holds - revert those slots or "
            "restate the claim."
        )

    if args.write:
        with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(FIELDNAMES)
            writer.writerows(records)
        print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
