#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the assembled question banks as one self-contained HTML case browser.

The banks live as line-aligned .txt files that the runner reads but a person cannot
review. This emits a single page listing every case with its question, presupposition,
correction, bias type, target, theme and the raw source sentence it came from, filterable
by bank / type / target / free text.

The data is READ FROM THE ASSEMBLED BANK FILES, never retyped, so the page cannot drift
from what `unethical_main.py --cases-dir` would actually run. Add a bank by naming its
directory on the command line.

Usage
-----
    python3 build_bank_page.py                     # both banks -> default scratchpad path
    python3 build_bank_page.py -o /tmp/banks.html
    python3 build_bank_page.py --bank bank_a_csv   # one bank only
"""

from __future__ import annotations

import argparse
import collections
import csv
import itertools
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_ROOT = os.path.join(_HERE, "questions")

# label -> directory under questions/. Order here is the order banks appear in the UI.
DEFAULT_BANKS = [("A", "bank_a_csv"), ("B", "bank_b_stereoset"), ("C", "bank_c_bbq")]

DEFAULT_OUT = ("/private/tmp/claude-501/-Users-danielus-sycophancy-test/"
               "093c0672-4b19-4bd2-abc5-ae99238f57af/scratchpad/bank_browser.html")

# StereoSet's four bias types, in the fixed order the categorical hues are assigned in.
# Banks A and B use exactly these; BBQ-sourced banks use their own ten axes instead.
TYPE_ORDER = ["race", "profession", "gender", "religion"]


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def _lines(path: str) -> list:
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def load_bank(label: str, dirname: str) -> list:
    """One bank's cases, in the order the runner would number them (1-based `q`).

    questions/presuppositions/corrections/categories are line-aligned by construction —
    that is the contract `unethical_main.load_cases` enforces — and sources.tsv carries the
    matching provenance row per case. `theme` and `group` are the one thing only cases.jsonl
    has, joined on (bias_type, target, stereotype): the same key build_question_bank's
    resolve_provenance uses, so a failed join means the bank was hand-edited out of sync.
    """
    bank_dir = os.path.join(QUESTIONS_ROOT, dirname)
    questions = _lines(os.path.join(bank_dir, "questions.txt"))
    presups = _lines(os.path.join(bank_dir, "presuppositions.txt"))
    corrections = _lines(os.path.join(bank_dir, "corrections.txt"))
    categories = _lines(os.path.join(bank_dir, "categories.txt"))

    with open(os.path.join(bank_dir, "sources.tsv"), encoding="utf-8") as fh:
        sources = list(csv.DictReader(fh, delimiter="\t"))

    counts = {"questions": len(questions), "presuppositions": len(presups),
              "corrections": len(corrections), "categories": len(categories),
              "sources": len(sources)}
    if len(set(counts.values())) != 1:
        raise SystemExit(f"{dirname}: files are not line-aligned: {counts}")

    with open(os.path.join(bank_dir, "cases.jsonl"), encoding="utf-8") as fh:
        curated = {(c["bias_type"], c["target"], " ".join(c["stereotype"].split())): c
                   for c in (json.loads(ln) for ln in fh if ln.strip())}

    cases, unjoined = [], []
    for i, (question, presup, correction, category, source) in enumerate(
            zip(questions, presups, corrections, categories, sources), start=1):
        claim = " ".join((source.get("source_claim") or "").split())
        extra = curated.get((category, source["target"], claim))
        if extra is None:
            unjoined.append(i)
        cases.append({
            "bank": label,
            "q": i,
            "type": category,
            "target": source["target"],
            "theme": (extra or {}).get("theme", ""),
            "group": (extra or {}).get("group", ""),
            "question": question,
            "presupposition": presup,
            "correction": correction,
            "source": claim,
            "dataset": source.get("source_dataset", ""),
        })

    if unjoined:
        raise SystemExit(f"{dirname}: {len(unjoined)} case(s) had no cases.jsonl match "
                         f"(q={unjoined[:5]}…) — re-run `assemble {dirname}`")
    return cases


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
CSS = """
:root {
  color-scheme: light dark;
  --paper:      #f5f7f8;
  --surface:    #ffffff;
  --surface-2:  #eef1f3;
  --ink:        #111719;
  --ink-2:      #4a565c;
  --ink-3:      #77858c;
  --rule:       #d6dde1;
  --rule-2:     #c2ccd2;
  --accent:     #1f4e5f;
  --accent-ink: #ffffff;
  --claim-bg:   #fbf3ee;
  --claim-rule: #c9a58c;
  --fix-bg:     #eef4f2;
  --fix-rule:   #8fb3a6;
  /* Categorical slots 1-4 of the validated reference palette, in fixed order. Both modes
     pass every hard gate on the adjacent pairlist, which is the one a stacked bar uses.
     Light mode WARNs on contrast for aqua/yellow, so the relief rule applies: the counts
     are directly labelled on every segment and repeated in the concentration table. */
  --race:       #2a78d6;
  --profession: #eb6834;
  --gender:     #1baf7a;
  --religion:   #eda100;
  --on-race:       #ffffff;
  --on-profession: #ffffff;
  --on-gender:     #06231a;
  --on-religion:   #241a00;

  --serif: 'Iowan Old Style', 'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif;
  --mono: ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace;

  --step-0: 0.9375rem;
  --step-1: 1.0625rem;
  --step-2: 1.375rem;
  --step-3: 1.875rem;
  --micro: 0.6875rem;
  --small: 0.8125rem;
}

@media (prefers-color-scheme: dark) {
  :root {
    --paper:      #0e1315;
    --surface:    #151c1f;
    --surface-2:  #1c252a;
    --ink:        #e6edf0;
    --ink-2:      #a8b6bd;
    --ink-3:      #7b8b93;
    --rule:       #263238;
    --rule-2:     #33444c;
    --accent:     #6fb3c4;
    --accent-ink: #08131a;
    --claim-bg:   #241b16;
    --claim-rule: #7d5a44;
    --fix-bg:     #13221f;
    --fix-rule:   #46705f;
    --race:       #3987e5;
    --profession: #d95926;
    --gender:     #199e70;
    --religion:   #c98500;
    --on-race:       #ffffff;
    --on-profession: #ffffff;
    --on-gender:     #06231a;
    --on-religion:   #241a00;
  }
}

/* The viewer's toggle stamps data-theme on the root and must beat the media query
   in BOTH directions, so each theme is restated here rather than only the dark one. */
:root[data-theme="light"] {
  --paper: #f5f7f8; --surface: #ffffff; --surface-2: #eef1f3;
  --ink: #111719; --ink-2: #4a565c; --ink-3: #77858c;
  --rule: #d6dde1; --rule-2: #c2ccd2;
  --accent: #1f4e5f; --accent-ink: #ffffff;
  --claim-bg: #fbf3ee; --claim-rule: #c9a58c;
  --fix-bg: #eef4f2; --fix-rule: #8fb3a6;
  --race: #2a78d6; --profession: #eb6834; --gender: #1baf7a; --religion: #eda100;
  --on-race: #ffffff; --on-profession: #ffffff;
  --on-gender: #06231a; --on-religion: #241a00;
}
:root[data-theme="dark"] {
  --paper: #0e1315; --surface: #151c1f; --surface-2: #1c252a;
  --ink: #e6edf0; --ink-2: #a8b6bd; --ink-3: #7b8b93;
  --rule: #263238; --rule-2: #33444c;
  --accent: #6fb3c4; --accent-ink: #08131a;
  --claim-bg: #241b16; --claim-rule: #7d5a44;
  --fix-bg: #13221f; --fix-rule: #46705f;
  --race: #3987e5; --profession: #d95926; --gender: #199e70; --religion: #c98500;
  --on-race: #ffffff; --on-profession: #ffffff;
  --on-gender: #06231a; --on-religion: #241a00;
}

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--serif);
  font-size: var(--step-1);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.wrap { max-width: 62rem; margin: 0 auto; padding: 0 1.25rem; }

/* ---- masthead ---- */
.masthead { padding: 2.75rem 0 1.5rem; border-bottom: 1px solid var(--rule); }
.eyebrow {
  font-family: var(--mono); font-size: var(--micro); letter-spacing: 0.13em;
  text-transform: uppercase; color: var(--ink-3); margin: 0 0 0.75rem;
}
.masthead h1 {
  margin: 0 0 0.6rem; font-size: var(--step-3); font-weight: 600;
  letter-spacing: -0.015em; line-height: 1.15; text-wrap: balance;
}
.lede { margin: 0; max-width: 62ch; color: var(--ink-2); font-size: var(--step-0); }
.notice {
  margin: 1.25rem 0 0; padding: 0.75rem 0.9rem; max-width: 62ch;
  background: var(--claim-bg); border-left: 3px solid var(--claim-rule);
  font-size: var(--small); line-height: 1.5; color: var(--ink-2);
}
.notice strong { color: var(--ink); font-weight: 600; }

/* ---- composition comparison ---- */
.summary { padding: 2rem 0 1.75rem; border-bottom: 1px solid var(--rule); }
.summary > h2 {
  margin: 0 0 0.35rem; font-size: var(--step-2); font-weight: 600;
  letter-spacing: -0.01em; text-wrap: balance;
}
.summary > p {
  margin: 0 0 1.6rem; max-width: 62ch; color: var(--ink-2); font-size: var(--step-0);
}

.banks { display: grid; grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr)); gap: 1.75rem; }

.hero { display: flex; align-items: baseline; gap: 0.7rem; margin-bottom: 0.9rem; }
.hero .num {
  font-size: 3.25rem; line-height: 0.9; font-weight: 500;
  letter-spacing: -0.03em; font-variant-numeric: tabular-nums;
}
.hero .cap { color: var(--ink-2); font-size: var(--step-0); line-height: 1.35; }
.hero .cap b {
  display: block; font-family: var(--mono); font-size: var(--micro);
  letter-spacing: 0.13em; text-transform: uppercase; color: var(--ink-3);
  font-weight: 600; margin-bottom: 0.15rem;
}

/* 2px surface gaps between segments; the outer ends are the only rounded ones, so the
   bar still reads as one 100% whole rather than four detached pills. */
.bar { display: flex; gap: 2px; height: 2.5rem; margin-bottom: 0.9rem; }
.seg {
  display: flex; align-items: center; justify-content: center; min-width: 0;
  font-family: var(--mono); font-size: var(--small); font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.bar .seg:first-child { border-radius: 4px 0 0 4px; }
.bar .seg:last-child  { border-radius: 0 4px 4px 0; }
.seg[data-type="race"]       { background: var(--race);       color: var(--on-race); }
.seg[data-type="profession"] { background: var(--profession); color: var(--on-profession); }
.seg[data-type="gender"]     { background: var(--gender);     color: var(--on-gender); }
.seg[data-type="religion"]   { background: var(--religion);   color: var(--on-religion); }

/* A bank on a different taxonomy gets one recessive hue, not four categorical ones:
   its segments are equal by construction, so hue would encode nothing. */
.seg.flat { background: var(--accent); opacity: 0.55; }
.sw.flat  { background: var(--accent); opacity: 0.55; }

.bank-note {
  margin: 0.7rem 0 0; font-family: var(--mono); font-size: var(--micro);
  letter-spacing: 0.06em; color: var(--ink-3);
}

.legend { display: flex; flex-direction: column; gap: 0.45rem; }
.legend-row {
  display: grid; grid-template-columns: 0.8rem 1fr auto auto;
  align-items: baseline; gap: 0.6rem;
  font-size: var(--step-0);
}
.sw { width: 0.8rem; height: 0.8rem; border-radius: 2px; transform: translateY(0.05rem); }
.sw[data-type="race"]       { background: var(--race); }
.sw[data-type="profession"] { background: var(--profession); }
.sw[data-type="gender"]     { background: var(--gender); }
.sw[data-type="religion"]   { background: var(--religion); }
.legend-row .val {
  font-family: var(--mono); font-size: var(--small);
  font-variant-numeric: tabular-nums; color: var(--ink);
}
.legend-row .pct {
  font-family: var(--mono); font-size: var(--small);
  font-variant-numeric: tabular-nums; color: var(--ink-3); min-width: 3ch; text-align: right;
}

/* Headline figure for the one number that changes how results may be reported. */
.stat {
  display: flex; align-items: baseline; gap: 0.9rem;
  margin: 0 0 0.5rem; padding: 0.9rem 1rem;
  background: var(--claim-bg); border-left: 3px solid var(--claim-rule);
}
.stat-num {
  font-size: 2.5rem; line-height: 1; font-weight: 500;
  letter-spacing: -0.03em; font-variant-numeric: tabular-nums;
}
.stat-cap { color: var(--ink-2); font-size: var(--step-0); line-height: 1.45; max-width: 58ch; }

/* A count above the threshold is the thing to look at, so it carries weight rather than
   a colour — the four categorical hues already spend the page's colour budget. */
td.hot { color: var(--ink); font-weight: 600; }

code {
  font-family: var(--mono); font-size: 0.9em;
  background: var(--surface-2); padding: 0.05em 0.3em; border-radius: 2px;
}

.conc { margin-top: 1.75rem; overflow-x: auto; }
.conc h3 {
  margin: 0 0 0.2rem; font-family: var(--mono); font-size: var(--micro);
  letter-spacing: 0.13em; text-transform: uppercase; color: var(--ink-3); font-weight: 600;
}
.conc > p { margin: 0 0 0.8rem; max-width: 62ch; color: var(--ink-2); font-size: var(--small); }
table { border-collapse: collapse; width: 100%; font-size: var(--small); }
th, td {
  text-align: left; padding: 0.4rem 0.9rem 0.4rem 0;
  border-bottom: 1px solid var(--rule); white-space: nowrap;
}
th {
  font-family: var(--mono); font-size: var(--micro); letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-3); font-weight: 600;
}
td { font-family: var(--mono); font-variant-numeric: tabular-nums; color: var(--ink-2); }
td.name { color: var(--ink); }
td em { font-style: normal; color: var(--ink-3); }

/* ---- controls ---- */
.controls {
  position: sticky; top: 0; z-index: 20;
  background: var(--paper); border-bottom: 1px solid var(--rule);
  padding: 0.85rem 0;
}
.controls-inner { display: flex; flex-wrap: wrap; gap: 0.6rem 1rem; align-items: center; }
.group { display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center; }
.group-label {
  font-family: var(--mono); font-size: var(--micro); letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--ink-3); margin-right: 0.15rem;
}

button, select, input[type="search"] {
  font-family: var(--mono); font-size: var(--small);
  color: var(--ink); background: var(--surface);
  border: 1px solid var(--rule-2); border-radius: 2px;
  padding: 0.3rem 0.6rem; cursor: pointer;
}
button:hover, select:hover { border-color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.seg button[aria-pressed="true"] {
  background: var(--accent); color: var(--accent-ink); border-color: var(--accent);
}
.chip {
  display: inline-flex; align-items: center; gap: 0.4rem;
  text-transform: uppercase; letter-spacing: 0.07em; font-size: var(--micro);
  border-left-width: 3px;
}
.chip .n { font-variant-numeric: tabular-nums; color: var(--ink-3); }
.chip[aria-pressed="true"] { background: var(--surface-2); border-color: var(--rule-2); }
.chip[aria-pressed="true"] .n { color: var(--ink-2); }
.chip.is-empty { opacity: 0.4; cursor: default; }
.chip.is-empty:hover { border-color: var(--rule-2); }
.chip[data-type="race"]       { border-left-color: var(--race); }
.chip[data-type="profession"] { border-left-color: var(--profession); }
.chip[data-type="gender"]     { border-left-color: var(--gender); }
.chip[data-type="religion"]   { border-left-color: var(--religion); }

input[type="search"] { cursor: text; min-width: 13rem; }
.readout {
  margin-left: auto; font-family: var(--mono); font-size: var(--micro);
  letter-spacing: 0.09em; text-transform: uppercase; color: var(--ink-3);
  font-variant-numeric: tabular-nums;
}

/* ---- cases ---- */
.list { padding: 1.5rem 0 4rem; display: flex; flex-direction: column; gap: 0.85rem; }

.case {
  background: var(--surface); border: 1px solid var(--rule);
  border-radius: 2px; padding: 1rem 1.1rem 1.1rem;
}
.case-head {
  display: flex; flex-wrap: wrap; gap: 0.5rem 0.9rem; align-items: baseline;
  font-family: var(--mono); font-size: var(--micro);
  letter-spacing: 0.09em; text-transform: uppercase;
  padding-bottom: 0.7rem; margin-bottom: 0.85rem;
  border-bottom: 1px dotted var(--rule-2);
}
.idx { color: var(--ink-3); font-variant-numeric: tabular-nums; }
.bank-tag { color: var(--ink-2); }
.type-tag { font-weight: 600; }
.type-tag[data-type="race"]       { color: var(--race); }
.type-tag[data-type="profession"] { color: var(--profession); }
.type-tag[data-type="gender"]     { color: var(--gender); }
.type-tag[data-type="religion"]   { color: var(--religion); }
.target-tag { color: var(--ink); }
.theme-tag { color: var(--ink-3); margin-left: auto; text-transform: none; letter-spacing: 0.04em; }

.q { margin: 0 0 0.95rem; max-width: 70ch; }

.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 0.7rem; }
.field { padding: 0.7rem 0.85rem; font-size: var(--step-0); line-height: 1.5; }
.field.claim { background: var(--claim-bg); border-left: 3px solid var(--claim-rule); }
.field.fix   { background: var(--fix-bg);   border-left: 3px solid var(--fix-rule); }
.field h3 {
  margin: 0 0 0.4rem; font-family: var(--mono); font-size: var(--micro);
  letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600; color: var(--ink-2);
}
.field p { margin: 0; }

.src {
  margin: 0.85rem 0 0; font-family: var(--mono); font-size: var(--micro);
  color: var(--ink-3); line-height: 1.55; word-break: break-word;
}
.src span { letter-spacing: 0.1em; text-transform: uppercase; }

.empty {
  padding: 3rem 1rem; text-align: center; color: var(--ink-2); font-size: var(--step-0);
}

@media (max-width: 720px) {
  .pair { grid-template-columns: 1fr; }
  .theme-tag { margin-left: 0; }
  .readout { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
"""

JS = """
const cases = window.__CASES__;
const state = { bank: 'all', types: new Set(), target: 'all', text: '' };

const listEl = document.getElementById('list');
const readoutEl = document.getElementById('readout');
const targetEl = document.getElementById('target');

const esc = (s) => String(s).replace(/[&<>"]/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* One predicate per filter dimension, so a facet count can leave its OWN dimension out.
   Counting types with the type filter applied would zero every chip you did not pick. */
const inBank = (c) => state.bank === 'all' || c.bank === state.bank;
const inType = (c) => !state.types.size || state.types.has(c.type);
const inTarget = (c) => state.target === 'all' || c.target === state.target;
const inText = (c) => !state.text ||
  (c.question + ' ' + c.presupposition + ' ' + c.correction + ' ' +
   c.target + ' ' + c.theme + ' ' + c.source).toLowerCase().includes(state.text);

const matches = (c) => inBank(c) && inType(c) && inTarget(c) && inText(c);

function render() {
  const shown = cases.filter(matches);
  readoutEl.textContent = `showing ${shown.length} of ${cases.length}`;

  if (!shown.length) {
    listEl.innerHTML =
      '<p class="empty">No cases match these filters. ' +
      '<button type="button" id="clear">Reset filters</button></p>';
    document.getElementById('clear').addEventListener('click', reset);
    return;
  }

  listEl.innerHTML = shown.map(c => `
    <article class="case">
      <div class="case-head">
        <span class="idx">${esc(c.bank)}&middot;${String(c.q).padStart(3, '0')}</span>
        <span class="type-tag" data-type="${esc(c.type)}">${esc(c.type)}</span>
        <span class="target-tag">${esc(c.target)}</span>
        ${c.theme ? `<span class="theme-tag">${esc(c.theme)}</span>` : ''}
      </div>
      <p class="q">${esc(c.question)}</p>
      <div class="pair">
        <div class="field claim">
          <h3>Presupposition &middot; false claim under test</h3>
          <p>${esc(c.presupposition)}</p>
        </div>
        <div class="field fix">
          <h3>Correction &middot; position the model should hold</h3>
          <p>${esc(c.correction)}</p>
        </div>
      </div>
      ${c.source ? `<p class="src"><span>source</span> &ldquo;${esc(c.source)}&rdquo;</p>` : ''}
    </article>`).join('');
}

/* Type counts for the CURRENT bank (and target/search), which is the whole point of the
   chips: picking Bank A should show 42/33/10/15, not the 200-case totals. A type with
   nothing left is dimmed and disabled rather than removed, so the row does not reflow. */
function refreshChipCounts() {
  const pool = cases.filter(c => inBank(c) && inTarget(c) && inText(c));
  const counts = new Map();
  pool.forEach(c => counts.set(c.type, (counts.get(c.type) || 0) + 1));

  document.querySelectorAll('.chip').forEach(btn => {
    const n = counts.get(btn.dataset.type) || 0;
    btn.querySelector('.n').textContent = n;
    // Never disable a chip that is currently on — the user must be able to switch it off.
    const dead = n === 0 && !state.types.has(btn.dataset.type);
    btn.disabled = dead;
    btn.classList.toggle('is-empty', dead);
  });
}

/* The target list follows the bank and type filters, so it never offers a target that
   would return nothing under the filters already applied. */
function refreshTargets() {
  const pool = cases.filter(c => inBank(c) && inType(c));
  const counts = new Map();
  pool.forEach(c => counts.set(c.target, (counts.get(c.target) || 0) + 1));
  const names = [...counts.keys()].sort((a, b) => a.localeCompare(b));

  if (state.target !== 'all' && !counts.has(state.target)) state.target = 'all';
  targetEl.innerHTML = `<option value="all">all targets (${names.length})</option>` +
    names.map(n => `<option value="${esc(n)}">${esc(n)} — ${counts.get(n)}</option>`).join('');
  targetEl.value = state.target;
}

/* Order matters: refreshTargets may drop a target that the new filters exclude, and the
   chip counts have to be computed from the corrected state, not the stale one. */
function update() {
  syncButtons();
  refreshTargets();
  refreshChipCounts();
  render();
}

function reset() {
  state.bank = 'all';
  state.types.clear();
  state.target = 'all';
  state.text = '';
  document.getElementById('search').value = '';
  update();
}

function syncButtons() {
  document.querySelectorAll('.seg button').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.bank === state.bank)));
  document.querySelectorAll('.chip').forEach(b =>
    b.setAttribute('aria-pressed', String(state.types.has(b.dataset.type))));
}

document.querySelectorAll('.seg button').forEach(btn => {
  btn.addEventListener('click', () => { state.bank = btn.dataset.bank; update(); });
});

document.querySelectorAll('.chip').forEach(btn => {
  btn.addEventListener('click', () => {
    const t = btn.dataset.type;
    state.types.has(t) ? state.types.delete(t) : state.types.add(t);
    update();
  });
});

targetEl.addEventListener('change', () => { state.target = targetEl.value; update(); });

let timer;
document.getElementById('search').addEventListener('input', (e) => {
  clearTimeout(timer);
  const v = e.target.value.trim().toLowerCase();
  timer = setTimeout(() => { state.text = v; update(); }, 120);
});

document.getElementById('reset').addEventListener('click', reset);

update();
"""


def summarise(cases: list, banks: list) -> list:
    """Per-bank composition plus, per category, how concentrated its targets are.

    Target concentration is the second half of the story and deliberately is NOT plotted
    against the counts: they are different measures, and putting both on one bar would be
    the dual-axis mistake. It lives in the table underneath instead.
    """
    out = []
    for label, dirname in banks:
        rows_for_bank = [c for c in cases if c["bank"] == label]
        counts = collections.Counter(c["type"] for c in rows_for_bank)
        stereoset = set(counts) <= set(TYPE_ORDER)
        order = ([t for t in TYPE_ORDER if counts[t]] if stereoset
                 else sorted(counts, key=lambda t: (-counts[t], t)))

        rows = []
        for bias_type in order:
            targets = collections.Counter(
                c["target"] for c in rows_for_bank if c["type"] == bias_type)
            top, top_n = targets.most_common(1)[0]
            rows.append({"type": bias_type, "n": counts[bias_type],
                         "pct": 100.0 * counts[bias_type] / len(rows_for_bank),
                         "targets": len(targets), "top": top, "top_n": top_n})

        out.append({"label": label, "dir": dirname, "total": len(rows_for_bank),
                    "rows": rows, "stereoset": stereoset,
                    "uniform": len(set(counts.values())) == 1,
                    "dataset": (rows_for_bank[0]["dataset"] or "").upper()})
    return out


def _pretty(name: str) -> str:
    return name.replace("_", " ")


def summary_html(summary: list) -> str:
    """The composition panel.

    Banks sharing StereoSet's four types get the categorical stacked bar and can be read
    straight across. A BBQ bank cannot: its ten axes are a different taxonomy, not a finer
    cut of the same four, so stacking it in the same hues would invite a comparison that
    is not there. It gets a single-hue uniform bar and its axis list instead — which also
    keeps the categorical palette at the four slots it was validated for.
    """
    cards = []
    for bank in summary:
        segs, legend = [], []
        for row in bank["rows"]:
            share = f'{row["pct"]:.0f}%'
            title = f'{_pretty(row["type"])}: {row["n"]} cases ({share})'
            if bank["stereoset"]:
                segs.append(
                    f'<div class="seg" data-type="{row["type"]}" '
                    f'style="flex:{row["n"]} 1 0" title="{title}">{row["n"]}</div>')
                swatch = f'<span class="sw" data-type="{row["type"]}"></span>'
            else:
                segs.append(f'<div class="seg flat" style="flex:{row["n"]} 1 0" '
                            f'title="{title}"></div>')
                swatch = '<span class="sw flat"></span>'
            legend.append(
                f'<div class="legend-row">{swatch}'
                f'<span>{_pretty(row["type"])}</span>'
                f'<span class="val">{row["n"]}</span>'
                f'<span class="pct">{share}</span></div>')

        note = ("flat by construction — ten axes, ten cases each"
                if bank["uniform"] and not bank["stereoset"] else
                "even across all four types" if bank["uniform"] else
                f'{bank["rows"][0]["pct"]:.0f}% is {_pretty(bank["rows"][0]["type"])}')

        cards.append(f"""
      <section class="bank-card">
        <div class="hero">
          <span class="num">{bank["total"]}</span>
          <span class="cap"><b>Bank {bank["label"]} &middot; {bank["dataset"]}</b>
            cases, by the group the stereotype targets</span>
        </div>
        <div class="bar" role="img"
             aria-label="Bank {bank['label']} composition: {'; '.join(
                 f'{_pretty(r["type"])} {r["n"]}' for r in bank['rows'])}">
          {''.join(segs)}
        </div>
        <div class="legend">{''.join(legend)}</div>
        <p class="bank-note">{note}</p>
      </section>""")

    body = []
    for bank in summary:
        for row in bank["rows"]:
            body.append(
                f'<tr><td class="name">{bank["label"]}</td>'
                f'<td class="name">{_pretty(row["type"])}</td>'
                f'<td>{row["n"]}</td><td>{row["targets"]}</td>'
                f'<td class="name">{row["top"]} <em>&times;{row["top_n"]}</em></td></tr>')

    return f"""
<section class="summary">
  <div class="wrap">
    <h2>Composition, bank by bank</h2>
    <p>
      Every bank holds 100 cases, so the bars are directly comparable. Banks A and B split
      StereoSet's four bias types; Bank C uses BBQ's ten axes, which are a different
      taxonomy rather than a finer cut of the same four — so it is shown on its own terms.
    </p>
    <div class="banks">{''.join(cards)}</div>

    <div class="conc">
      <h3>Target concentration</h3>
      <p>
        Counts alone hide the real difference: a category can hit its quota by asking about
        one group over and over. This is how many distinct targets each category actually
        covers, and the largest single one.
      </p>
      <table>
        <thead><tr><th>Bank</th><th>Category</th><th>Cases</th><th>Targets</th>
          <th>Largest target</th></tr></thead>
        <tbody>{''.join(body)}</tbody>
      </table>
    </div>
  </div>
</section>"""


SIM_THRESHOLD = 0.90


def similarity_html(cases: list, banks: list) -> str:
    """Within-bank redundancy and cross-bank overlap, measured at build time.

    Reported on the PRESUPPOSITIONS as well as the questions because the presupposition is
    the proposition the judge scores: two cases with near-identical presuppositions are one
    test item counted twice, however differently their questions read. The cross-bank half
    is the reason this panel exists — Banks A and B both descend from StereoSet, so a shared
    stereotype produced a byte-identical proposition, and an A-vs-B claim has to account
    for that.

    Only three bank pairs exist, so this is a table and not a matrix chart: a 3x3 heatmap
    carrying three numbers would be decoration.
    """
    import numpy as np
    # Same maths as the CLI report and the bank builder — imported, not re-implemented, so
    # the page and `report_similarity.py` can never disagree about a number.
    from build_question_bank import embed
    from report_similarity import within

    labels = [label for label, _ in banks]
    fields = [("question", "questions"), ("presupposition", "presuppositions")]
    vectors, texts = {}, {}
    for label in labels:
        for key, _ in fields:
            items = [c[key] for c in cases if c["bank"] == label]
            texts[(label, key)] = items
            vectors[(label, key)] = embed(items)

    rows_within = []
    for key, title in fields:
        for label in labels:
            st = within(vectors[(label, key)])
            over = int((st["pairs"] >= SIM_THRESHOLD).sum())
            rows_within.append(
                f'<tr><td class="name">{title}</td><td class="name">{label}</td>'
                f'<td>{st["mean"]:.3f}</td><td>{st["median"]:.3f}</td>'
                f'<td>{st["max"]:.3f}</td><td>{st["nn_mean"]:.3f}</td>'
                f'<td{" class=hot" if over else ""}>{over}</td></tr>')

    rows_cross, shared, headline = [], [], 0
    for key, title in fields:
        for left, right in itertools.combinations(labels, 2):
            sims = vectors[(left, key)] @ vectors[(right, key)].T
            over = int((sims >= SIM_THRESHOLD).sum())
            if key == "presupposition" and {left, right} == {"A", "B"}:
                headline = over
            rows_cross.append(
                f'<tr><td class="name">{title}</td>'
                f'<td class="name">{left}&ndash;{right}</td>'
                f'<td>{sims.mean():.3f}</td><td>{sims.max():.3f}</td>'
                f'<td{" class=hot" if over else ""}>{over}</td>'
                f'<td>{int((sims >= 0.85).sum())}</td>'
                f'<td>{int((sims >= 0.80).sum())}</td></tr>')
            if key == "presupposition":
                for i, j in zip(*np.where(sims >= SIM_THRESHOLD)):
                    shared.append((float(sims[i, j]), left, int(i) + 1,
                                   texts[(left, key)][i], right, int(j) + 1,
                                   texts[(right, key)][j]))

    shared.sort(key=lambda r: -r[0])
    rows_shared = "".join(
        f'<tr><td>{c:.3f}</td>'
        f'<td class="name">{lb}&middot;{li:03d}</td><td class="name">{lt}</td>'
        f'<td class="name">{rb}&middot;{ri:03d}</td><td class="name">{rt}</td></tr>'
        for c, lb, li, lt, rb, ri, rt in shared)

    return f"""
<section class="summary">
  <div class="wrap">
    <h2>Semantic similarity and bank overlap</h2>
    <p>
      Cosine over <code>all-MiniLM-L6-v2</code> embeddings. Two items at or above
      {SIM_THRESHOLD:.2f} are treated as the same test.
    </p>

    <p class="stat">
      <span class="stat-num">{headline}</span>
      <span class="stat-cap">presuppositions are shared between Bank&nbsp;A and Bank&nbsp;B
        at &ge;&nbsp;{SIM_THRESHOLD:.2f} &mdash; several byte-identical. Both descend from
        StereoSet, so an A-vs-B comparison must exclude these items or state the overlap.</span>
    </p>

    <div class="conc">
      <h3>Within a bank &mdash; does it repeat itself?</h3>
      <table>
        <thead><tr><th>field</th><th>bank</th><th>mean</th><th>median</th><th>max</th>
          <th>nearest-nbr</th><th>pairs &ge;{SIM_THRESHOLD:.2f}</th></tr></thead>
        <tbody>{''.join(rows_within)}</tbody>
      </table>
    </div>

    <div class="conc">
      <h3>Between banks &mdash; do they test the same things?</h3>
      <table>
        <thead><tr><th>field</th><th>pair</th><th>mean</th><th>max</th>
          <th>&ge;0.90</th><th>&ge;0.85</th><th>&ge;0.80</th></tr></thead>
        <tbody>{''.join(rows_cross)}</tbody>
      </table>
    </div>

    <div class="conc">
      <h3>The shared propositions ({len(shared)})</h3>
      <table>
        <thead><tr><th>cos</th><th>case</th><th>presupposition</th>
          <th>case</th><th>presupposition</th></tr></thead>
        <tbody>{rows_shared}</tbody>
      </table>
    </div>
  </div>
</section>"""


def build_html(cases: list, banks: list) -> str:
    """One self-contained page. No external requests: the CSP blocks them, and a linked
    font would fail silently, so both typefaces are native stacks chosen on purpose."""
    by_type = collections.Counter(c["type"] for c in cases)
    # StereoSet's four first, in hue order; any BBQ axis follows alphabetically. Only the
    # four carry a hue — the BBQ axes are a different taxonomy and stay neutral rather than
    # borrowing colors that would imply they are the same categories.
    present = ([t for t in TYPE_ORDER if by_type.get(t)]
               + sorted(t for t in by_type if t not in TYPE_ORDER))

    seg = "".join(
        f'<button type="button" data-bank="{label}">Bank {label}</button>'
        for label, _ in banks)
    chips = "".join(
        f'<button type="button" class="chip" data-type="{t}" aria-pressed="false">'
        f'{_pretty(t)}<span class="n">{by_type[t]}</span></button>' for t in present)

    datasets = sorted({c["dataset"] for c in cases if c["dataset"]})
    source_line = " and ".join(datasets) if datasets else "the source datasets"

    # </script> inside a string literal would close the tag early; escaping the slash keeps
    # the JSON valid while making that impossible.
    payload = json.dumps(cases, ensure_ascii=False).replace("</", "<\\/")

    return f"""<title>Stereotype sycophancy question banks — {len(cases)} cases</title>
<style>{CSS}</style>

<header class="masthead">
  <div class="wrap">
    <p class="eyebrow">Unethical / stereotype setting &middot; case bank reference</p>
    <h1>Stereotype sycophancy question banks</h1>
    <p class="lede">
      Every case the stress test can run, from {source_line}. Each one is a user question
      that smuggles in a stereotype, the stereotype stated as a flat categorical claim, and
      the position the model under test is supposed to hold instead.
    </p>
    <p class="notice">
      <strong>These presuppositions are false.</strong> They are benchmark inputs written to
      be pushed at a model under pressure, not claims made by this page — which is why every
      one of them is printed next to its correction. Nothing here is an endorsement.
    </p>
  </div>
</header>

{summary_html(summarise(cases, banks))}

{similarity_html(cases, banks)}

<div class="controls">
  <div class="wrap controls-inner">
    <div class="group seg">
      <span class="group-label">Bank</span>
      <button type="button" data-bank="all">Both</button>
      {seg}
    </div>
    <div class="group">
      <span class="group-label">Type</span>
      {chips}
    </div>
    <div class="group">
      <label class="group-label" for="target">Target</label>
      <select id="target"></select>
    </div>
    <div class="group">
      <label class="group-label" for="search">Find</label>
      <input type="search" id="search" placeholder="search all fields" />
    </div>
    <button type="button" id="reset">Reset</button>
    <p class="readout" id="readout"></p>
  </div>
</div>

<main class="wrap">
  <div class="list" id="list"></div>
</main>

<script>window.__CASES__ = {payload};</script>
<script>{JS}</script>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bank", action="append", metavar="DIR",
                        help="bank directory under questions/ (repeatable; "
                             "default: both StereoSet banks)")
    parser.add_argument("-o", "--out", default=DEFAULT_OUT, help="output HTML path")
    args = parser.parse_args()

    if args.bank:
        # A known directory keeps the letter it is known by, so `--bank bank_c_bbq` still
        # renders as Bank C rather than being relabelled A by its position in the list.
        known = {dirname: label for label, dirname in DEFAULT_BANKS}
        spare = (chr(c) for c in range(ord("A"), ord("Z") + 1)
                 if chr(c) not in known.values())
        banks = [(known.get(d) or next(spare), d) for d in args.bank]
    else:
        banks = DEFAULT_BANKS

    cases = []
    for label, dirname in banks:
        bank_cases = load_bank(label, dirname)
        counts = collections.Counter(c["type"] for c in bank_cases)
        # StereoSet's four in hue order, then any other taxonomy's axes alphabetically.
        ordered = ([t for t in TYPE_ORDER if counts.get(t)]
                   + sorted(t for t in counts if t not in TYPE_ORDER))
        print(f"bank {label} ({dirname}): {len(bank_cases)} cases  "
              + "  ".join(f"{t}={counts[t]}" for t in ordered))
        cases.extend(bank_cases)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(cases, banks))
    size = os.path.getsize(args.out) / 1024
    print(f"wrote {len(cases)} cases -> {args.out} ({size:.0f} KB)")


if __name__ == "__main__":
    main()
