#!/usr/bin/env python3
"""Add deepseek-v4-pro as a judge over the SAME 5 D0 transcripts, merging with the
existing gpt-4o/mini/R1/haiku scores. v4-pro is OpenAI-compatible (DeepSeek API) and
is NOT a reasoner-marked model, so it goes through the standard PositionStrengthJudge
chat path (temperature=0 + response_format json_object). No source files edited.
"""
import os, glob, json, statistics

import false_presuppositions_newjudge as j
from false_presuppositions_newjudge import (
    PositionStrengthJudge, build_target_client, JUDGE_MAX_TOKENS,
)
from calibrate_judges import load_turns

V4_MODEL = "deepseek-v4-pro"
REF = "gpt-4o"
EXISTING = "ablation_outputs/judge_calibration_with_haiku.jsonl"  # has gpt-4o/mini/R1/haiku
OUT = "ablation_outputs/judge_calibration_with_v4pro.jsonl"


def main():
    existing = {}
    with open(EXISTING) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            existing[(r["file"], r["turn"])] = r

    client = build_target_client("deepseek")
    files = sorted(glob.glob(
        "ablation_outputs/adversarial/D0/sycophancy_strength_adversarial_q[1-5]_*.jsonl"))

    rows = []
    print(f"Re-judging {len(files)} transcript(s) with {V4_MODEL}\n")
    for path in files:
        meta, turns = load_turns(path)
        premise, correction = meta.get("false_premise"), meta.get("correction")
        judge = PositionStrengthJudge(client, premise, model=V4_MODEL,
                                      correction=correction, max_tokens=JUDGE_MAX_TOKENS)
        fname = os.path.basename(path)
        for t in turns:
            tgt = t.get("target_output", "") or ""
            usr = t.get("proxy_input", "") or ""
            rsn = t.get("target_reasoning", "") or ""
            base_row = dict(existing.get((fname, t.get("turn")), {}))
            try:
                v = judge.evaluate(tgt, previous_user_message=usr,
                                   target_ai_reasoning=rsn, samples=1)
                dv = {"s": v.get("position_strength"), "c": v.get("is_collapsed")}
            except Exception as exc:
                dv = {"s": None, "c": None, "err": str(exc)[:90]}
            base_row["file"], base_row["turn"] = fname, t.get("turn")
            base_row["v4-pro"] = dv
            rows.append(base_row)
            cells = " | ".join(
                f"{n}: s={base_row.get(n,{}).get('s')} c={base_row.get(n,{}).get('c')}"
                for n in (REF, "v4-pro"))
            print(f"  {fname[:46]} t{base_row['turn']}: {cells}"
                  + (f"   ERR={dv['err']}" if "err" in dv else ""))

    # agreement vs gpt-4o
    sp = [(r[REF]["s"], r["v4-pro"]["s"]) for r in rows
          if r.get(REF, {}).get("s") is not None and r["v4-pro"].get("s") is not None]
    cp = [(r[REF]["c"], r["v4-pro"]["c"]) for r in rows
          if r.get(REF, {}).get("c") is not None and r["v4-pro"].get("c") is not None]
    mae = statistics.mean(abs(a - b) for a, b in sp) if sp else float("nan")
    exact = statistics.mean(1.0 if a == b else 0.0 for a, b in sp) if sp else float("nan")
    cagree = statistics.mean(1.0 if a == b else 0.0 for a, b in cp) if cp else float("nan")
    print("\n==== deepseek-v4-pro per-turn agreement vs %s ====" % REF)
    print(f"  v4-pro         strength: MAE={mae:.2f} exact={100*exact:3.0f}%   "
          f"is_collapsed: agree={100*cagree:3.0f}%   (n={len(sp)} turns)")

    # first collapse turn per file: every judge
    JUDGES = ["gpt-4o", "gpt-4o-mini", "deepseek-R1", "haiku-4.5", "v4-pro"]
    print("\n==== first is_collapsed turn per file (all judges) ====")
    print("  " + f"{'file':46} " + " ".join(f"{n:>12}" for n in JUDGES))
    for f in sorted(set(r["file"] for r in rows)):
        fr = [r for r in rows if r["file"] == f]
        cells = []
        for n in JUDGES:
            ct = next((r["turn"] for r in fr if r.get(n, {}).get("c") is True), None)
            cells.append("none" if ct is None else str(ct))
        print("  " + f"{f[:46]:46} " + " ".join(f"{c:>12}" for c in cells))

    with open(OUT, "w") as fo:
        for r in rows:
            fo.write(json.dumps(r) + "\n")
    print("\ndumped merged per-turn scores:", OUT)


if __name__ == "__main__":
    main()
