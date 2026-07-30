#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resume a finished, killed, or partial run from its JSONL log
============================================================

Rebuilds the Target and Proxy agents from a run's own JSONL and hands the orchestrator a
`ResumeState` so the normal loop picks up mid-conversation instead of starting at turn 1.
Ported from `false_presuppositions/false_presuppositions_resume.py`; the two modules are
deliberate mirrors, and `unethical_setting/` imports nothing from that package.

Three uses, one mechanism — replay the logged prefix up to turn `S`, then run
`S+1 .. max_turns`:

  * CONTINUE (no --from-turn, log has no `result`): S = last logged turn. A run killed
    mid-conversation — an API 402, a SIGKILL — resumes exactly where it stopped. This is
    the case the FP module refuses; it is allowed here because a log with no result and a
    non-terminal last turn is unambiguous: it still had turns to run.
  * EXTEND (no --from-turn, log has a non-terminal `result`): S = last logged turn.
    Continue a run that hit --max-turns while still holding, e.g. 25 -> 30.
  * BRANCH (--from-turn N): S = N-1. Discard the logged turns from N on and resample them.
    Legitimate on ANY run including a collapsed one, as long as turns 0..S were logged.

Why replay is faithful: the target's history is exactly
`[system(opening_question)] + (proxy_input, target_output)*` — reasoning was never appended
to it — and every turn record carries `context_messages`, which pins the expected history
length so a bad replay fails loudly instead of quietly running a different conversation.
The proxy's per-turn user message is a pure function of the previous reply, the display
turn and the recap, all rendered through the proxy's own `_build_turn_user`.

The one thing NOT logged verbatim is the proxy's raw JSON reply per turn; it is rebuilt
from the parsed fields (`proxy_reasoning`, `proxy_decision`, `proxy_input`). Semantically
identical, not byte-identical, so the first resumed call pays one prompt-cache write
instead of a hit. Nothing downstream depends on those bytes.

Unethical-specific: the cold ESSENTIALIST_FRAMING ceiling probe is NEVER re-fired on a
resume. Its verdict is replayed from the logged `baseline_probe` record — re-running it
would spend a call and could return a different ceiling, silently changing whether the
case counts as valid.

Caveat worth knowing: replay renders the CURRENT prompt templates. Resuming a run made
before a template change silently mixes versions — check the run's date against
`unethical_proxy.py` before resuming anything old.
"""

from __future__ import annotations

import glob
import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from unethical_base import logger
from unethical_proxy import ProxyAgent, ProxyState
from unethical_target import TargetAgent

# Outcomes meaning "this conversation already ended". They can still be BRANCHED (re-rolled
# from an earlier turn) but never continued. "error" is deliberately NOT here: a run that
# died on an API fault is exactly what CONTINUE is for.
TERMINAL_OUTCOMES = ("collapsed", "eroded", "ended_winddown")


class ResumeError(Exception):
    pass


@dataclass
class ResumeState:
    """Everything `StrengthOrchestrator.run()` would have accumulated by turn `start_turn`.

    All counters are derived from the RETAINED prefix (turns 1..start_turn) only — a branch
    at turn 13 must not inherit erosion events from the turns it just discarded.
    """
    start_turn: int                      # last replayed turn; the loop resumes at +1
    kind: str                            # "continue" | "extend" | "branch"
    source_path: str
    prior_records: list                  # turn records to re-emit verbatim into the new log
    target_last: str
    target_reasoning: str
    baseline_probe: Optional[dict] = None   # replayed; the probe is never re-fired
    essentialism_ceiling: Optional[int] = None
    scores: list = field(default_factory=list)
    eroded_turns: list = field(default_factory=list)
    first_eroded_turn: Optional[int] = None
    effective_collapse_turns: list = field(default_factory=list)
    first_effective_collapse_turn: Optional[int] = None
    winddown_streak: int = 0
    winddown_first_turn: Optional[int] = None
    winddown_signal: Optional[str] = None
    # Stereotype-specific tallies with no false-presupposition counterpart.
    discriminatory_action_turns: list = field(default_factory=list)
    first_discriminatory_action_turn: Optional[int] = None
    evidence_capitulation_trajectory: list = field(default_factory=list)


@dataclass
class LoadedRun:
    meta: dict
    turns: list          # retained turn records, turn 0 first, contiguous through start_turn
    result: Optional[dict]
    baseline: Optional[dict]
    start_turn: int
    kind: str
    path: str


def _parse_jsonl(path: str) -> tuple:
    meta, turns, result, baseline = None, [], None, None
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                # A run killed mid-write can leave a truncated final line; everything before
                # it is still usable, so warn rather than abort.
                logger.warning("%s: skipping malformed line %d (%s)",
                               os.path.basename(path), lineno, exc)
                continue
            kind = rec.get("type")
            if kind == "meta" and meta is None:
                meta = rec
            elif kind == "turn":
                turns.append(rec)
            elif kind == "result":
                result = rec
            elif kind == "baseline_probe" and baseline is None:
                baseline = rec
    if meta is None:
        raise ResumeError(f"{path}: no meta record — not a run log")
    if not turns:
        raise ResumeError(f"{path}: no turn records")
    return meta, turns, result, baseline


def load_run(path: str, from_turn: Optional[int] = None,
             new_max_turns: Optional[int] = None) -> LoadedRun:
    """Parse a run log and resolve the cut point. Raises ResumeError if it can't be resumed."""
    meta, turns, result, baseline = _parse_jsonl(path)

    numbers = [t.get("turn") for t in turns]
    if numbers != list(range(len(numbers))):
        raise ResumeError(f"{path}: turn numbers are not contiguous from 0 ({numbers[:5]}...)")
    last_turn = numbers[-1]

    if from_turn is not None:
        if from_turn < 1:
            raise ResumeError("--from-turn must be >= 1 (turn 0 is the baseline question)")
        start_turn = from_turn - 1
        if start_turn > last_turn:
            raise ResumeError(
                f"{os.path.basename(path)}: cannot branch at turn {from_turn} — the run only "
                f"reached turn {last_turn}, so turn {start_turn} was never logged")
        turns = turns[:start_turn + 1]
        kind = "branch"
    elif result is None:
        # Killed mid-conversation: no result was ever written. Continue from the last
        # complete turn. The turn it died ON was never logged, so nothing is discarded.
        start_turn = last_turn
        kind = "continue"
    else:
        outcome = result.get("outcome")
        if outcome in TERMINAL_OUTCOMES:
            raise ResumeError(
                f"{os.path.basename(path)}: outcome is '{outcome}' — the conversation already "
                f"ended, nothing to continue. Use --from-turn N to re-roll it from turn N")
        start_turn = last_turn
        kind = "extend"

    if new_max_turns is not None and start_turn >= new_max_turns:
        raise ResumeError(
            f"{os.path.basename(path)}: already at turn {start_turn}, which is >= --max-turns "
            f"{new_max_turns} — nothing to run")

    return LoadedRun(meta=meta, turns=turns, result=result, baseline=baseline,
                     start_turn=start_turn, kind=kind, path=path)


def build_resume_state(run: LoadedRun) -> ResumeState:
    """Recompute the orchestrator's per-run counters from the retained prefix."""
    scores, eroded_turns, effective_collapse_turns = [], [], []
    first_eroded_turn = first_effective_collapse_turn = None
    winddown_streak, winddown_first_turn, winddown_signal = 0, None, None
    discrim_turns, first_discrim_turn, evidence_traj = [], None, []

    for rec in run.turns[1:]:                      # turn 0 is the baseline; it has no score
        turn = rec["turn"]
        judge = rec.get("judge") or {}
        scores.append(rec.get("position_strength", judge.get("position_strength")))
        if rec.get("eroded"):
            eroded_turns.append(turn)
            if first_eroded_turn is None:
                first_eroded_turn = turn
        # Same predicate as the live loop: a soft cave is an effective_collapse that is not
        # (yet) a strict one.
        if judge.get("effective_collapse") is True and judge.get("is_collapsed") is not True:
            effective_collapse_turns.append(turn)
            if first_effective_collapse_turn is None:
                first_effective_collapse_turn = turn
        if judge.get("endorsed_discriminatory_action") is True:
            discrim_turns.append(turn)
            if first_discrim_turn is None:
                first_discrim_turn = turn
        if judge.get("evidence_capitulation") is not None:
            evidence_traj.append(judge.get("evidence_capitulation"))
        # The streak is only the TRAILING run of wind-down turns; anything substantive
        # resets it, exactly as the loop does.
        wd = rec.get("winddown") or {}
        if wd.get("is_winddown"):
            winddown_streak += 1
            if winddown_first_turn is None:
                winddown_first_turn, winddown_signal = turn, wd.get("signal")
        else:
            winddown_streak = 0
            winddown_first_turn = winddown_signal = None

    ceiling = None
    if run.baseline is not None:
        ceiling = run.baseline.get("position_strength")
    elif run.result is not None:
        ceiling = run.result.get("essentialism_ceiling")

    last = run.turns[-1]
    return ResumeState(
        start_turn=run.start_turn,
        kind=run.kind,
        source_path=run.path,
        prior_records=run.turns,
        target_last=last.get("target_output", ""),
        target_reasoning=last.get("target_reasoning", "") or "",
        baseline_probe=run.baseline,
        essentialism_ceiling=ceiling,
        scores=scores,
        eroded_turns=eroded_turns,
        first_eroded_turn=first_eroded_turn,
        effective_collapse_turns=effective_collapse_turns,
        first_effective_collapse_turn=first_effective_collapse_turn,
        winddown_streak=winddown_streak,
        winddown_first_turn=winddown_first_turn,
        winddown_signal=winddown_signal,
        discriminatory_action_turns=discrim_turns,
        first_discriminatory_action_turn=first_discrim_turn,
        evidence_capitulation_trajectory=evidence_traj,
    )


# --------------------------------------------------------------------------- #
# Agent reconstruction
# --------------------------------------------------------------------------- #
def rebuild_target(run: LoadedRun, client, *, model: str, provider: str,
                   enable_thinking=None, temperature: Optional[float] = None) -> TargetAgent:
    """Rebuild the model-under-test with the exact history it had at `run.start_turn`.

    The constructor already installs the system prompt from the opening question, so the
    replay only re-appends the (user, assistant) pair each turn contributed. Reasoning was
    never part of history, so there is nothing to strip.
    """
    if temperature is None:
        temperature = run.meta.get("target_temperature")
    target = TargetAgent(client, model=model,
                         opening_question=run.meta["opening_question"],
                         enable_thinking=enable_thinking, provider=provider,
                         temperature=temperature)
    for rec in run.turns:
        target.history.append({"role": "user", "content": rec.get("proxy_input", "")})
        target.history.append({"role": "assistant", "content": rec.get("target_output", "")})

    # `context_messages` was written by the original run from this same property, so it is an
    # independent check that the replay produced the same conversation shape.
    expected = run.turns[-1].get("context_messages")
    if expected is not None and target.turns_in_context != expected:
        raise ResumeError(
            f"{os.path.basename(run.path)}: rebuilt target history has "
            f"{target.turns_in_context} messages but the log says {expected} at turn "
            f"{run.start_turn} — refusing to continue a conversation that does not match")
    return target


def rebuild_proxy(run: LoadedRun, client, *, model: str, provider: str) -> ProxyAgent:
    """Rebuild the user-simulator with the dialogue and move history it had at `start_turn`."""
    ablation = run.meta.get("ablation") or {}
    persona = ("adversarial" if str(run.meta.get("variant", "")).endswith("adversarial")
               else "naturalistic")
    proxy = ProxyAgent(
        client, run.meta["false_premise"], model=model, persona=persona, provider=provider,
        judge_feedback=bool(ablation.get("judge_feedback")),
        reasoning_access=bool(ablation.get("reasoning_access")),
        enable_thinking=ablation.get("proxy_thinking"),
        memory_turns=int(ablation.get("proxy_memory_turns") or 0),
    )

    # Walk the turns in order, reconstructing each exchange the way the live loop built it:
    # the user message is rendered from the PREVIOUS reply and the recap as it stood at that
    # moment, so record_turn must be called as we go rather than all at the end.
    for i, rec in enumerate(run.turns[1:], start=1):
        prev = run.turns[i - 1]
        visible = (proxy._dialogue if not proxy.memory_turns
                   else proxy._dialogue[-2 * proxy.memory_turns:])
        display_turn = len(visible) // 2 + 1
        user_content = proxy._build_turn_user(
            prev.get("target_output", ""), display_turn, proxy._recent_moves(),
            prev.get("target_reasoning", "") or "")
        decision = rec.get("proxy_decision") or {}
        # The raw JSON the model actually emitted is not logged; rebuild an equivalent object
        # from the parsed fields. Key order/whitespace differ from the original, which costs
        # one cache write and nothing else.
        assistant = json.dumps({
            "reasoning": rec.get("proxy_reasoning", ""),
            "category": decision.get("category") or rec.get("category", ""),
            "tactic": decision.get("strategy") or rec.get("state", ""),
            "rationale": decision.get("rationale", ""),
            "message": rec.get("proxy_input", ""),
        }, ensure_ascii=False)
        proxy._dialogue.append({"role": "user", "content": user_content})
        proxy._dialogue.append({"role": "assistant", "content": assistant})

        state_value = decision.get("strategy") or rec.get("state")
        try:
            strategy = ProxyState(state_value)
        except ValueError:
            raise ResumeError(
                f"{os.path.basename(run.path)}: turn {rec['turn']} has unknown tactic "
                f"{state_value!r} — the tactic menu changed since this run was made")
        judge = rec.get("judge") or {}
        proxy.record_turn(
            turn=rec["turn"], strategy=strategy,
            proxy_message=rec.get("proxy_input", ""),
            target_reply=rec.get("target_output", ""),
            position_strength=rec.get("position_strength", judge.get("position_strength")),
            is_collapsed=judge.get("is_collapsed"),
            effective_collapse=judge.get("effective_collapse"),
            firmness=(decision.get("target_read") or {}).get("firmness", ""),
        )
    return proxy


# --------------------------------------------------------------------------- #
# Config reconciliation + file discovery
# --------------------------------------------------------------------------- #
def check_config(run: LoadedRun, args) -> None:
    """Abort if an explicitly-passed CLI flag contradicts what the log says the run used.

    Continuing a conversation under a different model or temperature silently invalidates
    it, so an explicit contradiction is worth stopping for. Flags left at their default are
    taken from the log instead.
    """
    ablation = run.meta.get("ablation") or {}
    checks = [
        ("--target-model", "target_model", run.meta.get("target_model")),
        ("--target-provider", "target_provider", run.meta.get("target_provider")),
        ("--model", "model", run.meta.get("proxy_model") or ablation.get("proxy_model")),
        ("--proxy-provider", "proxy_provider", ablation.get("proxy_provider")),
        ("--target-temperature", "target_temperature", run.meta.get("target_temperature")),
    ]
    problems = []
    for flag, attr, logged in checks:
        if logged is None or attr not in getattr(args, "_explicit", set()):
            continue
        given = getattr(args, attr, None)
        if given != logged:
            problems.append(f"{flag}={given!r} but the run used {logged!r}")
    if problems:
        raise ResumeError(
            f"{os.path.basename(run.path)}: config mismatch — " + "; ".join(problems) +
            ". Drop the flag to reuse the logged value, or resume a different run")


_TS_RE = re.compile(r"_(\d{8}_\d{6})\.jsonl$")


def discover_runs(path: str, pattern: str = "unethical_strength_*.jsonl") -> list:
    """Resolve --resume-from to a list of run logs.

    A file resolves to itself. A directory resolves to the LATEST log per question, so a
    folder holding re-runs of the same question is not resumed several times over.
    """
    if os.path.isfile(path):
        return [path]
    if not os.path.isdir(path):
        raise ResumeError(f"{path}: no such file or directory")
    files = sorted(glob.glob(os.path.join(path, pattern)))
    if not files:
        raise ResumeError(f"{path}: no files matching {pattern}")
    latest: dict = {}
    for f in files:
        key = _TS_RE.sub("", os.path.basename(f))
        stamp = _TS_RE.search(os.path.basename(f))
        stamp = stamp.group(1) if stamp else ""
        if key not in latest or stamp > latest[key][0]:
            latest[key] = (stamp, f)
    return [f for _, f in sorted(latest.values())]


def resume_output_path(run: LoadedRun, output_dir: str, batch_ts: str,
                       branch_index: Optional[int] = None) -> str:
    """Name the new log. A branch is marked so it is never mistaken for a fresh run."""
    base = os.path.basename(run.path)
    stem = _TS_RE.sub("", base) or f"unethical_strength_{run.meta.get('topic', 'case')}"
    suffix = ""
    if run.kind == "branch":
        suffix = f"_from{run.start_turn + 1}"
        if branch_index is not None:
            suffix += f"_b{branch_index}"
    return os.path.join(output_dir, f"{stem}{suffix}_{batch_ts}.jsonl")
