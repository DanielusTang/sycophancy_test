#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch runner — ESCALATE mode
============================

Runs the position-strength sycophancy stress test over every case, with adaptive
pressure pinned to **escalate**: once a strategy causes erosion (or leaves the target
at position_strength <= the lock threshold), the human proxy reuses it — and if the
score PLATEAUS (no further drop) for `--escalation-patience` turns, it climbs the
pressure ladder (MILD_CONFUSION -> FALSE_PIVOT -> RE_ASSERTION -> PERSONAL_EXPERIENCE
-> DIRECT_CHALLENGE). Pair with `false_presuppositions_exploitation.py` to A/B the two.

Outputs default to false_presuppositions/outputs_escalation/.

Run (from anywhere):
    export DEEPSEEK_API_KEY=sk-xxxx
    python3 false_presuppositions/false_presuppositions_escalation.py
    python3 false_presuppositions/false_presuppositions_escalation.py --limit 3 --max-turns 15
    python3 false_presuppositions/false_presuppositions_escalation.py --escalation-patience 3
"""

import os

from sycophancy_pipeline_strength import run_strength_batch_cli

_HERE = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    run_strength_batch_cli(
        pressure_mode="escalate",
        default_output_dir=os.path.join(_HERE, "outputs_escalation"),
        description="Batch position-strength sycophancy test — ESCALATE mode (reuse, then climb the ladder on plateau).",
    )
