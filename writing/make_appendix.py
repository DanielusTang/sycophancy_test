#!/usr/bin/env python3
"""Generate writing/spine_appendix.tex from the pipeline's own constants.

Every prompt in the appendix is pulled from the live module at generation time
rather than retyped, so the appendix cannot drift from the code that produced
the runs. Re-run this after touching any prompt constant:

    python3 writing/make_appendix.py

The per-tactic usage/drop table is recomputed from the shipped T=25 runs under
outputs/naturalistic/sonnet_5/, using the same drop rule as Sec. 6.3 (a turn is
a drop when position_strength falls below the previous scored turn; turn 1 has
no predecessor and is skipped).
"""
from __future__ import annotations

import json
import sys
import textwrap
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FP = ROOT / "false_presuppositions"
UN = ROOT / "unethical_setting"
sys.path.insert(0, str(FP))
sys.path.insert(0, str(UN))

import false_presuppositions_proxy as P  # noqa: E402
import false_presuppositions_judge as J  # noqa: E402
import false_presuppositions_target as T  # noqa: E402

OUT = ROOT / "writing" / "spine_appendix.tex"
CORPUS = FP / "outputs/naturalistic/sonnet_5"
TARGET_DIRS = ["deepseek_v4_pro", "gemini_3.1_pro", "gpt_5.6_terra", "sonnet_5"]

# Prompt boxes are set full-width (\onecolumn); 92 columns fits at \scriptsize,
# and is wide enough that most prompt lines keep their original breaks.
WRAP = 92

# The prompts contain exactly two non-ASCII characters. Neither survives a
# verbatim environment under pdflatex, so both are transliterated and the
# substitution is declared in the appendix text.
TRANSLIT = {"—": "---", "≠": "!=", "·": "-"}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
class Keep(dict):
    """format_map map that leaves unfilled placeholders visible as {name}."""

    def __missing__(self, key):
        return "{" + key + "}"


def fill(template: str, **known) -> str:
    """Resolve the clauses that were actually spliced; keep the rest as placeholders."""
    return template.format_map(Keep(**known))


def wrap(text: str, width: int = WRAP) -> str:
    """Hard-wrap for verbatim boxes, preserving paragraph and list structure."""
    for src, dst in TRANSLIT.items():
        text = text.replace(src, dst)
    out = []
    for line in text.split("\n"):
        if not line.strip():
            out.append("")
            continue
        indent = " " * (len(line) - len(line.lstrip()))
        sub = indent + "  " if line.lstrip().startswith(("-", "STEP", "(")) else indent
        out.extend(textwrap.wrap(line, width=width,
                                 initial_indent=indent, subsequent_indent=sub,
                                 break_long_words=False, break_on_hyphens=False)
                   or [""])
    return "\n".join(out)


TEX_ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(s: str) -> str:
    """Escape for text mode. Non-ASCII is mapped to markup rather than relying
    on inputenc, so the tables compile under a bare pdflatex too."""
    text_map = {"—": "---", "·": r"\textperiodcentered{}", "≠": r"$\neq$"}
    return "".join(text_map.get(c, TEX_ESC.get(c, c)) for c in s)


def box(title: str, body: str, label: str | None = None) -> str:
    lab = f"\n% {label}" if label else ""
    return (f"{lab}\n\\begin{{tcolorbox}}[breakable, colback=black!3, colframe=black!45,\n"
            f"  fonttitle=\\bfseries\\small, title={{{esc(title)}}}]\n"
            f"\\scriptsize\n\\begin{{verbatim}}\n{wrap(body).strip()}\n"
            f"\\end{{verbatim}}\n\\end{{tcolorbox}}\n")


# --------------------------------------------------------------------------- #
# corpus statistics (same rule as Sec. 6.3)
# --------------------------------------------------------------------------- #
def corpus_stats():
    turns_by_tac, drops_by_tac = Counter(), Counter()
    n_scored = n_drops = n_runs = 0
    direct_heavy = 0
    for tgt in TARGET_DIRS:
        for path in sorted((CORPUS / tgt).glob("*.jsonl")):
            lines = path.read_text().splitlines()
            if not lines:
                continue
            meta = json.loads(lines[0])
            if (meta.get("type") != "meta" or meta.get("max_turns") != 25
                    or "mafalda23+direct" not in (meta.get("proxy_strategy") or "")):
                continue
            n_runs += 1
            prev = None
            run_tactics = []
            for ln in lines[1:]:
                rec = json.loads(ln)
                if rec.get("type") != "turn":
                    continue
                state, ps = rec.get("state"), rec.get("position_strength")
                if state is None or ps is None:
                    continue  # turn 0 carries no tactic and no score
                n_scored += 1
                turns_by_tac[state] += 1
                run_tactics.append(state)
                if prev is not None and ps < prev:
                    n_drops += 1
                    drops_by_tac[state] += 1
                prev = ps
            if run_tactics and sum(t == "DIRECT_CHALLENGE" for t in run_tactics) / len(run_tactics) > 0.5:
                direct_heavy += 1
    return dict(turns=turns_by_tac, drops=drops_by_tac, n_scored=n_scored,
                n_drops=n_drops, n_runs=n_runs, direct_heavy=direct_heavy)


# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #
CHANNEL_LABEL = {
    P.FallacyCategory.CREDIBILITY: ("Credibility", "Ethos"),
    P.FallacyCategory.LOGIC: ("Logic", "Logos"),
    P.FallacyCategory.EMOTION: ("Emotion", "Pathos"),
    P.FallacyCategory.NO_FALLACY: ("No fallacy", "control"),
}


def split_desc(desc: str):
    """SIMPLE_TACTICS entries open with a short bracket label; separate it out."""
    if desc.startswith("[") and "]" in desc:
        i = desc.index("]")
        return desc[1:i], desc[i + 1:].strip()
    return "", desc


def taxonomy_table() -> str:
    rows = []
    for cat, members in P.CATEGORIES.items():
        name, greek = CHANNEL_LABEL[cat]
        rows.append(f"\\midrule\n\\multicolumn{{3}}{{l}}{{\\emph{{{name} ({greek})}} "
                    f"--- {len(members)} " + ("entry" if len(members) == 1 else "entries") + "} \\\\\n\\midrule")
        for st in members:
            label, body = split_desc(P.SIMPLE_TACTICS[st])
            rows.append(f"\\texttt{{\\scriptsize {esc(st.value)}}} & {esc(label)} & {esc(body)} \\\\")
    return ("\\begin{longtable}{@{}p{0.22\\textwidth}p{0.13\\textwidth}p{0.57\\textwidth}@{}}\n"
            "\\caption{The 24-entry tactic menu offered to the user proxy at every turn: the 23 "
            "level-2 MAFALDA fallacies grouped under their three level-1 categories, plus the "
            "non-fallacious control channel. Names are the literal values logged in the "
            "\\texttt{state} field of every run; descriptions are the text the proxy actually "
            "sees.}\\label{tab:mafalda-menu}\\\\\n"
            "\\toprule\n\\textbf{Tactic} & \\textbf{Short label} & \\textbf{Description shown to the proxy} \\\\\n"
            "\\endfirsthead\n\\toprule\n\\textbf{Tactic} & \\textbf{Short label} & "
            "\\textbf{Description shown to the proxy} \\\\\n\\endhead\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{longtable}\n")


def usage_table(s) -> str:
    rows = []
    for cat, members in P.CATEGORIES.items():
        name, greek = CHANNEL_LABEL[cat]
        ct = sum(s["turns"][m.value] for m in members)
        cd = sum(s["drops"][m.value] for m in members)
        rows.append("\\midrule")
        for st in sorted(members, key=lambda m: -s["turns"][m.value]):
            t, d = s["turns"][st.value], s["drops"][st.value]
            rows.append(f"\\quad \\texttt{{\\scriptsize {esc(st.value)}}} & {t} & "
                        f"{100*t/s['n_scored']:.1f} & {d} & {100*d/s['n_drops']:.1f} \\\\")
        rows.append(f"\\cmidrule(l){{1-5}}\n\\emph{{{name} ({greek})}} & \\textbf{{{ct}}} & "
                    f"\\textbf{{{100*ct/s['n_scored']:.1f}}} & \\textbf{{{cd}}} & "
                    f"\\textbf{{{100*cd/s['n_drops']:.1f}}} \\\\")
    return ("\\begin{table}[t]\n\\centering\\small\n"
            "\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n"
            "& \\multicolumn{2}{c}{\\textbf{Turns}} & \\multicolumn{2}{c}{\\textbf{Strength drops}} \\\\\n"
            "\\cmidrule(lr){2-3}\\cmidrule(l){4-5}\n"
            "\\textbf{Tactic} & $n$ & \\% & $n$ & \\% \\\\\n"
            + "\n".join(rows) + "\n\\midrule\n"
            f"\\textbf{{Total}} & \\textbf{{{s['n_scored']}}} & \\textbf{{100.0}} & "
            f"\\textbf{{{s['n_drops']}}} & \\textbf{{100.0}} \\\\\n"
            "\\bottomrule\n\\end{tabular}\n"
            "\\caption{Per-tactic usage and damage over the "
            f"{s['n_runs']} naturalistic runs at $T=25$ ({s['n_scored']} scored turns, "
            f"{s['n_drops']} strength drops). A turn is a \\emph{{drop}} when the judge's "
            "position strength falls below the previous scored turn; turn 1 has no predecessor "
            "and is excluded. Level-1 rows are the totals reported in "
            "\\S\\ref{sec:analysis}.}\\label{tab:mafalda-usage}\n\\end{table}\n")


# --------------------------------------------------------------------------- #
# assembled prompts
# --------------------------------------------------------------------------- #
def naturalistic_frame() -> str:
    """The naturalistic task frame with its menu-shaped slots resolved for the MAFALDA menu.

    The frame delegates the menu intro (the STEP 1 / STEP 2 instruction) and the "category"
    JSON field to the active TacticSet, so that the CMU-5 menu can drop both. The paper
    documents the MAFALDA benchmark, so splice MAFALDA's back in. These are the RAW values —
    the {category_csv} inside them stays a visible placeholder, as every other unfilled slot
    in these boxes does (`fill` substitutes in one pass and never rescans what it inserted).
    """
    return fill(P.NATURALISTIC_TASK_FRAME,
                menu_intro=P.MAFALDA.menu_intro["naturalistic"],
                category_json=P.MAFALDA.category_json)


def proxy_system() -> str:
    persona = fill(P.PROXY_NATURALISTIC_SYSTEM_PROMPT_TEMPLATE,
                   reasoning_clause=P._NATURALISTIC_BLIND_CLAUSE)
    return persona + naturalistic_frame()


def proxy_turn_user() -> str:
    return fill(P.NATURALISTIC_TURN_USER,
                visibility_note=P._NATURALISTIC_BLIND_NOTE, reasoning_block="")


def menu_excerpt() -> str:
    return P.render_menu([P.FallacyCategory.EMOTION, P.FallacyCategory.NO_FALLACY])


def target_prompt() -> str:
    return T.TARGET_SYSTEM_PROMPT_TEMPLATE


def insertions(base: str, variant: str, min_words: int = 4) -> list[str]:
    """Word-level diff: the passages `variant` adds to `base`.

    Used so the stereotype-scenario deltas are extracted from the two live
    templates rather than transcribed by hand.
    """
    import difflib
    bw, vw = base.split(), variant.split()
    out = []
    for tag, _, _, j1, j2 in difflib.SequenceMatcher(None, bw, vw).get_opcodes():
        if tag in ("insert", "replace") and j2 - j1 >= min_words:
            out.append(" ".join(vw[j1:j2]))
    return out


def slice_from(text: str, start: str, end: str | None = None) -> str:
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j].rstrip()


# --------------------------------------------------------------------------- #
# document
# --------------------------------------------------------------------------- #
HEADER = r"""% ============================================================
% Ready-to-paste LaTeX for the SPINE Appendix.
%
% GENERATED FILE -- do not hand-edit the prompt boxes or the two
% tables. Regenerate with:
%     python3 writing/make_appendix.py
% Every prompt below is pulled verbatim from the module that ran
% the experiments, so the appendix cannot drift from the code.
%
% Resolves the placeholders left in the body:
%   Appendix~[A] (spine_section3.tex:133) -> \ref{app:persona}
%   Appendix~[B] (spine_section3.tex:156) -> \ref{app:mafalda}
%   Appendix~[X] (spine_section4.tex:185, :213) -> \ref{app:params}
%   the appendix note at spine_section6.tex:175-179 -> \ref{app:mafalda}
%
% Preamble requirements:
%   \usepackage{tcolorbox}\tcbuselibrary{breakable}
%   \usepackage{booktabs}
%   \usepackage{longtable}
%
% Layout: the whole appendix is single-column (\onecolumn right
% after \appendix, never switched back). Two reasons, both hard:
% the prompts are wrapped at 92 columns and overflow a single ACL
% column, and the menu table is a longtable, which LaTeX cannot
% set inside a two-column region at all. If you add further
% appendices after this one and want them in two columns, put
% \twocolumn at the top of the first of them.
%
% Labels defined here: app:prompts, app:persona, app:menu, app:judge,
% app:target, app:deltas, app:ablation-prompts, app:mafalda,
% app:params, tab:mafalda-menu, tab:mafalda-usage, tab:decoding.
% Labels referenced but defined elsewhere: sec:proxy, sec:judge,
% sec:protocol, sec:analysis, sec:models, sec:judge-reliability.
% ============================================================

\appendix
\onecolumn

\section{Prompts}
\label{app:prompts}

Every prompt in this appendix is reproduced verbatim from the code that
generated the runs. Text in braces marks a slot filled at run time:
\verb|{question}|, \verb|{false_premise}|, and \verb|{correction}| are the
three fields of a CREPE item, and the remaining slots carry per-turn state.
Line breaks inside the boxes are the prompts' own except where a line exceeded
the page, and two characters are transliterated because they cannot be set
verbatim: the em dash appears as \texttt{-{}-{}-} and \texttt{U+2260} as
\texttt{!=}. Nothing else is altered, and the boxes are generated from the
source constants rather than transcribed.
"""


def main():
    s = corpus_stats()
    parts = [HEADER]

    # ---------------- persona ----------------
    parts.append(r"""
\subsection{User Proxy Persona}
\label{app:persona}

The proxy's system prompt is assembled once per item, in
\texttt{ProxyAgent.\_\_init\_\_}, from a persona preamble and a task frame; the
two are concatenated and sent as a single \texttt{system} message. Box~1 shows
the result. The \verb|{reasoning_clause}| slot is filled with the blind clause
in every run reported in this paper --- the proxy sees only what the target
says to it. Box~2 is the user message appended on each turn, which carries the
only volatile state: the target's latest reply, the turn counter, and a recap
of the proxy's own recent moves.

Three properties of this prompt carry claims made in \S\ref{sec:proxy}. First,
the full 24-entry tactic menu is rendered into the \emph{system} prompt once and
never resent, so the proxy is never restricted to a subset of the menu and the
prefix stays byte-stable for caching. Second, the constraints that bound the
persona to a sincere user --- never manipulate, never fake agreement, never
concede or soften the original claim, add a new argument each turn, one
first-person sentence, never reveal the role --- are all in the task frame, not
in a per-turn instruction, so they hold identically at turn 1 and turn 25.
Third, the persona is blind to the judge's scores at every turn: no score is
ever placed in its context.

The pipeline defines exactly two personas, \texttt{naturalistic} and
\texttt{adversarial}. The naturalistic persona below is the one used for every
headline result; the adversarial persona is an ablation condition and appears in
\S\ref{app:ablation-prompts}.
""")
    parts.append(box("Box 1 --- Proxy system prompt (naturalistic persona, as assembled)",
                     proxy_system()))
    parts.append(box("Box 2 --- Proxy per-turn user message", proxy_turn_user()))

    # ---------------- menu ----------------
    parts.append(r"""
\subsection{Tactic Menu Block}
\label{app:menu}

The \verb|{strategy_menu}| slot in Box~1 is filled with the full menu, grouped
by level-1 channel. Box~3 shows the rendered form of two channels; the
remaining two are identical in format, and every entry is listed in
Table~\ref{tab:mafalda-menu}. The proxy commits to a channel, then a tactic
within it, then writes its sentence, in one structured call.

One implementation detail matters for reading \S\ref{sec:analysis}. The
decision parser treats the \emph{tactic} as authoritative and derives the
level-1 category from it, so a reply whose declared category contradicts its
chosen tactic cannot corrupt the category-level analysis. The same parser falls
back to \texttt{DIRECT\_CHALLENGE} when a reply cannot be parsed at all, which
would inflate the control channel if it fired often. It does not: only
""" + str(s["direct_heavy"]) + r""" of the """ + str(s["n_runs"]) + r""" runs
give \texttt{DIRECT\_CHALLENGE} more than half their turns, so the control
channel's share is a genuine choice by the proxy rather than the parser default
in disguise.
""")
    parts.append(box("Box 3 --- Rendered menu, two of four channels", menu_excerpt()))

    # ---------------- judge ----------------
    parts.append(r"""
\subsection{Judge}
\label{app:judge}

The judge scores one reply at a time and returns the three signals described in
\S\ref{sec:judge}. Box~4 is its system prompt and Box~5 the per-turn template.
The rubric in Box~5 is where the conservatism of the collapse criterion lives:
PART~A requires an own-voice, unconditional, general assertion of the false
premise and enumerates the near-misses that do not qualify, PART~B fixes the
0--4 strength scale, and PART~C records whether the correct fact survives in the
reply at all.

The wind-down detector referenced in \S\ref{sec:protocol} is a deterministic
regular-expression check over the target's own closing phrases, not a model
call, so it has no prompt. It is disabled in every run reported here.
""")
    parts.append(box("Box 4 --- Judge system prompt", J.STRENGTH_JUDGE_SYSTEM_PROMPT))
    parts.append(box("Box 5 --- Judge per-turn template",
                     fill(J.STRENGTH_JUDGE_PROMPT_TEMPLATE)))

    # ---------------- target ----------------
    parts.append(r"""
\subsection{Target System Prompt}
\label{app:target}

Every target receives the same minimal system prompt, with no persona, no
instruction about how to handle disagreement, and no mention of the evaluation
(Box~6). \verb|{question}| is the CREPE question, drawn line-for-line in
parallel with the false premise and the gold correction that the judge scores
against. The same prompt is used in both scenarios.
""")
    parts.append(box("Box 6 --- Target system prompt (all targets, both scenarios)",
                     target_prompt()))

    # ---------------- deltas ----------------
    import unethical_proxy as UP
    import unethical_judge as UJ
    parts.append(r"""
\subsection{Stereotype-Scenario Deltas}
\label{app:deltas}

The unethical-queries scenario reuses the prompts above with four insertions,
all of which do the same work: they stop a concession about \emph{individuals}
from being read as a concession about the \emph{group}, which is the claim
actually under test. Box~7 gives the clauses added to the proxy. The target
prompt is unchanged.

The judge gains two signals beyond the three in \S\ref{sec:judge} ---
\texttt{endorsed\_discriminatory\_action}, whether the reply recommends acting
on the stereotype, and \texttt{evidence\_capitulation}, whether it accepts the
user's anecdote as adequate grounds for a group-level claim --- scored by the
two extra rubric parts in Box~8. These support the harm-level measurements in
\S\ref{sec:harm}.

One tactic exists in this setting that the proxy can never choose:
\texttt{ESSENTIALIST\_FRAMING} is held off the rendered menu and fired only by
the cold-start baseline probe, so the proxy's choice space here is the same
23 fallacies plus the control channel as in the first scenario.
""")
    pre = insertions(P.PROXY_NATURALISTIC_SYSTEM_PROMPT_TEMPLATE,
                     UP.PROXY_NATURALISTIC_SYSTEM_PROMPT_TEMPLATE)
    # Resolve the FP frame's menu slots before diffing, or the unethical setting's still-inline
    # STEP 1 / STEP 2 text would be reported as an insertion of its own.
    frame = insertions(naturalistic_frame(), UP.NATURALISTIC_TASK_FRAME)
    adv = insertions(P.PROXY_ADVERSARIAL_SYSTEM_PROMPT_TEMPLATE,
                     UP.PROXY_ADVERSARIAL_SYSTEM_PROMPT_TEMPLATE)
    delta = "\n\n".join([
        "--- added to the naturalistic persona preamble ---", "\n".join(pre),
        "--- added to the naturalistic task frame ---", "\n".join(frame),
        "--- added to the adversarial persona preamble ---", "\n".join(adv),
        "--- off-menu baseline probe (never selectable by the proxy) ---",
        UP.SIMPLE_TACTICS[UP.ProxyState.ESSENTIALIST_FRAMING],
    ])
    judge_delta = "\n\n".join([
        "--- added to the judge system prompt ---",
        "\n".join(insertions(J.STRENGTH_JUDGE_SYSTEM_PROMPT, UJ.STRENGTH_JUDGE_SYSTEM_PROMPT)),
        "--- added rubric parts ---",
        slice_from(UJ.STRENGTH_JUDGE_PROMPT_TEMPLATE, "PART D", "Return ONLY this JSON"),
    ])
    parts.append(box("Box 7 --- Stereotype-scenario proxy clauses", delta))
    parts.append(box("Box 8 --- Stereotype-scenario judge, added signals and rubric parts",
                     judge_delta))

    # ---------------- ablation prompts ----------------
    parts.append(r"""
\subsection{Ablation-Only Clauses}
\label{app:ablation-prompts}

None of the following is used in the headline results; each defines one
condition in the pressure-generator ablation. The reasoning-access condition
replaces the blind clause of Box~1 with a sighted one and appends the target's
private trace to each turn. The adversarial persona replaces the sincere
preamble outright with an attacker that reads the target's firmness and picks
the tactic most likely to move it.
""")
    parts.append(box("Box 9 --- Reasoning-access clause (replaces the blind clause)",
                     P._NATURALISTIC_SIGHTED_CLAUSE + "\n\n"
                     + fill(P.NATURALISTIC_REASONING_BLOCK_TEMPLATE)))
    parts.append(box("Box 10 --- Adversarial persona preamble",
                     fill(P.PROXY_ADVERSARIAL_SYSTEM_PROMPT_TEMPLATE,
                          reasoning_clause="", score_clause="")))

    # ---------------- taxonomy ----------------
    parts.append(r"""
\section{The Tactic Menu}
\label{app:mafalda}

Table~\ref{tab:mafalda-menu} lists the menu in full. The 23 level-2 fallacies
and their three level-1 groupings are taken from MAFALDA
\citep{helwe2024mafalda}; the fourth channel, holding the single non-fallacious
tactic \texttt{DIRECT\_CHALLENGE}, is ours and serves as the control against
which the fallacies are compared. The channels are uneven by construction ---
seven entries under Credibility, ten under Logic, six under Emotion, one
control --- because they inherit MAFALDA's own structure rather than a balanced
design of ours.

Table~\ref{tab:mafalda-usage} gives the level-2 breakdown deferred from
\S\ref{sec:analysis}: how often the proxy reached for each tactic, and how often
a turn using it preceded a drop in position strength. Per-tactic cells are thin,
which is why the body reports at the level of channels; the table is included
because the level-1 asymmetry it aggregates --- emotion doing more damage than
its share of turns, logic less --- is visible in the individual tactics as well.
""")
    parts.append(taxonomy_table())
    parts.append(usage_table(s))

    # ---------------- params ----------------
    parts.append(PARAMS)

    OUT.write_text("\n".join(parts))
    print(f"wrote {OUT}")
    print(f"  runs={s['n_runs']} scored_turns={s['n_scored']} drops={s['n_drops']} "
          f"direct_heavy={s['direct_heavy']}")


PARAMS = r"""
\section{Models and Decoding Parameters}
\label{app:params}

Table~\ref{tab:decoding} gives the exact configuration of every model reported
in the paper. Three of the four targets, and both non-target roles, are
reasoning models whose providers do not accept a sampling temperature when
extended thinking is active; for those the parameter is omitted from the request
rather than set to a value, and we report it as such rather than quoting a
default that never reached the API. This has one consequence worth stating
plainly: the judge is not deterministic. Its configured temperature of $0$ is
among the parameters dropped on this path, which is why the pipeline supports
majority voting over repeated judgements, though all runs reported here use a
single sample. \S\ref{sec:judge-reliability} addresses judge stability directly.

No \texttt{top\_p}, seed, stop sequence, or frequency and presence penalty is
set anywhere in the pipeline; all are left at provider defaults. Requests time
out at 300\,s and are retried up to six times with exponential backoff between
2 and 60\,s. Anthropic calls mark the system block and, on multi-turn calls, the
most recent message with an ephemeral cache breakpoint; this affects cost, not
sampling. No API version header is pinned for any provider, so each SDK sent its
own built-in default.

Two asymmetries are visible in Table~\ref{tab:decoding} and we flag them rather
than let them be discovered. The DeepSeek target ran at a quarter of the
output-token budget of the two largest, an artefact of a provider-specific
default rather than a deliberate choice, and the limit does occasionally bind:
10 of its 870 scored replies, or 1.1\%, end mid-sentence, against one such reply
across the other three targets combined. The effect is small and falls on the
target's longest answers rather than on any particular item, but the budget was
not equal across targets. And Gemini is reached through its native
endpoint rather than the OpenAI-compatible shim, because only the native
endpoint returns thought summaries, so its request fields are named differently
from the others.

Each run's log records the models, the turn budget, and the ablation flags in a
header line, so the shipped transcripts are self-describing on configuration;
the decoding parameters in Table~\ref{tab:decoding} are properties of the code
rather than of any individual run.

\begin{table}[t]
\centering\small
\begin{tabular}{@{}llllll@{}}
\toprule
\textbf{Role} & \textbf{Model ID} & \textbf{Interface} & \textbf{Temp.} & \textbf{Output cap} & \textbf{Thinking} \\
\midrule
Proxy  & \texttt{claude-sonnet-5} & \texttt{anthropic} SDK, Messages & --- & 8192 & adaptive, summarized \\
Judge  & \texttt{claude-sonnet-5} & \texttt{anthropic} SDK, Messages & --- & 8192 & adaptive, summarized \\
\midrule
Target & \texttt{claude-sonnet-5} & \texttt{anthropic} SDK, Messages & --- & 8192 & adaptive, summarized \\
Target & \texttt{gpt-5.6-terra} & \texttt{openai} SDK, chat completions & --- & 8192\rlap{$^{\dagger}$} & model-internal \\
Target & \texttt{gemini-3.1-pro-preview} & native \texttt{:generateContent} & 0.6 & 4096\rlap{$^{\ddagger}$} & dynamic budget \\
Target & \texttt{deepseek-v4-pro} & \texttt{openai} SDK, chat completions & 0.6 & 2048 & --- \\
\bottomrule
\end{tabular}
\caption{Decoding parameters and interfaces. ``---'' under Temperature means the
parameter is omitted from the request, not set to zero: these models reject a
sampling temperature while extended thinking is active.
$^{\dagger}$~sent as \texttt{max\_completion\_tokens}.
$^{\ddagger}$~sent as \texttt{maxOutputTokens}, with a dynamic thinking budget
and thought summaries requested. All runs use a 25-turn budget, give the proxy
the full conversation rather than a window, and disable both the
judge-feedback and reasoning-access ablations.}
\label{tab:decoding}
\end{table}
"""

if __name__ == "__main__":
    main()
