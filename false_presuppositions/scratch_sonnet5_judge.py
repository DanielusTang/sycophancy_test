#!/usr/bin/env python3
"""Add claude-sonnet-5 as a judge over the SAME 5 D0 transcripts, merging with all
prior judges. Sonnet 5 is an Anthropic model, so it reuses HaikuJudge (native Messages
API subclass) with model='claude-sonnet-5'. No source files edited.
"""
import os, glob, json, statistics

import false_presuppositions_newjudge as j
from false_presuppositions_newjudge import build_target_client, JUDGE_MAX_TOKENS
from calibrate_judges import load_turns
from scratch_haiku_judge import HaikuJudge

MODEL = "claude-sonnet-5"
LABEL = "sonnet-5"
REF = "gpt-4o"
EXISTING = "ablation_outputs/judge_calibration_with_v4pro.jsonl"  # gpt-4o/mini/R1/haiku/v4-pro
OUT = "ablation_outputs/judge_calibration_all6.jsonl"


def main():
    existing = {}
    with open(EXISTING) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            existing[(r["file"], r["turn"])] = r

    client = build_target_client("anthropic")
    files = sorted(glob.glob(
        "ablation_outputs/adversarial/D0/sycophancy_strength_adversarial_q[1-5]_*.jsonl"))

    rows = []
    print(f"Re-judging {len(files)} transcript(s) with {MODEL}\n")
    for path in files:
        meta, turns = load_turns(path)
        premise, correction = meta.get("false_premise"), meta.get("correction")
        judge = HaikuJudge(client, premise, model=MODEL,
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
                sv = {"s": v.get("position_strength"), "c": v.get("is_collapsed")}
            except Exception as exc:
                sv = {"s": None, "c": None, "err": str(exc)[:90]}
            base_row["file"], base_row["turn"] = fname, t.get("turn")
            base_row[LABEL] = sv
            rows.append(base_row)
            cells = " | ".join(
                f"{n}: s={base_row.get(n,{}).get('s')} c={base_row.get(n,{}).get('c')}"
                for n in (REF, LABEL))
            print(f"  {fname[:46]} t{base_row['turn']}: {cells}"
                  + (f"   ERR={sv['err']}" if "err" in sv else ""))

    sp = [(r[REF]["s"], r[LABEL]["s"]) for r in rows
          if r.get(REF, {}).get("s") is not None and r[LABEL].get("s") is not None]
    cp = [(r[REF]["c"], r[LABEL]["c"]) for r in rows
          if r.get(REF, {}).get("c") is not None and r[LABEL].get("c") is not None]
    mae = statistics.mean(abs(a - b) for a, b in sp) if sp else float("nan")
    exact = statistics.mean(1.0 if a == b else 0.0 for a, b in sp) if sp else float("nan")
    cagree = statistics.mean(1.0 if a == b else 0.0 for a, b in cp) if cp else float("nan")
    print("\n==== claude-sonnet-5 per-turn agreement vs %s ====" % REF)
    print(f"  sonnet-5       strength: MAE={mae:.2f} exact={100*exact:3.0f}%   "
          f"is_collapsed: agree={100*cagree:3.0f}%   (n={len(sp)} turns)")

    JUDGES = ["gpt-4o", "gpt-4o-mini", "deepseek-R1", "haiku-4.5", "v4-pro", "sonnet-5"]
    print("\n==== first is_collapsed turn per file (all judges) ====")
    print("  " + f"{'file':40} " + " ".join(f"{n:>11}" for n in JUDGES))
    for f in sorted(set(r["file"] for r in rows)):
        fr = [r for r in rows if r["file"] == f]
        cells = []
        for n in JUDGES:
            ct = next((r["turn"] for r in fr if r.get(n, {}).get("c") is True), None)
            cells.append("none" if ct is None else str(ct))
        print("  " + f"{f[:40]:40} " + " ".join(f"{c:>11}" for c in cells))

    with open(OUT, "w") as fo:
        for r in rows:
            fo.write(json.dumps(r) + "\n")
    print("\ndumped merged per-turn scores:", OUT)


if __name__ == "__main__":
    main()
