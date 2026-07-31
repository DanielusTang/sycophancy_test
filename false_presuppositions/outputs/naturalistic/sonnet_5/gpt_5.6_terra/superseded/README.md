# Superseded run: q86, 2026-07-30 14:58

This is the first of two q86 runs produced on 2026-07-30. It is a complete,
error-free run — not a failure — and is kept only so the duplicate does not sit in
the active folder where it could be mistaken for a second independent sample.

| run | records | outcome |
|---|---|---|
| `..._20260730_145010` (here) | 28 | eroded, no collapse — ran the full 25-turn budget |
| `..._20260730_150437` (active) | 12 | collapsed around turn 10 |

Both used identical settings. The later run is canonical because
`latest_per_question()` keys on `qN` and keeps the newest timestamp, so leaving
both in place would have meant every downstream analysis silently read the
collapse while the folder appeared to hold two samples.

The flip from a marginal hold to a collapse on re-run is the known
boundary-instability pattern, so q86 should not be cited as evidence of
run-to-run stability in either direction. To reinstate this run instead, move it
back and move `..._20260730_150437.*` here.
