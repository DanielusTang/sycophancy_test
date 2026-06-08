#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch runner — position-strength (general)
==========================================

The general batch runner for the position-strength sycophancy stress test. By
default it runs with `--pressure-mode off` (the wave-band baseline), but you can
pass `--pressure-mode exploit` or `--pressure-mode escalate` to enable adaptive
pressure. For convenience, the two adaptive modes also have dedicated runners:
    false_presuppositions_exploitation.py   (pressure-mode = exploit)
    false_presuppositions_escalation.py     (pressure-mode = escalate)

Outputs default to false_presuppositions/outputs_strength/.

Run (from anywhere):
    export DEEPSEEK_API_KEY=sk-xxxx
    python3 false_presuppositions/run_batch_strength.py                      # baseline (off)
    python3 false_presuppositions/run_batch_strength.py --pressure-mode exploit
    python3 false_presuppositions/run_batch_strength.py --limit 3 --max-turns 15
"""

from sycophancy_pipeline_strength import run_strength_batch_cli


if __name__ == "__main__":
    run_strength_batch_cli(
        pressure_mode=None,  # exposes --pressure-mode (default off)
        description="Batch position-strength sycophancy stress test (choose --pressure-mode).",
    )
