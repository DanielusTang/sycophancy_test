#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resume a finished (or partial) run from its JSONL log
======================================================

Rebuilds the Target and Proxy agents from a run's own JSONL and hands the
orchestrator a `ResumeState` so the normal loop picks up mid-conversation instead of
starting from turn 1. Two uses, one mechanism — replay the logged prefix up to turn
`S`, then run turns `S+1 .. max_turns`:

  * EXTEND (no --from-turn): S = the last logged turn. Continue a run that hit the
    --max-turns ceiling while still holding, e.g. 25 -> 30 turns. Only meaningful for a
    non-terminal outcome; a collapsed / wound-down conversation already ended.
  * BRANCH (--from-turn N): S = N-1. Discard the logged turns from N on and resample
    them. Legitimate on ANY run, including a collapsed one, as long as it logged turns
    0..S — branching below the collapse turn is a re-roll of that decision point.

Why this is exact rather than approximate: the JSONL records everything the two agents
need. The target's history is `[system(opening_question)] + (proxy_input, target_output)*`
and nothing else — reasoning was deliberately never appended to it — and every turn
record carries `context_messages`, which pins the expected history length so a bad
replay fails loudly instead of quietly running a different conversation. The proxy's
per-turn user message is a pure function of the previous reply, the display turn and the
recap, all rendered here through the proxy's own `_build_turn_user`.

The one thing NOT logged verbatim is the proxy's raw JSON reply per turn; it is rebuilt
from the parsed fields (`proxy_reasoning`, `proxy_decision`, `proxy_input`). That is
semantically identical but not byte-identical, so the first resumed call pays one prompt
cache write instead of a hit. Nothing downstream depends on those bytes.

Caveat worth knowing: replay renders the CURRENT prompt templates. Resuming a run made
before a template change silently mixes versions — check the run's date against
`false_presuppositions_proxy.py` before resuming anything old.

Which TACTIC MENU to replay with is resolved per run by `infer_tactic_set` rather than taken
from the CLI default, so resuming a CMU-5 log does not silently hand the proxy the MAFALDA
menu. It trusts what the log DID (its tactics, then its categories) over what it says about
itself, because `proxy_strategy` is provably wrong on the archived CMU runs.
"""

from __future__ import annotations

import glob
import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from false_presuppositions_base import logger
from false_presuppositions_proxy import (
    ProxyAgent,
    ProxyState,
    DEFAULT_TACTIC_SET,
    TACTIC_SETS,
    tactic_sets_containing,
    tactic_sets_with_category,
)
from false_presuppositions_target import TargetAgent

# Outcomes that mean "this conversation already ended". They can still be BRANCHED
# (re-rolled from an earlier turn) but never EXTENDED — there is nothing to continue.
TERMINAL_OUTCOMES = ("collapsed", "eroded", "ended_winddown")


class ResumeError(Exception):
    """A run cannot be resumed as requested (bad cut point, truncated log, mismatch)."""


# --------------------------------------------------------------------------- #
# Parsed run + the state the orchestrator needs to continue it
# --------------------------------------------------------------------------- #
@dataclass
class ResumeState:
    """Everything `StrengthOrchestrator.run()` would have accumulated by turn `start_turn`.

    All counters are derived from the RETAINED prefix (turns 1..start_turn) only — a
    branch at turn 13 must not inherit erosion events from the turns it just discarded.
    """
    start_turn: int                      # last replayed turn; the loop resumes at +1
    kind: str                            # "extend" | "branch"
    source_path: str
    prior_records: list                  # turn records to re-emit verbatim into the new log
    target_last: str
    target_reasoning: str
    scores: list = field(default_factory=list)
    eroded_turns: list = field(default_factory=list)
    first_eroded_turn: Optional[int] = None
    effective_collapse_turns: list = field(default_factory=list)
    first_effective_collapse_turn: Optional[int] = None
    winddown_streak: int = 0
    winddown_first_turn: Optional[int] = None
    winddown_signal: Optional[str] = None


@dataclass
class LoadedRun:
    meta: dict
    turns: list          # retained turn records, turn 0 first, contiguous through start_turn
    result: Optional[dict]
    start_turn: int
    kind: str
    path: str
    # Which tactic menu this run used, and how confidently we know (see infer_tactic_set).
    tactic_set: str = DEFAULT_TACTIC_SET
    tactic_set_source: str = "default"


# Evidence strong enough to REFUSE a contradicting --tactic-set (see check_config); a set
# resolved any other way is a guess and stays hand-overridable.
_CONFIDENT_SOURCES = ("meta", "tactics", "categories")


def infer_tactic_set(meta: dict, turns: list) -> tuple[str, str]:
    """Work out which tactic menu a logged run used, returning (set_name, evidence_source).

    Ranked by trustworthiness, because `proxy_strategy` LIES on the archived CMU runs: those
    were produced by re-pointing the proxy import while the tag stayed hardcoded, so they
    claim the MAFALDA menu while logging CMU tactics. What the run actually DID (its tactics,
    then its categories) therefore outranks what it says about itself.
    """
    recorded = ((meta.get("ablation") or {}).get("tactic_set") or "").strip().lower()
    if recorded in TACTIC_SETS:
        return recorded, "meta"

    # A tactic unique to one set settles it; DIRECT_CHALLENGE is in both and proves nothing.
    for rec in turns:
        tactic = (rec.get("proxy_decision") or {}).get("strategy") or rec.get("state")
        if not tactic:
            continue
        owners = tactic_sets_containing(tactic)
        if len(owners) == 1:
            return owners[0], "tactics"

    # Failing that, the level-1 category: "simple" is CMU, the MAFALDA channels are MAFALDA.
    for rec in turns:
        category = (rec.get("proxy_decision") or {}).get("category") or rec.get("category")
        if not category:
            continue
        owners = tactic_sets_with_category(category)
        if len(owners) == 1:
            return owners[0], "categories"

    # Last and least: the self-description. Better than nothing for a run whose only logged
    # tactic was the shared DIRECT_CHALLENGE.
    desc = str(meta.get("proxy_strategy") or "").lower()
    matches = [name for name in TACTIC_SETS if name in desc]
    if len(matches) == 1:
        return matches[0], "proxy_strategy"

    logger.warning("could not tell which tactic menu this run used — assuming '%s'; "
                   "pass --tactic-set to override", DEFAULT_TACTIC_SET)
    return DEFAULT_TACTIC_SET, "default"


def _parse_jsonl(path: str) -> tuple[dict, list, Optional[dict]]:
    meta, turns, result = None, [], None
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                # A run killed mid-write can leave a truncated final line; everything
                # before it is still usable, so warn rather than abort.
                logger.warning("%s: skipping malformed line %d (%s)",
                               os.path.basename(path), lineno, exc)
                continue
            kind = rec.get("type")
            if kind == "meta":
                if meta is None:
                    meta = rec
            elif kind == "turn":
                turns.append(rec)
            elif kind == "result":
                result = rec
    if meta is None:
        raise ResumeError(f"{path}: no meta record — not a run log")
    if not turns:
        raise ResumeError(f"{path}: no turn records")
    return meta, turns, result


def load_run(path: str, from_turn: Optional[int] = None,
             new_max_turns: Optional[int] = None) -> LoadedRun:
    """Parse a run log and resolve the cut point. Raises ResumeError if it can't be resumed."""
    meta, turns, result = _parse_jsonl(path)

    numbers = [t.get("turn") for t in turns]
    if numbers != list(range(len(numbers))):
        raise ResumeError(f"{path}: turn numbers are not contiguous from 0 ({numbers[:5]}...)")
    last_turn = numbers[-1]

    # Resolve the tactic menu from the WHOLE log, before any branch truncation below — a
    # branch at turn 2 may retain only turn 1, and one turn's tactic can be the shared
    # DIRECT_CHALLENGE, which identifies neither set.
    tactic_set, tactic_set_source = infer_tactic_set(meta, turns)

    if from_turn is not None:
        if from_turn < 1:
            raise ResumeError(f"--from-turn must be >= 1 (turn 0 is the baseline question)")
        start_turn = from_turn - 1
        if start_turn > last_turn:
            raise ResumeError(
                f"{os.path.basename(path)}: cannot branch at turn {from_turn} — the run only "
                f"reached turn {last_turn}, so turn {start_turn} was never logged")
        turns = turns[:start_turn + 1]
        kind = "branch"
    else:
        # Extend mode: the conversation must not already have ended.
        if result is None:
            raise ResumeError(
                f"{os.path.basename(path)}: no result record — the run is incomplete (still "
                f"running, or killed). Use --from-turn to branch from a partial log instead")
        outcome = result.get("outcome")
        if outcome in TERMINAL_OUTCOMES:
            raise ResumeError(
                f"{os.path.basename(path)}: outcome is '{outcome}' — the conversation already "
                f"ended, nothing to extend. Use --from-turn N to re-roll it from turn N")
        start_turn = last_turn
        kind = "extend"

    if new_max_turns is not None and start_turn >= new_max_turns:
        raise ResumeError(
            f"{os.path.basename(path)}: already at turn {start_turn}, which is >= "
            f"--max-turns {new_max_turns} — nothing to run")

    return LoadedRun(meta=meta, turns=turns, result=result,
                     start_turn=start_turn, kind=kind, path=path,
                     tactic_set=tactic_set, tactic_set_source=tactic_set_source)


def build_resume_state(run: LoadedRun) -> ResumeState:
    """Recompute the orchestrator's per-run counters from the retained prefix."""
    scores, eroded_turns, effective_collapse_turns = [], [], []
    first_eroded_turn = first_effective_collapse_turn = None
    winddown_streak, winddown_first_turn, winddown_signal = 0, None, None

    for rec in run.turns[1:]:                      # turn 0 is the baseline; it has no score
        turn = rec["turn"]
        scores.append(rec.get("position_strength"))
        if rec.get("eroded"):
            eroded_turns.append(turn)
            if first_eroded_turn is None:
                first_eroded_turn = turn
        judge = rec.get("judge") or {}
        # Same predicate as the live loop: a soft cave is an effective_collapse that is
        # not (yet) a strict one.
        if judge.get("effective_collapse") is True and judge.get("is_collapsed") is not True:
            effective_collapse_turns.append(turn)
            if first_effective_collapse_turn is None:
                first_effective_collapse_turn = turn
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

    last = run.turns[-1]
    return ResumeState(
        start_turn=run.start_turn,
        kind=run.kind,
        source_path=run.path,
        prior_records=run.turns,
        target_last=last.get("target_output", ""),
        target_reasoning=last.get("target_reasoning", "") or "",
        scores=scores,
        eroded_turns=eroded_turns,
        first_eroded_turn=first_eroded_turn,
        effective_collapse_turns=effective_collapse_turns,
        first_effective_collapse_turn=first_effective_collapse_turn,
        winddown_streak=winddown_streak,
        winddown_first_turn=winddown_first_turn,
        winddown_signal=winddown_signal,
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

    `temperature` defaults to whatever the log recorded, so a continuation samples the
    same way its own prefix did. Logs written before --target-temperature existed have no
    such field and fall back to the module default.
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

    # `context_messages` was written by the original run from this same property, so it is
    # an independent check that the replay produced the same conversation shape.
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
    persona = "adversarial" if run.meta.get("variant", "").endswith("adversarial") else "naturalistic"
    proxy = ProxyAgent(
        client, run.meta["false_premise"], model=model, persona=persona, provider=provider,
        tactic_set=run.tactic_set,
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
        # The raw JSON the model actually emitted is not logged; rebuild an equivalent
        # object from the parsed fields. Key order/whitespace differ from the original,
        # which costs one cache write and nothing else.
        # These replayed turns are what the model reads back as its OWN prior output, so the
        # object must match the schema its system prompt asks for: a flat menu (CMU) never
        # requested a "category", and teaching it one here would invite it to emit one.
        fields = {"reasoning": rec.get("proxy_reasoning", "")}
        if proxy.tactic_set.has_channels:
            fields["category"] = decision.get("category") or rec.get("category", "")
        fields.update({
            "tactic": decision.get("strategy") or rec.get("state", ""),
            "rationale": decision.get("rationale", ""),
            "message": rec.get("proxy_input", ""),
        })
        assistant = json.dumps(fields, ensure_ascii=False)
        proxy._dialogue.append({"role": "user", "content": user_content})
        proxy._dialogue.append({"role": "assistant", "content": assistant})

        # The enum is the union of both menus, so parsing alone no longer proves the tactic
        # belongs to the menu we are replaying — check membership too, or a mis-resolved set
        # would quietly replay tactics the proxy is not being offered.
        state_value = decision.get("strategy") or rec.get("state")
        try:
            strategy = ProxyState(state_value)
        except ValueError:
            raise ResumeError(
                f"{os.path.basename(run.path)}: turn {rec['turn']} has unknown tactic "
                f"{state_value!r} — the tactic menu changed since this run was made")
        if strategy not in proxy.tactic_set.tactic_category:
            raise ResumeError(
                f"{os.path.basename(run.path)}: turn {rec['turn']} used tactic "
                f"{state_value!r}, which is not in the '{proxy.tactic_set.name}' menu this "
                f"resume resolved ({run.tactic_set_source}) — pass --tactic-set to correct it")
        judge = rec.get("judge") or {}
        proxy.record_turn(
            turn=rec["turn"], strategy=strategy,
            proxy_message=rec.get("proxy_input", ""),
            target_reply=rec.get("target_output", ""),
            position_strength=rec.get("position_strength"),
            is_collapsed=judge.get("is_collapsed"),
            effective_collapse=judge.get("effective_collapse"),
            firmness=(decision.get("target_read") or {}).get("firmness", ""),
        )
    return proxy


# --------------------------------------------------------------------------- #
# Config reconciliation + file discovery
# --------------------------------------------------------------------------- #
# meta records these, so a resume takes them from the log rather than the CLI. If the CLI
# explicitly contradicts one, that is a mistake worth stopping for — continuing a
# conversation with a different model silently invalidates it.
def check_config(run: LoadedRun, args) -> None:
    """Abort if an explicitly-passed CLI flag contradicts what the log says the run used."""
    ablation = run.meta.get("ablation") or {}
    checks = [
        ("--target-model", "target_model", run.meta.get("target_model")),
        ("--target-provider", "target_provider", run.meta.get("target_provider")),
        ("--model", "model", run.meta.get("proxy_model") or ablation.get("proxy_model")),
        ("--proxy-provider", "proxy_provider", ablation.get("proxy_provider")),
        ("--target-temperature", "target_temperature", run.meta.get("target_temperature")),
        # Only when we KNOW the run's menu: a set guessed from proxy_strategy (or defaulted)
        # must stay hand-overridable, since that tag is wrong on the archived CMU runs.
        ("--tactic-set", "tactic_set",
         run.tactic_set if run.tactic_set_source in _CONFIDENT_SOURCES else None),
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


def discover_runs(path: str, pattern: str = "sycophancy_strength_*.jsonl") -> list:
    """Resolve --resume-from to a list of run logs.

    A file resolves to itself. A directory resolves to the LATEST log per question, so a
    folder holding re-runs of the same question does not get resumed several times over.
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
        # Group by the filename with the timestamp stripped, so q52 re-runs collapse to one
        # entry and the newest timestamp wins.
        key = _TS_RE.sub("", os.path.basename(f))
        ts = _TS_RE.search(os.path.basename(f))
        stamp = ts.group(1) if ts else ""
        if key not in latest or stamp > latest[key][0]:
            latest[key] = (stamp, f)
    return [f for _, f in sorted(latest.values())]


def resume_output_path(run: LoadedRun, output_dir: str, batch_ts: str,
                       branch_index: Optional[int] = None) -> str:
    """Name the new log. A branch is marked so it is never mistaken for a fresh run.

    `latest_per_question()` in the analysis tooling groups by filename, so an unmarked
    branch would silently outrank the run it forked from.
    """
    base = os.path.basename(run.path)
    stem = _TS_RE.sub("", base) or f"sycophancy_strength_{run.meta.get('topic', 'case')}"
    suffix = ""
    if run.kind == "branch":
        suffix = f"_from{run.start_turn + 1}"
        if branch_index is not None:
            suffix += f"_b{branch_index}"
    return os.path.join(output_dir, f"{stem}{suffix}_{batch_ts}.jsonl")
