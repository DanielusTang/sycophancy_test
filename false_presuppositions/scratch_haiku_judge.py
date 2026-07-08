#!/usr/bin/env python3
"""Add Haiku 4.5 as a judge over the SAME 5 D0 transcripts, reusing the existing
gpt-4o / gpt-4o-mini / deepseek-R1 scores from outputs/judge_calibration.jsonl.

Haiku is an Anthropic model, so it cannot go through JudgeAgent._chat (which speaks
the OpenAI .chat.completions surface). We subclass the judge and override _chat to
call the native Anthropic Messages API (client.messages.create), mapping the system
turn to `system=` and relying on the prompt's "Return ONLY this JSON" + the judge's
existing regex JSON parser — exactly how the reasoner/qwen paths already skip
response_format. No source files are edited.
"""
import os, glob, json, statistics

import false_presuppositions_newjudge as base
from false_presuppositions_newjudge import (
    PositionStrengthJudge, build_target_client, JUDGE_MAX_TOKENS,
)
from calibrate_judges import load_turns  # reuse the exact transcript loader

HAIKU_MODEL = "claude-haiku-4-5"
REF = "gpt-4o"
EXISTING = "ablation_outputs/judge_calibration.jsonl"
OUT = "ablation_outputs/judge_calibration_with_haiku.jsonl"


class HaikuJudge(PositionStrengthJudge):
    """PositionStrengthJudge that talks to the native Anthropic Messages API."""

    def _chat(self, messages, *, temperature=None, response_format=None,
              return_reasoning=False):
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        user = "\n".join(m["content"] for m in messages if m["role"] == "user")
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        return (content, "") if return_reasoning else content


def main():
    # 1) existing per-turn scores, keyed by (file, turn)
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
    print(f"Re-judging {len(files)} transcript(s) with Haiku 4.5 ({HAIKU_MODEL})\n")
    for path in files:
        meta, turns = load_turns(path)
        premise, correction = meta.get("false_premise"), meta.get("correction")
        judge = HaikuJudge(client, premise, model=HAIKU_MODEL,
                           correction=correction, max_tokens=JUDGE_MAX_TOKENS)
        fname = os.path.basename(path)
        for t in turns:
            tgt = t.get("target_output", "") or ""
            usr = t.get("proxy_input", "") or ""
            rsn = t.get("target_reasoning", "") or ""
            base_row = existing.get((fname, t.get("turn")), {})
            try:
                v = judge.evaluate(tgt, previous_user_message=usr,
                                   target_ai_reasoning=rsn, samples=1)
                hk = {"s": v.get("position_strength"), "c": v.get("is_collapsed")}
            except Exception as exc:
                hk = {"s": None, "c": None, "err": str(exc)[:90]}
            row = dict(base_row)
            row["file"], row["turn"] = fname, t.get("turn")
            row["haiku-4.5"] = hk
            rows.append(row)
            cells = " | ".join(
                f"{n}: s={row.get(n,{}).get('s')} c={row.get(n,{}).get('c')}"
                for n in (REF, "haiku-4.5"))
            print(f"  {fname[:46]} t{row['turn']}: {cells}"
                  + (f"   ERR={hk['err']}" if "err" in hk else ""))

    # 2) agreement vs gpt-4o
    sp = [(r[REF]["s"], r["haiku-4.5"]["s"]) for r in rows
          if r.get(REF, {}).get("s") is not None and r["haiku-4.5"].get("s") is not None]
    cp = [(r[REF]["c"], r["haiku-4.5"]["c"]) for r in rows
          if r.get(REF, {}).get("c") is not None and r["haiku-4.5"].get("c") is not None]
    mae = statistics.mean(abs(a - b) for a, b in sp) if sp else float("nan")
    exact = statistics.mean(1.0 if a == b else 0.0 for a, b in sp) if sp else float("nan")
    cagree = statistics.mean(1.0 if a == b else 0.0 for a, b in cp) if cp else float("nan")
    print("\n==== Haiku-4.5 per-turn agreement vs %s ====" % REF)
    print(f"  haiku-4.5      strength: MAE={mae:.2f} exact={100*exact:3.0f}%   "
          f"is_collapsed: agree={100*cagree:3.0f}%   (n={len(sp)} turns)")

    # 3) first collapse turn per file: gpt-4o vs haiku
    print("\n==== first is_collapsed turn per file ====")
    print(f"  {'file':52} {'gpt-4o':>10} {'haiku-4.5':>12}")
    for f in sorted(set(r["file"] for r in rows)):
        fr = [r for r in rows if r["file"] == f]
        g = next((r["turn"] for r in fr if r.get(REF, {}).get("c") is True), None)
        h = next((r["turn"] for r in fr if r["haiku-4.5"].get("c") is True), None)
        print(f"  {f[:52]:52} {('none' if g is None else g)!s:>10} "
              f"{('none' if h is None else h)!s:>12}")

    with open(OUT, "w") as fo:
        for r in rows:
            fo.write(json.dumps(r) + "\n")
    print("\ndumped merged per-turn scores:", OUT)


if __name__ == "__main__":
    main()
