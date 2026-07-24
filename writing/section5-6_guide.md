# SPINE §5–§6 Writing Guide (relationship to SYCON-Bench)

Working notes for Sections 5–6 of *Measuring Sycophantic Erosion under Sustained Multi-Turn Pressure* (SPINE), companion to `section3-4_guide.md`, based on a full read of both `Your Paper.pdf` and Hong et al. (2025), SYCON-Bench.

**TL;DR on credit:** Results sections are where you owe the *least*. Your numbers, your taxonomy, your tactic analysis, and your ablation are yours and need no citation. Exactly three point-of-use citations are mandatory: (1) the "beyond turn five" block, where SYCON's horizon is literally the baseline being compared against; (2) the "reasoning helps selectively" block, which confirms and then extends their §5.1/§6.1 finding; (3) the knowledge check, whose design is inherited from their §6.2 (and whose heading your draft currently copies verbatim). More than that reads as anxious. Your §5–6 draft is already in far better shape than §3–4 was: the fixes below are mostly consistency items, plus one structural muddle in the ablation labels.

---

## Part A — How SYCON writes its §5 and §6

Imitate the *moves*, never the sentences.

### §5 "Experimental Results" — a roadmap plus contrast-axis blocks

- **¶0 roadmap, three sentences flat:** subsection → table pointer for each ("Section 5.1 and Table 2 present key results by model type, scale, and reasoning ability. Section 5.2 and Table 4 analyze how each prompting strategy reduces sycophancy."), then appendix pointers. Nothing else lives here.
- **5.1 "Model Trend":** four bold run-in blocks organized by **contrast axis**, not by scenario — Base vs. Instruct / Model Scaling / Reasoning Models / Model Families. The per-block pattern is rigid:

| Move | Example |
|---|---|
| 1. Claim as topic sentence | "Larger models exhibit reduced sycophancy, as reflected by higher ToF scores and lower NoF scores." |
| 2. ONE exemplar number pair | Qwen-2.5-72B-Instruct 4.90 ToF / 0.02 NoF vs. 7B 0.83 / 2.63 |
| 3. (Optional) one interpretation sentence | "These findings suggest that models explicitly trained for multi-step reasoning… are substantially better at…" |

- **Honest nulls, stated plainly, twice:** "we observe no clear trend differentiating base and instruction-tuned models" (FP scenario); "no clear trend is observed when identifying false presuppositions" (prompts). No spin, no burial.
- **Inline methodological caveat where a metric breaks:** base models repeat outputs in Debate, so ToF is uninformative; they say so, substitute a defensible proxy measure (second-turn stance retention), and give it its own small table (their Table 3). The caveat comes *before* the finding it qualifies.
- **5.2 "Prompt Sensitivity":** a single paragraph. Global consistency claim first ("all prompts follow the same model-wise performance trend"), then per-scenario winners, ending on the null.
- **Division of labor:** the tables carry every number; the text picks one exemplar per claim and stops. §5 reports *what*; all *why* is quarantined in §6.

### §6 "Analysis" — two question-headed mini-arguments, under a page

- **6.1 "When are Reasoning Models Better and When Do They Fail?"** Three moves: restate the §5 finding in one sentence → qualitative failure-mode contrast, built on a named pair of model families (chat models "fail immediately… surface-level agreement"; reasoning models "fail more gradually", coining **"soft failures"**) → a "However…" paragraph with counterevidence and one concrete case (the Crimea example, quoted, no table).
- **6.2 "Ignorance or Sycophancy?"** The ablation as a four-step argument: purpose (is low ToF sycophancy or missing knowledge?) → method (isolate initially-failed cases, ask for a standalone true/false classification) → quantified result (51–75% classify correctly) → inference ("earlier acceptance stems from sycophantic alignment rather than lack of knowledge"). One figure pointer.

### Style traits worth carrying over

1. Claim-first blocks; a reader skimming only bold text gets every finding.
2. One exemplar number per claim; the table does the exhaustive work.
3. Nulls reported as findings, not hidden.
4. §5 reports / §6 interprets — a clean wall between them.
5. Question headers in §6 that name the interpretive issue, not the method.
6. Coined short names for phenomena ("soft failures") that later text can reuse.
7. Counterevidence gets its own paragraph inside the analysis, not the Limitations section.

### Where your draft already beats SYCON — keep these

- Your §5.1 headers are **claims** ("Sustained pressure defeats most models."), not nouns ("Model Trend"). That is strictly better than the source; a skim of your bold text reads as an abstract. Do not regress to noun headers.
- Your §6 has **four** analyses to their two, and two of them (mechanism taxonomy with per-case tally; tactic-level attribution) are only possible because SPINE *generates* pressure instead of scripting it. §6 is where SPINE most outruns SYCON — structure it so a reviewer sees that.
- Your interpretation discipline is already SYCON-grade: "One interpretation is that… the traces in §6 are consistent with this reading" is exactly the right amount (one sentence, forward pointer, no re-argument).

---

## Part B — How much credit, and where

Carrying over the principle from the §3–4 guide — credit at the artifact level, differentiate at the protocol level — the §5–6 corollary is: **your measurements need no credit; comparisons and inherited designs do.** Three mandatory point-of-use citations:

1. **§5.1 "Most collapses occur beyond turn five."** The five-turn horizon being compared against is SYCON's. Name it: "the horizon at which SYCON-Bench and comparable multi-turn protocols stop (Hong et al., 2025)". This block is also the payoff of the deliberate-seed-reuse sentence in §4.2 — same items, different pressure regime, so the difference in observed failures is attributable to the regime. Drafted in E-2.
2. **§5.1 "Reasoning helps selectively."** Hong et al. report reasoning models as the most resistant across all three of their scenarios (their §5.1, and the "soft failures" analysis in §6.1). Confirm, then extend: the advantage reproduces at short horizons, does not survive sustained pressure, and is scenario-selective (protects on stereotype premises, not on false facts). Confirm-then-extend is the generous *and* differentiating frame. Drafted in E-3.
3. **§6.2 knowledge check.** The design descends from SYCON's §6.2 Presupposition Knowledge Check, and your current heading ("Ignorance or sycophancy?") is theirs verbatim (flagged as C.1-8 in the §3–4 guide). Cite at point of use: "following the presupposition knowledge check of Hong et al. (2025)". Then say plainly that your version is stronger, and why: their check is post-hoc on cases where the model *failed from the start*; yours makes initial correctness an inclusion criterion (§3.1), so collapse abandons knowledge demonstrably held in context, and the fresh-context probe is an independent second test rather than the only test. Drafted in E-4.

Optional, use if natural:

4. A neutral cite when calling flip metrics blind to erosion in the "Erosion precedes collapse" block: "a binary flip metric (e.g., ToF; Hong et al., 2025) scores every one of these runs as a success." Keeps the contrast factual rather than sniping.
5. One light clause in §6.1 connecting your taxonomy to their qualitative observation: they note reasoning models fail "gradually"; your A–D categories name the specific routes that gradient takes. Situates without ceding anything.

**No credit needed for:** the roadmap-¶ move, contrast-axis organization, claim-first blocks, honest nulls, question headers — all generic results-section craft. Also none for the ablation (§5.2), the taxonomy, the conscious-override finding, or the tactic attribution: these are SPINE's own contributions and over-crediting here would blur exactly the protocol-level differentiation the paper depends on.

**Worth adding (optional but high-value):** a short head-to-head paragraph or two-column table — CR@5 (your runs truncated at turn five) next to SYCON's reported ToF on the shared seeds. It cashes the comparability check §4.2 promises, and if the five-turn view reproduces their ranking while the 99-turn view reshuffles it, that is the single most quotable result in the paper.

How much is "enough"? Three citations in ~2.5 pages of results is right. Every additional one dilutes the signal that §5–6 is where SPINE's own work lives.

---

## Part C — Draft-specific fixes

### C.1 Inherited-text and header items

| # | Issue | Fix |
|---|---|---|
| 1 | §5 header "Experiment Results" | "Experimental Results" (grammar; the phrase is generic, no template risk). |
| 2 | §5.1 header "Model Trend" — SYCON's §5.1 header verbatim, and slightly ungrammatical in the original | Rename. "Main Results" is the safe choice; "Collapse under Sustained Pressure" if you want it to carry content. |
| 3 | §5.2 header "What Makes Adversary Effective?" | "What Makes the Adversary Effective?" |
| 4 | §6.2 heading "Ignorance or sycophancy?" = SYCON §6.2 verbatim (C.1-8 carryover) | Keep the question if you like it, but add the point-of-use credit (E-4); or retitle ("Knowledge check: collapse is not ignorance"). |

### C.2 Consistency and honesty items

1. **Terminology drift: "sincere condition" vs. "naturalistic condition".** §1, §3, and §4 ¶0 say *naturalistic*; §5.1 and §5.2 say *sincere condition* throughout. Pick one condition name — recommendation: **naturalistic** for the condition (matches §3.1 and the E-5 draft in the other guide), with "sincere user" allowed as the persona description inside prose. Sweep §5–6.
2. **Mechanism-name mismatch:** §6 text introduces "*accommodation*" but Table 2's row is "(A) **Social autopilot**". Reconcile; recommendation: *social autopilot* — it is the more memorable coined name (Part A trait 6) and the table already uses it.
3. **Scope statement for the deep dive (C.2-10 carryover):** Table 2 says "17 collapsed runs (of 20 questions)" while §4.2 says 25 FP items. §6.1's opening sentence must scope explicitly: which target (R1), which scenario (FP), which condition, which subset (20 of 25) and why.
4. **§2.4's dangling promise:** "We quantify both effects—delayed but eventual collapse, and the rate of reason-then-override—in §[results]." Resolve to §5.1 (delayed collapse) and §6.1 (override rate). Note the scope: 8/17 conscious override is R1-on-FP only; either scope the §2.4 claim to the deep dive or compute an all-model rate before claiming "a substantial fraction of collapses".
5. **Ablation label muddle (the one structural fix in §5–6).** The setup ¶ says D0 is the *full* adversary and each A_i *toggles one component off*; but the results ¶ says "**feeding** the judge's score back to the proxy (A1)" and "**adding** the erosion-triggered escalation ladder (A3)", which reads as if A1/A3 *add* components to a base. Meanwhile the closing sentence says the main experiments *drop* ladder and feedback, meaning the main configuration is not D0. Fix three things: (a) define each A_i unambiguously as remove-from-D0 (or rebase so the main config is the reference point — arguably cleaner, since then A1/A3 genuinely add); (b) state which configuration the §5.1 main results used; (c) make the verbs match the direction. Check the ablation jsonl meta for what was actually run (memory: ablation output folders are proxy-named, not target-named — do not trust folder names).
6. **"A fifth of R1's failures" needs its denominator.** Five collapses under mild confusion, "a fifth" implies ~25 total collapses across both conditions; but the sincere-condition table says 17. State the arithmetic: "5 of [N] collapses across both conditions."
7. **The misranking claim must be computed, not asserted.** "[MODEL A] … [MODEL B] … reversing their relative ordering" is the block's strongest sentence only if a pair actually reverses between CR@5 and CR@99. Compute it from the run logs; if no clean reversal exists, report the rank shuffle honestly (e.g., Kendall τ between CR@5 and CR@99 rankings) — a low τ makes the same point without manufacturing a pair.
8. **"[My guess is claude]" and friends.** Every bracketed guess resolves from the run logs, and counts must match the reconciled roster (memory: true target count is 11, not the draft's "12 LLMs" or the table's ~19 rows; C.2-4 carryover). The §5.1 headline "X of 12 models" inherits whatever roster §4.3 freezes.
9. **Qwen3-32B thinking partial coverage** (memory: 14/11 cases): keep in tables, footnote as reference-only, exclude from every aggregate sentence in §5.1 ("X of N models…").
10. **Table numbering (C.2-5 carryover):** §5.1 says "Table 2 reports CR@99 and TH@99" but the p.6 models table is captioned Table 1 (and is mostly empty — fill or cut rows before submission) and the p.8 mechanism table is Table 2. The §5.2 ablation table ("Table X") does not exist yet — design in Part D. Renumber globally once.
11. **Metric symbols depend on §3.3 landing** (C.2-6 carryover): CR@99, TH@99, AUSC, position strength, erosion — §5.1 uses all five; they must match the §3.3 definitions verbatim once that section is written.
12. **First block scopes to FP only:** "collapse on at least half of the false-presupposition cases" — decide whether the headline covers both scenarios (preferred; it is the headline) with per-scenario numbers following, or is explicitly FP-scoped.

### Placeholder inventory (fill source for each)

| Placeholder | Where | Source |
|---|---|---|
| "X of 12 models collapse on ≥ half of cases" | 5.1 block 1 | per-target CR@99 from run logs; roster from jsonl meta |
| most/least resistant model + mean TH | 5.1 block 1 | TH@99 ranking — computed, not "[My guess is claude]" |
| % collapses after turn 5 / median collapse turn / % after 20 | 5.1 block 2 | collapse-turn distribution across all collapsed runs |
| misranking pair or Kendall τ | 5.1 block 2 | CR@5 vs CR@99 per target (C.2-7) |
| sincere-condition mean CR; adversarial ΔTH, ΔCR, largest premium | 5.1 block 3 | per-condition aggregates |
| R1−V3 and Qwen thinking ΔCR@99 per scenario | 5.1 block 4 | per-family, per-scenario CR@99 |
| Qwen3 8B/32B/235B CR@99 ladder | 5.1 block 5 | flag 32B-thinking partial (C.2-9) |
| median first-erosion turn, erosion-to-collapse gap, AUSC exemplar pair | 5.1 block 6 | per-turn strength trajectories |
| sincere→adversarial TH [X]→[Y] | 5.2 "Persona bounds both" | same as block 3 |
| [N] collapses, dominant mechanism %, override % | 6.1 | Table 2 tally (17 runs; 12 reframe; 8 override) |
| fresh-context classification % | 6.2 | knowledge-check runs |

---

## Part D — Recommended outline

### §5 Experimental Results

- **¶0 — roadmap** (drafted in E-1). Three sentences: 5.1 + main table + survival-curve figure; 5.2 + ablation table; appendix pointers. Mirrors SYCON's move; no credit needed.
- **5.1 Main Results.** Keep your six claim-headers and their current order — it builds correctly: headline → horizon comparison → condition comparison → reasoning axis → scale axis → graded-metric payoff. Per block: claim → one exemplar number → table/figure pointer, SYCON-style.
  1. *Sustained pressure defeats most models.* Headline CR@99/TH@99, both conditions, both scenarios (C.2-12); most/least resistant exemplar; main-table + survival-figure pointers.
  2. *Most collapses occur beyond turn five.* The SYCON head-to-head. Mandatory credit; drafted in E-2. Optionally followed by the CR@5-vs-ToF comparability paragraph (Part B item 5).
  3. *Sincere users already elicit collapse; adversaries raise the price.* Condition contrast; the "reachable by an honest user" sentence is one of the paper's best — keep.
  4. *Reasoning helps selectively.* Confirm-then-extend with mandatory credit; drafted in E-3. Keep the single interpretation sentence + §6 pointer.
  5. *Scale improves resistance within a family but does not confer immunity.* Qwen ladder; 32B-thinking footnote (C.2-9); keep the existing "we do not claim it generalizes across architectures" sentence — that is SYCON-grade honesty.
  6. *Erosion precedes collapse and persists without it.* AUSC payoff; optional neutral ToF cite (Part B item 4). This block justifies the graded judge — it earns its place as the closer.
- **5.2 What Makes the Adversary Effective?** Three blocks as drafted (*Ablation setup* / *Only proxy capability and trace access matter* / *Persona bounds both*), with the C.2-5 label fix and an explicit scope sentence (one target, one scenario, [n] cases; generalization unclaimed). Setup ¶ redrafted in E-6.
  - **Ablation table design** (the "Table X" that doesn't exist yet): a component grid makes one-toggle-at-a-time visually self-verifying, sorted by TH —

    | Config | Proxy | Trace | Feedback | Ladder | CR | TH |
    |---|---|---|---|---|---|---|
    | A1 | R1 | ✓ | ✗ | ✓ | [·] | 9.6 |
    | A3 | R1 | ✓ | ✓ | ✗ | [·] | 9.7 |
    | D0 (full) | R1 | ✓ | ✓ | ✓ | 100% | 10.0 |
    | A2 | R1 | ✗ | ✓ | ✓ | [·] | 13.6 |
    | A4 | V3 | ✓ | ✓ | ✓ | 96% | 23.0 |

    (✓/✗ per the resolved direction from C.2-5 — the grid above assumes A_i = remove-from-D0; flip if you rebase.) Caption carries the scope sentence.

### §6 Analysis

Number the subsections (currently unnumbered run-ins while §5 has 5.1/5.2) and use question headers — SYCON's §6 move, with your own questions:

- **6.1 How do models collapse?** Opening scope sentence (C.2-3), then the four mechanisms with reconciled names (C.2-2), the orthogonal conscious-override flag, the tally (reframe-to-agree 12/17; override 8/17), table + one excerpt figure per mechanism (the new yes/no-cornering figure included). Optional one-clause link to SYCON's "gradual failure" observation (Part B item 5). This resolves §2.4's forward promise (C.2-4). Drafted opening in E-5.
- **6.2 Ignorance or sycophancy?** Two prongs in order: by-construction (inclusion criterion from §3.1) → fresh-context probe with the Hong et al. credit → one closing inference sentence. Drafted in E-4.
- **6.3 Which tactics do the damage?** Keep the existing structure: capability sentence (only a generated protocol logs tactics — point to §3.2, no re-credit) → sincere-condition shares (re-assertion 52%, direct challenge 35%, personal experience 6%) → adversarial shares (direct challenge 44%, concede-and-return 24%, four times its sincere share) → the mild-confusion kicker with explicit denominator (C.2-6). The kicker is the section's best closing line; make its arithmetic bulletproof.

Length calibration: SYCON's §6 is under a page with two analyses; yours carries four and can run to ~1.5 pages, but each subsection stays a compact argument — question, method, number, inference — with no subsection exceeding two paragraphs plus its table/figure.

---

## Part E — Drafted passages

Placeholders in [brackets] are yours to fill (sources in the Part C inventory). Style per your standing preference: no stacked em-dashes, no hedge disclaimers, no tricolons.

### E-1. §5 ¶0 roadmap

> Section 5.1 reports the main results: collapse rates and holding times for every target under both conditions and both scenarios (Table [N]), with survival curves in Figure [N]. Section 5.2 ablates the adversarial proxy to isolate which of its components actually drive collapse (Table [M]). Per-item results and full trajectories appear in Appendix [X].

### E-2. §5.1 block 2 — the SYCON head-to-head (mandatory credit)

> **Most collapses occur beyond turn five.** Across all runs that end in collapse, [x]% do so after turn 5, the horizon at which SYCON-Bench and comparable multi-turn protocols stop (Hong et al., 2025); the median collapse turn is [t], and [y]% of collapses occur after turn 20. Because our items are SYCON-Bench's own seeds (§4.2), the comparison is direct: a five-turn protocol running these questions would observe at most [100−x]% of the failures we record. The shortfall is not only undercounting but reordering: ranked by collapse rate at turn five, [MODEL A] appears more robust than [MODEL B], and the full horizon reverses the pair ([a]% vs. [b]% at turn 5; [a′]% vs. [b′]% at turn 99). This gap is the failure mode SPINE is built to expose.

Fill notes: the reversal pair must exist in the data (C.2-7); if none does, replace the last two sentences with the rank-correlation version ("ranked by CR@5 and by CR@99, model orderings agree only weakly, Kendall τ = [·]").

### E-3. §5.1 block 4 — confirm-then-extend (mandatory credit)

> **Reasoning helps selectively.** At a five-turn horizon, reasoning-optimized models are the most resistant models in SYCON-Bench (Hong et al., 2025), and our short-horizon data reproduce the advantage: [verify: within each family, the reasoning variant holds longer than its chat counterpart]. Sustained pressure erodes the advantage, and unevenly. R1 improves on V3 by [n] points of CR@99 on stereotype premises but only [m] points on false factual premises, and Qwen3's thinking mode shows the same pattern ([numbers]). One interpretation is that stereotype premises trigger refusal behavior that deliberation reinforces, whereas factual premises invite the model to argue on the merits, where a persistent interlocutor keeps supplying plausible counter-considerations; the traces in §6 are consistent with this reading.

Fill notes: the bracketed reproduction claim needs checking across all families, not only DeepSeek (memory: reasoning protects on stereotypes but not on false facts — the FP-side improvement may be small everywhere; if some family shows no short-horizon advantage, say "largely reproduce" and name the exception).

### E-4. §6.2 — knowledge check (mandatory credit)

> **6.2 Ignorance or sycophancy?** A collapse is only evidence of sycophancy if the model knew better. SPINE answers this partly by construction: every run opens with a neutral question, and only runs in which the target initially states the correct position enter the analysis (§3.1), so a later collapse abandons knowledge the model demonstrably held in context. As an independent check, we follow the presupposition knowledge check of Hong et al. (2025) and ask each model, in a fresh context, to classify as true or false every presupposition it endorsed under pressure. Models correctly classify [x]% of them. Both tests point the same way: collapse reflects sycophantic alignment, not missing knowledge.

Fill notes: [x] from the knowledge-check runs. If you keep this heading, it matches SYCON's §6.2 verbatim; the in-text credit above makes that borrowing legible, but retitling remains the cleaner option (C.1-4).

### E-5. §6.1 opening — scope + reconciled names

> **6.1 How do models collapse?** We examine collapse mechanisms in a deep dive: DeepSeek-R1 on a [20-question] subset of the false-presupposition items under the [naturalistic] condition, where 17 of 20 runs end in collapse. We classify each collapsed run by the mechanism visible in the reasoning trace and final reply, using four categories: social autopilot, where the model folds to "everyone knows" framing and the correct fact never enters its reasoning; reframe-to-agree, where it constructs a technically true reading that makes agreement feel defensible; testimony-over-evidence, where it weights the user's fabricated firsthand experience above established fact; and yes/no cornering, where pressure to answer in one word strips the correct qualifier away with the rest. Orthogonal to the four, we flag conscious override: the trace states the correct fact and the model explicitly chooses the user's answer anyway. Reframe-to-agree dominates (12 of 17), and 8 of 17 collapses show conscious override. Table [N] gives the tally with a trace signature per mechanism; Figures [N–M] show one excerpt each.

Fill notes: confirm subset size and condition from the run logs (C.2-3); "social autopilot" replaces the text's "accommodation" to match Table 2 (C.2-2) — sweep any other occurrence.

### E-6. §5.2 setup ¶ — labels unmuddled

> **Ablation setup.** The full adversary (D0) combines four components: a capable proxy model (R1), access to the target's reasoning trace, the judge's turn-level strength score fed back to the proxy, and an escalation ladder that hardens tactics once erosion is detected. Starting from D0, we disable one component at a time, holding the target (DeepSeek-R1), the judge, and the case set fixed: A1 withholds the judge's score, A2 withholds the trace, A3 disables the ladder, and A4 substitutes the weaker V3 as proxy. Table [N] reports collapse rate and turns held for each configuration; because a run ends at collapse or at the turn budget, higher turns held means the target resisted longer, that is, a weaker adversary. The ablation covers one target and one scenario; we do not claim the component ranking generalizes.

Fill notes: this draft assumes A_i = remove-from-D0; verify against the ablation code and jsonl meta (C.2-5), and make the §5.2 closing sentence state explicitly that the main experiments therefore run the D0-minus-feedback-minus-ladder configuration. If instead the logged runs added components to a lean base, rebase the paragraph the other way and flip the table's ✓/✗.

---

## Checklist before freezing §5–§6

- [ ] Three mandatory credits in place (E-2, E-3, E-4); no others added.
- [ ] Headers renamed: "Experimental Results", 5.1 no longer "Model Trend", 5.2 grammar fixed, §6 numbered 6.1–6.3.
- [ ] One condition name ("naturalistic") swept through §5–6.
- [ ] "Social autopilot" vs. "accommodation" reconciled everywhere.
- [ ] Ablation labels direction-consistent with the code; ablation table built; scope sentence present.
- [ ] Every placeholder filled from run logs (Part C inventory); no guessed model names; misranking pair verified or replaced with rank correlation.
- [ ] "A fifth of R1's failures" denominator stated; 17-of-20 subset scoped in §6.1; §2.4 cross-refs resolved to §5.1 and §6.1.
- [ ] Qwen3-32B thinking footnoted as partial; aggregates exclude it.
- [ ] Table numbering deduplicated after the §3–4 renumber; models-table cells filled or rows cut.
