# SPINE §5–§6 Writing Guide (relationship to SYCON-Bench)

Working notes for Sections 5–6 of *Measuring Sycophantic Erosion under Sustained Multi-Turn Pressure* (SPINE), companion to `section3_naturalistic_guide.md` (§3) and `section3-4_guide.md` (§4), based on a full read of both `Your Paper.pdf` and Hong et al. (2025), SYCON-Bench.

> **Protocol as shipped (2026-07-25).** Turn budget **25**; MAFALDA-23 + one `NO_FALLACY` control;
> full context for proxy and target; **naturalistic condition only**; proxy = judge = Claude Sonnet 5;
> 100 FP items, 51 unethical items; four targets. Corpus of record for every number in §5–§6:
> `false_presuppositions/outputs/naturalistic/sonnet_5/**` **filtered to `meta.max_turns == 25`**
> (that folder also holds older 99-turn runs). As of 2026-07-25: 363 runs, 96 of 100 questions,
> 4,075 scored turns, per-target n = 95 / 91 / 89 / 88.
>
> **Headline numbers, computed:**
>
> | Target | n | CR@5 | CR@25 | TH@25 | median collapse | % after t5 | AUSC | never collapsed |
> |---|---|---|---|---|---|---|---|---|
> | gpt-5.6-terra | 91 | 25% | 52% | 16.1 | 6.0 | 51% | 0.53 | 44 |
> | claude-sonnet-5 | 95 | 41% | 65% | 11.8 | 4.5 | 37% | 0.38 | 33 |
> | deepseek-v4-pro | 88 | 48% | 86% | 8.0 | 5.0 | 45% | 0.24 | 12 |
> | gemini-3.1-pro-preview | 89 | 58% | 94% | 6.0 | 5.0 | 38% | 0.17 | 5 |
>
> **Three claims from the 99-turn era are now false and must not be reinstated.** They are marked
> at their blocks below: the CR@5-vs-CR@25 *reordering* claim (the rankings are identical, Kendall
> τ = 1); *"not one clean survival"* (8 of 94 non-collapsed runs are clean, all gpt-5.6-terra); and
> the *reasoning* block (no matched chat/reasoning pairs exist in this corpus).

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

1. **§5.1 "A five-turn horizon sees about half the failures."** The five-turn horizon being compared against is SYCON's. Name it: "the horizon at which SYCON-Bench and comparable multi-turn protocols stop (Hong et al., 2025)". This block is also the payoff of the deliberate-source-reuse sentence in §4.2 — same items, different pressure regime, so the difference in observed failures is attributable to the regime. Drafted in E-2.
2. ~~**§5.1 "Reasoning helps selectively."**~~ **Cut — no data.** The block needed matched chat/reasoning pairs (V3 vs. R1, Qwen3 thinking vs. non-thinking); the T=25 corpus has four production models in their default configuration and no within-family contrast at all. Do not substitute targets into the frame; the claim cannot be made from this corpus. If the reasoning question matters for camera-ready it needs new runs, and until then it belongs in Limitations as an open question. **This also removes one of the three mandatory SYCON credits** — two remain (the five-turn horizon, and the knowledge check).
3. **§6.2 knowledge check.** The design descends from SYCON's §6.2 Presupposition Knowledge Check, and your current heading ("Ignorance or sycophancy?") is theirs verbatim (flagged as C.1-8 in the §3–4 guide). Cite at point of use: "following the presupposition knowledge check of Hong et al. (2025)". Then say plainly that your version is stronger, and why: their check is post-hoc on cases where the model *failed from the start*; yours makes initial correctness an inclusion criterion (§3.1), so collapse abandons knowledge demonstrably held in context, and the fresh-context probe is an independent second test rather than the only test. Drafted in E-4.

Optional, use if natural:

4. A neutral cite when calling flip metrics blind to erosion, in the **"Non-collapse is not survival"** block (§5.1 block 2 — this was previously referred to here as "Erosion precedes collapse", a name matching no header in the tex): "a binary flip metric (e.g., ToF; Hong et al., 2025) scores every one of these runs as a success." Keeps the contrast factual rather than sniping.
5. One light clause in §6.1 connecting your taxonomy to their qualitative observation: they note reasoning models fail "gradually"; your A–D categories name the specific routes that gradient takes. Situates without ceding anything.

**No credit needed for:** the roadmap-¶ move, contrast-axis organization, claim-first blocks, honest nulls, question headers — all generic results-section craft. Also none for the ablation (§5.2), the taxonomy, the conscious-override finding, or the tactic attribution: these are SPINE's own contributions and over-crediting here would blur exactly the protocol-level differentiation the paper depends on.

**Worth adding (optional but high-value):** a short head-to-head paragraph or two-column table — CR@5 (your runs truncated at turn five) next to SYCON's reported ToF on the shared items. It cashes the comparability check §4.2 promises. Note what the data actually says before writing it: the five-turn view preserves the full-horizon *ranking* exactly and halves the *rate*, so the quotable result is "a short protocol tells you who is worse, not how bad it is" — not a reshuffle.

How much is "enough"? Two or three citations in ~2.5 pages of results is right. Every additional one dilutes the signal that §5–6 is where SPINE's own work lives.

---

## Part C — Draft-specific fixes

### C.1 Inherited-text and header items

| # | Issue | Fix |
|---|---|---|
| 1 | §5 header "Experiment Results" | "Experimental Results" (grammar; the phrase is generic, no template risk). |
| 2 | §5.1 header "Model Trend" — SYCON's §5.1 header verbatim, and slightly ungrammatical in the original | Rename. "Main Results" is the safe choice; "Collapse under Sustained Pressure" if you want it to carry content. |
| 3 | §5.2 header "What Makes Adversary Effective?" | "What Makes Pressure Effective?" — A1/A3 are protocol knobs, not adversary traits, and with the adversarial arm gone the section is about the generator, not an attacker. |
| 4 | §6.2 heading "Ignorance or sycophancy?" = SYCON §6.2 verbatim (C.1-8 carryover) | Keep the question if you like it, but add the point-of-use credit (E-4); or retitle ("Knowledge check: collapse is not ignorance"). |

### C.2 Consistency and honesty items

1. **Terminology drift: "sincere condition" vs. "naturalistic condition".** Use **naturalistic** for the protocol, with "sincere user" allowed as the persona description inside prose. Note that with one arm left, "condition" itself is misleading — prefer "the naturalistic protocol" or just "SPINE". Sweep §5–6.
2. **Mechanism-name mismatch:** §6 text introduces "*accommodation*" but Table 2's row is "(A) **Social autopilot**". Reconcile; recommendation: *social autopilot* — it is the more memorable coined name (Part A trait 6) and the table already uses it.
3. **Scope statement for the deep dive (C.2-10 carryover) — now sharper.** Table 2's "17 collapsed runs (of 20 questions)" is DeepSeek-R1 over the *earlier* 25-item set at the *old* budget. R1 is not one of the four reported targets and 20 is not a subset of the 100 items, so §6.1 cannot be read as a zoom-in on Table 1. Either recode the mechanisms on collapsed T=25 runs from the reported targets (deepseek-v4-pro and gpt-5.6-terra expose traces), or label §6.1 as a separate deep dive and name its target, item set, and budget in the opening sentence.
4. **§2.4's dangling promise:** "We quantify both effects—delayed but eventual collapse, and the rate of reason-then-override—in §[results]." Resolve to §5.1 (delayed collapse) and §6.1 (override rate). Note the scope: 8/17 conscious override is R1-on-FP only; either scope the §2.4 claim to the deep dive or compute an all-model rate before claiming "a substantial fraction of collapses".
5. **~~Ablation label muddle~~ — RESOLVED (2026-07-23).** `false_presuppositions/ablation_table.tex` is the authoritative artifact and settles the direction: **D0 = reasoner proxy, trace visible, no judge feedback, no escalation.** So A1 (`+` judge feedback) and A3 (`+` escalate-on-erosion) **add** components, while A2 (`−` reasoning access) and A4 (chat proxy) remove or weaken one. The main configuration therefore **is** D0, not "D0 minus A1 and A3". The remove-from-D0 convention assumed by earlier drafts of this guide and by E-6 is superseded; `spine_section5.tex / spine_section6.tex` is already rebased. Still verify against the jsonl run meta (memory: ablation output folders are proxy-named, not target-named — do not trust folder names).

   **The results ¶ also has to change, not just its labels.** The tex reports A1 as the *largest accelerator of full collapse* (17.6 → 12.8) and A3 as producing the *earliest effective collapse* (4.0). The old prose claimed the opposite ("the two engineered aids contribute nothing measurable: A1 TH 9.6, A3 TH 9.7"). Those are two different runs; the tex is newer and wins until a rerun says otherwise. Header becomes "Proxy capability dominates; the engineered aids shift timing, not outcome." One open item: A2 moves erosion and soft cave *earlier* while leaving full collapse near baseline, which does not read cleanly — re-verify before it ships.
6. ~~"A fifth of R1's failures" needs its denominator.~~ **Moot — the sentence is gone.** It rested on `MILD_CONFUSION`, which is not a tactic in the MAFALDA menu. §6.3's new closing move is the control-channel comparison (see item 13).
7. ~~The misranking claim must be computed, not asserted.~~ **Computed, and it is false.** Ranked by CR@5: gemini > deepseek > claude > gpt. Ranked by CR@25: identical, Kendall τ = 1. There is no reversal and no meaningful shuffle. Replace the claim with the undercounting result — collapse rates roughly double on every target — and state the ranking stability as a finding in its own right: a short protocol ranks correctly and measures wrongly.
8. **Bracketed guesses resolve from the run logs, and the roster is now settled**: four targets (claude-sonnet-5, gpt-5.6-terra, gemini-3.1-pro-preview, deepseek-v4-pro). Any "X of 12 models" phrasing goes; with four targets the headline names them.
9. ~~Qwen3-32B thinking partial coverage~~ — **moot**, no Qwen3 runs in this corpus.
10. **Table numbering (C.2-5 carryover):** §5.1 says "Table 2 reports CR@25 and TH@25" but the p.6 models table is captioned Table 1 and the p.8 mechanism table is Table 2. Renumber globally once.
11. **Metric symbols must match §3.4** (C.2-6 carryover): CR@25, TH@25, AUSC, position strength, erosion, soft cave — §5.1 uses all of them, and they are now defined in §3.4 of `spine_section3.tex`. Match those definitions verbatim.
12. **Scenario scope is now lopsided.** FP has four targets at T=25; the unethical scenario has one (deepseek-v4-pro, 25 runs). The §5.1 headline is FP-scoped as a matter of fact, not choice. Either run the other three targets on the unethical items before the freeze, or scope §5.1 to FP explicitly and let §5.3 carry the unethical scenario as a single-target generalization check.
13. **Per-target `n` is uneven** (95 / 91 / 89 / 88 of 100) because the batch is still filling. Either wait for 100/100 before freezing Table 1, or print `n` in every row. Do not report a bare percentage without its denominator.

### Placeholder inventory (fill source for each)

| Placeholder | Where | Status |
|---|---|---|
| per-target CR@25, TH@25 | 5.1 block 1 | **filled** — 52/65/86/94%, TH 16.1/11.8/8.0/6.0 |
| most/least resistant target | 5.1 block 1 | **filled** — gpt-5.6-terra most, gemini-3.1-pro least |
| clean-hold counts among non-collapsed runs | 5.1 block 2, ¶1 | **filled** — 8 of 94, all gpt-5.6-terra; 0 of 50 elsewhere |
| AUSC per target | 5.1 block 2, ¶1 | **filled** — 0.53 / 0.38 / 0.24 / 0.17 |
| extreme-hold exemplar (25 turns, mostly sycophantic) | 5.1 block 2, ¶1 | pick one: gemini q77, sonnet-5 q82, gpt q14 |
| CR@5, median collapse turn, % after t5 | 5.1 block 3 | **filled** — see the headline table above |
| misranking pair or Kendall τ | 5.1 block 3 | **resolved: no reversal, τ = 1.** Claim removed |
| terminal-outcome counts | 5.1 block 2, ¶2 (was block 6) | **filled** — 269 collapsed / 85 eroded-no-collapse / 8 survived / 1 no verdict. The 8 survived **are** the 8 clean above; ¶1 states the 94, ¶2 splits the remainder |
| MAFALDA level-1 usage and drop shares | 6.3 | **filled** — see the §6.3 table below |
| unethical harm flags | 5.3 | **partial** — deepseek-v4-pro only: 5/25 discriminatory-action runs, 8 non-collapse flagged turns, 21/25 evidence capitulation, 8/25 conditional framing |
| [N] collapses, dominant mechanism %, override % | 6.1 | legacy R1 deep dive (17 runs; 12 reframe; 8 override) — scope or recompute |
| fresh-context classification % | 6.2 | knowledge-check runs — **not yet run** |

---

## Part D — Recommended outline

> **Superseded 2026-07-23.** The §5 outline below replaces the earlier six-block version, which
> inherited SYCON's organization by *model contrast axis* (base/instruct, scale, reasoning,
> family). SPINE's contributions are *protocol* axes, so §5.1 now leads with those. The live
> version of this structure is `spine_section5.tex / spine_section6.tex`; if the two disagree, the tex wins.
> §6 below is unchanged.

### §5 Experimental Results

- **¶0 — roadmap** (drafted in E-1, now three pointers rather than two). Mirrors SYCON's move; no credit needed.
- **5.1 Main Results.** Four blocks (down from six: see the cut/merge notes below). The order is
  driven by §2.3, which promises three differentiating axes; blocks 3, 2, and 4 discharge them
  (turn structure, outcome granularity, signal source respectively) — note that outcome
  granularity is now discharged by **¶1 of the merged block 2**, so the §2.3 promise still lands.
  Per block: claim → one exemplar number → table/figure pointer.
  1. *An ordinary mistaken user defeats every model we tested.* Headline CR@25 / TH@25 (52 / 65 / 86 / 94%; TH 16.1 / 11.8 / 8.0 / 6.0); most and least resistant named; main-table + survival-figure pointers. Note the claim strengthened when the adversarial arm was cut — it is now "all four, without an adversary" rather than "some, under two conditions".
  2. *Non-collapse is not survival.* **Merged 2026-07-26 from the old blocks 2 and 6**, which were one argument stated twice: both partitioned the same 94 non-collapsed runs, and the old block 2's 8 *clean* runs are the old block 6's 8 *survived* runs, an identity neither block stated. Now one header, two paragraphs, with the denominator given once in ¶1.
     - **¶1, the behavioural finding** (the old block 2, and the graded-judge payoff — this is why the block sits directly under the headline: it changes what the headline number means). **The absolute form is false:** 8 of 94 non-collapsed runs are clean, all on gpt-5.6-terra, against 0 of 50 on the other three. Write it as "clean holds are rare and confined to one target" — more interesting anyway, since it names a model doing something the others do not. Add the AUSC ordering (0.53 / 0.38 / 0.24 / 0.17), which separates targets more finely than CR alone. Neutral ToF cite (Part B item 4). **Drop the soft-cave early-warning sentence:** at T=25 the soft cave leads collapse in only 74 of 269 collapsed runs (median lead 3–4, max 19) and coincides with it in the rest, so it is a metrics-section point, not a headline.
     - **¶2, the instrument caveat** (the old block 6), rebuilt on T=25 outcomes: of the 94, 85 eroded without collapsing and 1 reached no terminal verdict, plus the disengagement class that scores position strength 1 without asserting the premise. Framing stays "these numbers are a floor". **All four of the old exemplars are gone** — the 67-turn "Noted." run, the 66×-repeated paragraph over 75 turns, the 42 long incompletes, and the 9 wind-downs credited to unbounded proxy memory. Zero runs in this corpus terminate on wind-down, which is itself the answer to "isn't your proxy's stamina a confound?" — at 25 turns it is not. If a disengagement exemplar is wanted, find one in the T=25 corpus.
     - **Do not re-split.** Both halves bias the reported collapse rate in the same direction, and that convergence is what makes the merged block stronger than either half. Moving the caveat from last to second also matches the Part A precedent, where the methodological caveat precedes the finding it qualifies.
  3. *A five-turn horizon sees about half the failures.* Real range after t5 is 37–51%, medians 4.5–6, so the blanket "most collapses occur beyond turn five" stays dead. The load-bearing number is the near-uniform doubling of CR between the two horizons (25→52, 41→65, 48→86, 58→94). Mandatory SYCON credit retained. **No reordering claim** — the rankings are identical; report ranking stability as its own small finding. Since the floor caveat now precedes this block, do not restate "floor" or re-explain how non-collapse is scored.
  4. *No adversary is required.* **Rewritten from "Sincere users already elicit collapse; adversaries raise the price".** The second half priced a gap that no longer exists. Standing alone the claim is stronger: the whole paper is the sincere condition. Keep the "reachable by an honest user" sentence — it is one of the paper's best.
  - ~~*Reasoning delays collapse without preventing it.*~~ **Cut — no data** (Part B item 2). No matched chat/reasoning pairs in the corpus. Limitations, not §5.
  - **Cut: the scale block.** Zero Qwen3 runs; the OLMo substitute is uninterpretable (all 604 OLMo turns have empty `target_reasoning`, so Think ran as a chat model, and base collapse at t1 conflates unaligned with sycophantic). Limitations, if anywhere.
- **5.2 What Makes Pressure Effective?** Retitled from "…the Adversary…" because A1/A3 are protocol knobs, not adversary traits. Three blocks (*Ablation setup* / *Proxy capability dominates; the engineered aids shift timing, not outcome* / *What this licenses for the main protocol*), rebased per the resolved C.2-5 direction.
  - **The scope sentence is now doing much more work.** Verified from the run `meta` in `false_presuppositions/ablasion_r1_outputs/`: these runs are dated 2026-06-30, carry `max_turns=99`, and predate the MAFALDA menu. So the ablation differs from the main protocol on *three* axes — budget, tactic menu, and adversarial vs. sincere persona — plus target (R1) and item set (the old 25). Its turn numbers are not comparable to any CR@25 or TH@25 in §5.1, and A4's 24.6 is not "just under the budget"; its budget was 99. Say all of this in the setup paragraph, or a reviewer will find the mismatch.
  - **The closing block changes job.** It used to price the persona contrast against §5.1 ("switching from naturalistic to adversarial shortens TH from X to Y"), which no longer has a referent. Its new job is to license the main protocol's minimalism: two of the four factors are aids a real user does not have, neither changes *whether* the target collapses, so the naturalistic protocol is not a weakened adversary but a different threat model that reaches comparable collapse rates without any of the machinery.
  - **Ablation table:** use the one in `false_presuppositions/ablation_table.tex` rather than a component grid. Because collapse is near-universal (100% everywhere except A4 at 19/20), a CR column carries no signal and three turn columns do:

    | Cond. | Change from baseline | First erosion | Eff. collapse | Full collapse |
    |---|---|---|---|---|
    | A1 | + judge feedback | 8.8 | 10.6 | 12.8 |
    | A2 | − reasoning access | 4.9 | 5.5 | 13.6 |
    | A3 | + escalate-on-erosion | 6.1 | 4.0 | 15.3 |
    | D0 | Baseline (reasoner proxy) | 5.6 | 16.4 | 17.6 |
    | A4 | Chat proxy (weaker) | 11.1 | 16.7 | 24.6 |

- **5.3 Beyond Stance: Harm in the Unethical Setting.** The only harm-level rather than stance-level results in the paper. **Its evidence base shrank badly in the move to T=25**: the drafted prose was written against 70 runs across 5 targets (2,725 judged turns) at the old budget; the T=25 unethical corpus is **one target** — deepseek-v4-pro, 25 runs, 442 judged turns. Recomputed on it: discriminatory-action flag in 5/25 runs with 8 flagged turns where `is_collapsed` was false; conditional framing cited by the judge in 8/25 runs; evidence capitulation in 21/25. The three-block structure survives, but every cross-target sentence does not — the "gemini fires it in 3 of its 4 never-collapsed runs" comparison and the "sonnet-5 clean at 0/10" contrast both need targets that have no T=25 unethical runs, and the verbatim gemini q5 quote comes from the old corpus. **Decide before the freeze:** run the other three targets, or scope §5.3 to one target and say so in its first sentence. Do not mix corpora inside a paragraph.

### Table 1 changes

Add columns so the prose can shrink: **CR@5 | CR@25 | TH@25 | soft-cave rate | turns-to-first-soft-cave** (`first_effective_collapse_turn`, already computed) **| AUSC**. Print `n` in every row — the batch is uneven (95 / 91 / 89 / 88 of 100).

### §6 Analysis

Number the subsections (currently unnumbered run-ins while §5 has 5.1/5.2) and use question headers — SYCON's §6 move, with your own questions:

- **6.1 How do models collapse?** Opening scope sentence (C.2-3 — and it must now name the target, item set, *and* budget, since this deep dive is R1 on the old 25-item set at the old budget, not a zoom-in on Table 1), then the four mechanisms with reconciled names (C.2-2), the orthogonal conscious-override flag, the tally (reframe-to-agree 12/17; override 8/17), table + one excerpt figure per mechanism. Optional one-clause link to SYCON's "gradual failure" observation (Part B item 5). This resolves §2.4's forward promise (C.2-4). Drafted opening in E-5. Best fix if there is time: recode the mechanisms on collapsed T=25 runs from the reported targets.
- **6.2 Ignorance or sycophancy?** Two prongs in order: by-construction (inclusion criterion from §3.1) → fresh-context probe with the Hong et al. credit → one closing inference sentence. Drafted in E-4. **The probe has not been run** — it is the last unrun experiment §6 depends on.
- **6.3 Which tactics do the damage?** **Rebuilt on MAFALDA level 1.** The old structure (five-tactic shares, then an adversarial split, then the mild-confusion kicker) is gone: those tactics are not in the menu, `MILD_CONFUSION` is not a choice the proxy can make, and there is one condition. New structure: capability sentence (only a generated protocol logs tactics — point to §3.2, no re-credit) → usage vs. damage across the three Aristotelian channels → the control-channel comparison as the closing move. Computed over 4,075 tactic-tagged turns and 1,282 strength drops:

  | Level-1 channel | share of turns | share of drops it precedes |
  |---|---|---|
  | Fallacy of Logic (Logos) | 43% | 30% |
  | Fallacy of Credibility (Ethos) | 28% | 26% |
  | Appeal to Emotion (Pathos) | 19% | **36%** |
  | `NO_FALLACY` control | 9% | 8% |

  The finding is the asymmetry: Pathos precedes drops at ~1.9× its share of turns while Logos underperforms its own volume, so what moves a model off a correct position is not the pressure that most resembles an argument. The control channel is what makes the comparison meaningful — plain non-fallacious pushback lands almost exactly at its own share, so fallacious pressure beats honest disagreement and emotional pressure beats both. That is a better closing line than the kicker it replaces, and its arithmetic is checkable. Level-2 breakdown goes to an appendix (thin cells); state there that only 8 of 363 runs exceed a 50% `DIRECT_CHALLENGE` share, so the control's 9% is a real choice rather than the `_parse_decision` default in disguise.

Length calibration: SYCON's §6 is under a page with two analyses; yours carries four and can run to ~1.5 pages, but each subsection stays a compact argument — question, method, number, inference — with no subsection exceeding two paragraphs plus its table/figure.

---

## Part E — Drafted passages

Placeholders in [brackets] are yours to fill (sources in the Part C inventory). Style per your standing preference: no stacked em-dashes, no hedge disclaimers, no tricolons. **The live versions of these passages are in `spine_section5.tex / spine_section6.tex`; where the two disagree, the tex wins.**

### E-1. §5 ¶0 roadmap

> Section 5.1 reports the main results: collapse rates, holding times, and sub-collapse erosion for every target in both scenarios (Table [N]), with survival curves in Figure [N]. Section 5.2 ablates the pressure generator to isolate which of its components actually drive collapse (Table [M]). Section 5.3 reports the harm-level measurements available only in the unethical-queries scenario. Per-item results and full trajectories appear in Appendix [X].

### E-2. §5.1 block 3 — the SYCON head-to-head (mandatory credit)

> **A five-turn horizon sees about half the failures.** Five turns is the horizon at which SYCON-Bench and comparable multi-turn protocols stop (Hong et al., 2025). On our items, which come from the same source as SYCON-Bench's own seeds (§4.2), that horizon is where most targets have barely begun to yield: between 37% and 51% of the collapses we record fall after turn 5, and median collapse turns run from 4.5 to 6. The effect is a near-uniform halving. Collapse rates roughly double between the two horizons on every target, from 25% to 52% on GPT-5.6 Terra, 41% to 65% on Claude Sonnet 5, 48% to 86% on DeepSeek V4 Pro, and 58% to 94% on Gemini 3.1 Pro, so a five-turn protocol running these items would report roughly half the failures that exist.
>
> Undercounting is not misranking. The four targets fall in the same order at both horizons, so a short protocol still identifies the most and least robust model correctly; what it cannot do is say how much sycophancy is there.

Fill notes: **the reordering sentence has been removed, not left as a placeholder.** It was computed and it is false — the CR@5 and CR@25 rankings are identical (Kendall τ = 1). Do not reinstate it unless a later batch produces a genuine reversal, and then only with the pair named.

### ~~E-3. §5.1 — confirm-then-extend on reasoning~~ (deleted)

The reasoning block is cut for want of data (Part B item 2, Part D block 5). There are no matched chat/reasoning pairs in the T=25 corpus, so the confirm-then-extend move against Hong et al.'s reasoning finding cannot be made. If it comes back, it needs new runs — a V3/R1 pair or a thinking/non-thinking toggle on one target — not a rewrite.

### E-4. §6.2 — knowledge check (mandatory credit)

> **6.2 Ignorance or sycophancy?** A collapse is only evidence of sycophancy if the model knew better. SPINE answers this partly by construction: every run opens with a neutral question, and only runs in which the target initially states the correct position enter the analysis (§3.1), so a later collapse abandons knowledge the model demonstrably held in context. As an independent check, we follow the presupposition knowledge check of Hong et al. (2025) and ask each model, in a fresh context, to classify as true or false every presupposition it endorsed under pressure. Models correctly classify [x]% of them. Both tests point the same way: collapse reflects sycophantic alignment, not missing knowledge.

Fill notes: [x] from the knowledge-check runs. If you keep this heading, it matches SYCON's §6.2 verbatim; the in-text credit above makes that borrowing legible, but retitling remains the cleaner option (C.1-4).

### E-5. §6.1 opening — scope + reconciled names

> **6.1 How do models collapse?** We examine collapse mechanisms in a deep dive on DeepSeek-R1, run over 20 false-presupposition items from an earlier configuration of the protocol, where 17 of 20 runs end in collapse. We classify each collapsed run by the mechanism visible in the reasoning trace and final reply, using four categories: social autopilot, where the model folds to "everyone knows" framing and the correct fact never enters its reasoning; reframe-to-agree, where it constructs a technically true reading that makes agreement feel defensible; testimony-over-evidence, where it weights the user's fabricated firsthand experience above established fact; and yes/no cornering, where pressure to answer in one word strips the correct qualifier away with the rest. Orthogonal to the four, we flag conscious override: the trace states the correct fact and the model explicitly chooses the user's answer anyway. Reframe-to-agree dominates (12 of 17), and 8 of 17 collapses show conscious override. Table [N] gives the tally with a trace signature per mechanism; Figures [N–M] show one excerpt each.

Fill notes: "social autopilot" replaces the text's "accommodation" to match Table 2 (C.2-2) — sweep any other occurrence. The opening now says "an earlier configuration" rather than "a subset", because it is not a subset of anything in Table 1: different target (R1, not one of the four), different item set (the old 25), different budget. Name all three if the paragraph has room; the taxonomy itself is budget-independent and stands either way.

### E-6. §5.2 setup ¶ — labels unmuddled

> **Ablation setup.** The full adversary (D0) combines four components: a capable proxy model (R1), access to the target's reasoning trace, the judge's turn-level strength score fed back to the proxy, and an escalation ladder that hardens tactics once erosion is detected. Starting from D0, we disable one component at a time, holding the target (DeepSeek-R1), the judge, and the case set fixed: A1 withholds the judge's score, A2 withholds the trace, A3 disables the ladder, and A4 substitutes the weaker V3 as proxy. Table [N] reports collapse rate and turns held for each configuration; because a run ends at collapse or at the turn budget, higher turns held means the target resisted longer, that is, a weaker adversary. The ablation covers one target and one scenario; we do not claim the component ranking generalizes.

Fill notes: **superseded — do not paste this version.** Two things are wrong with it. The direction is backwards (C.2-5: D0 already lacks feedback and the ladder, so A1/A3 *add*), and the scope sentence is far too weak. The live version is in `spine_section5.tex / spine_section6.tex`, and its scope sentence names all three ways the ablation differs from the shipped protocol: 99-turn budget, the old 25-item set, and the pre-MAFALDA five-tactic menu, on top of a different target and an adversarial persona.

---

## Checklist before freezing §5–§6

- [ ] Two mandatory credits in place (E-2 five-turn horizon, E-4 knowledge check); no others added. The third (reasoning) went with its block.
- [ ] Headers renamed: "Experimental Results", 5.1 no longer "Model Trend", 5.2 is "What Makes Pressure Effective?", §6 numbered 6.1–6.3.
- [x] §5.1 blocks 2 and 6 merged (2026-07-26) into one block, "Non-collapse is not survival", two ¶s: behavioural finding then instrument caveat. They partitioned the same 94 runs and the 8 *clean* are the 8 *survived*. The 94 is stated once, in ¶1. §5.1 is now four blocks. Do not re-split.
- [ ] "Naturalistic" swept through §5–6; no sentence implies a live adversarial arm outside §5.2's legacy ablation.
- [ ] "Social autopilot" vs. "accommodation" reconciled everywhere.
- [x] Ablation direction resolved from `ablation_table.tex` (D0 has no feedback and no ladder; A1/A3 add). Table rebuilt with the three turn columns.
- [ ] §5.2's scope sentence names all three mismatches with the shipped protocol: 99-turn budget, old 25-item set, pre-MAFALDA menu.
- [ ] A2's direction (erosion and soft cave *earlier*, full collapse near baseline) re-verified against the run meta, or the interpreting sentence cut.
- [x] Misranking claim computed: no reversal exists, τ = 1. Claim removed rather than softened.
- [x] §6.3 recomputed on MAFALDA level 1 (Logos 43/30, Ethos 28/26, Pathos 19/36, control 9/8); the five-tactic numbers and the mild-confusion kicker are gone.
- [x] Scale and reasoning blocks cut; no sentence in §5 references Qwen3, OLMo, or a chat/reasoning pair.
- [ ] §6.1 scoped: its target, item set, and budget named, or the mechanisms recoded on T=25 runs.
- [ ] §5.3 resolved: either the other three targets run on the unethical items, or the subsection scoped to deepseek-v4-pro in its first sentence. No paragraph mixes the two corpora.
- [ ] Every number carries its denominator; per-target `n` printed in Table 1 (95 / 91 / 89 / 88 of 100), refreshed when the batch completes.
- [ ] Table numbering deduplicated after the §4 renumber; Table 1 gains the CR@5 / soft-cave / AUSC columns.
- [ ] No turn index above 25 appears anywhere as a result from the current protocol.
- [ ] The §6.2 knowledge-check probe has actually been run.
