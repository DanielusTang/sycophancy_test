"""
Build questions/push_back.csv: one row of 4 fixed pushback turns for each of the
100 questions in questions/questions.txt.

Every row is copied verbatim from CMU/SYCON-Bench's push_back.csv, so the
`provenance` column reads `sycon` throughout. That is an invariant, not a
coincidence: all 100 questions are drawn from CMU's 200-question bank, and a
question that fails to match upstream is a bug in questions.txt rather than a
question needing pushbacks of its own.

Usage:
    python3 build_push_back.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_DIR = os.path.join(HERE, "questions")
LOCAL_QUESTIONS = os.path.join(QUESTIONS_DIR, "questions.txt")
UPSTREAM_PUSHBACKS = os.path.join(QUESTIONS_DIR, "push_back_upstream_200.csv")
OUT_CSV = os.path.join(QUESTIONS_DIR, "push_back.csv")

TURNS = ("Pushback_1", "Pushback_2", "Pushback_3", "Pushback_4")
FIELDNAMES = ("q_index", "Question", *TURNS, "provenance", "upstream_question")


def norm(text: str, drop_whitespace: bool = False) -> str:
    """Normalize question text for matching against the upstream bank."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = re.sub(r"[^a-z0-9]+", "" if drop_whitespace else " ", text)
    return text if drop_whitespace else " ".join(text.split())


def load_upstream() -> Tuple[Dict[str, dict], Dict[str, dict], Dict[str, dict]]:
    """Index CMU's 200 rows by exact, normalized, and whitespace-stripped text."""
    with open(UPSTREAM_PUSHBACKS, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    exact: Dict[str, dict] = {}
    loose: Dict[str, dict] = {}
    tight: Dict[str, dict] = {}
    for row in rows:
        question = row["Question"].strip()
        exact.setdefault(question, row)
        loose.setdefault(norm(question), row)
        tight.setdefault(norm(question, True), row)
    return exact, loose, tight


def match_upstream(question: str, indexes) -> Optional[dict]:
    """Look a question up in CMU's bank, strictest tier first.

    Tiered so a looser tier can never override an exact hit: exact equality, then
    punctuation/Unicode normalization, then whitespace-insensitive (which
    recovers upstream's '100C degrees' typo).
    """
    exact, loose, tight = indexes
    for key, index in (
        (question, exact),
        (norm(question), loose),
        (norm(question, True), tight),
    ):
        if key in index:
            return index[key]
    return None


def main() -> int:
    with open(LOCAL_QUESTIONS, encoding="utf-8") as fh:
        questions = [line.strip() for line in fh if line.strip()]

    indexes = load_upstream()

    rows: List[dict] = []
    missing: List[int] = []

    for q_index, question in enumerate(questions, start=1):
        upstream = match_upstream(question, indexes)
        if upstream is None:
            missing.append(q_index)
            continue

        upstream_question = upstream["Question"].strip()
        rows.append(
            {
                "q_index": q_index,
                "Question": question,
                **{turn: upstream[turn].strip() for turn in TURNS},
                "provenance": "sycon",
                # Only recorded when CMU's wording differs from ours, so the
                # two punctuation/typo matches stay auditable.
                "upstream_question": (
                    "" if upstream_question == question else upstream_question
                ),
            }
        )

    if missing:
        print(
            f"ERROR: q{missing} not found in {os.path.basename(UPSTREAM_PUSHBACKS)}. "
            "Every question must come from CMU's 200-question bank - check "
            "questions.txt against 'questions/CMU questions/questions.txt'.",
            file=sys.stderr,
        )
        return 1

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(FIELDNAMES))
        writer.writeheader()
        writer.writerows(rows)

    reworded = [r["q_index"] for r in rows if r["upstream_question"]]
    print(f"Wrote {len(rows)} rows to {OUT_CSV}")
    print(f"  provenance=sycon        : {len(rows)}")
    print(f"  wording differs from CMU: q{reworded}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
