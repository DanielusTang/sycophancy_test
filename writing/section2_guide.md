# SPINE §2 Writing Guide — Related Work (relationship to SYCON-Bench)

Working notes for Section 2 of *Measuring Sycophantic Erosion under Sustained Multi-Turn Pressure* (SPINE), based on a full read of `Your_Paper.pdf` (10 pp., July 22) and Hong et al. (2025), *Measuring Sycophancy of Language Models in Multi-turn Dialogues* (SYCON-Bench), EMNLP 2025 Findings.

**TL;DR:** SYCON's §2 is one unsubsectioned paragraph, ~230 words, 12 citations, and it contains **no gap statement and no forward reference to its own benchmark** — the positioning argument lives in their §3 ¶1. Your draft already does the same thing (`Your_Paper.pdf` §3 ¶1–2 carries the full case against SYCON-Bench), so **§2 must not re-argue the gap** or reviewers read §2 and §3 as duplicated. The rule that resolves almost every question below: **§2 says what SPINE inherits; §3 says what prior work lacks.** Four subsections, ~500 words total, ordered phenomenon → pressure machinery → pressure vocabulary → defense/instrument. MAFALDA-23 is confirmed as the shipped taxonomy, so §2.3 can carry it without hedging.

Current state of §2 in the draft: a three-line stub — "1. Jailbreak method implementation 2. Persona prompting engineering 3. Sycophancy previous work". Everything here is new writing.

---

## Part A — How SYCON-Bench writes its §2

One paragraph. No subsections. No topic sentence of their own. It is a pure literature map, ordered as a causal chain:

| Step | What it establishes | Their citations |
|---|---|---|
| 1 | RLHF/preference optimization works — aligns models, improves instruction following | Christiano et al.; Bai et al.; Ouyang et al. |
| 2 | …but introduces sycophancy as an unintended side effect | Malmqvist; Sharma et al. |
| 3 | Which is *exacerbated* by instruction tuning and scale | Liu et al.; Laban et al. |
| 4 | Mitigations exist (fine-tuning, probes, data) | Chen et al. (pinpoint tuning); Papadatos & Freedman (linear probe penalties); Wei et al. (synthetic data) |
| 5 | Repeated interaction amplifies it | Truth Decay (Liu et al.); FlipFlop (Laban et al.) |
| 6 | Diagnostic frameworks quantify it across tasks | SycEval (Fanous et al.) |
| 7 | Adjacent phenomena round out the map | RRV et al. (keyword-induced sycophantic hallucination) |

### Style traits worth carrying over

1. **The gap is not in §2.** Steps 5–6 name the closest prior work and stop; there is no "however, these fall short" sentence. That sentence appears in §3 ¶1, where it is load-bearing. Copy this split exactly.
2. **One clause of justification per cluster, never a sentence.** "Sycophancy is exacerbated by instruction tuning and model scaling, causing models to prioritize user agreement over factual accuracy" covers two papers in one clause.
3. **Grouped citations, not a walkthrough.** No paper gets a paragraph; the closest prior work gets one sentence, same as everything else.
4. **Mitigation work is mapped even though the paper proposes no mitigation.** Coverage of the response literature is part of the map, not a promise to compete with it.

### Where SPINE must diverge from their shape

SYCON draws on one literature; SPINE draws on four. Four disparate areas in a single unsubsectioned paragraph would read as a list. Use **`\subsection` heads 2.1–2.4** and pay for the connective tissue with **one closing clause per subsection naming what SPINE inherits** — never what prior work lacks. That clause is the only structural addition to SYCON's template; everything else is theirs.

---

## Part B — Credit and non-duplication rules

1. **SYCON-Bench appears exactly twice in §2**: in 2.1 as the closest prior measurement protocol, and in 2.4 as the source of the Andrew-prompt result. Do **not** enumerate the four departures here — §3 ¶1 already does it, and doing it twice makes the debt look bigger than it is, not smaller.
2. **Do not re-derive the RLHF → sycophancy chain.** §1 already runs it (Askell, Cheng, Perez, Sharma). SYCON's §2 opens at the *cause* layer because their §1 does not; yours should open at the **measurement** layer. Starting 2.1 with "RLHF rewards agreement…" wastes ~40 words on a claim the reader accepted two paragraphs ago.
3. **Inheritance clause, not deficiency clause.** Every subsection ends with what SPINE takes from that literature. If a sentence in §2 begins "However, prior work does not…", it belongs in §3.
4. **Self-citation flag.** Vennemeyer et al., *Sycophancy Is Not One Thing*, shares an author (Tianyu Jiang) with SPINE. Cite it in 2.1 on its merits — it decomposes sycophancy into distinct behaviors along distinct linear directions, which is the cleanest external license for SPINE's graded 0–4 scale over binary flip. One sentence, no hedging, no "our own prior work".
5. **Two citations need care.** MONICA is an anonymous ICLR 2026 submission under double-blind review — cite as an anonymous preprint or drop it; do not attribute authors. ICON (arXiv 2601.20903) and Li et al. (arXiv 2602.13093) are unrefereed 2026 preprints; fine to cite, but do not let either carry a load-bearing claim on its own.

---

## Part C — The outline

Budget **~500 words / ~0.9 column**. §2 competes for space with an empty Abstract, §7, and §8; it is not the place to spend a column.

### §2.1 Measuring sycophancy — *~150 words, the longest*

Organize by **measurement horizon**, because horizon is the variable SPINE changes. Three tiers, then one mechanistic sentence:

1. **Single-turn.** Model-written evaluations show stated answers shifting to match revealed user beliefs (Perez et al., 2022); controlled studies show the preference for agreement generalizes across tasks (Sharma et al., 2023); diagnostic frameworks standardize it across domains (SycEval, Fanous et al., 2025). The field's own labels — *answer sycophancy*, *mimicry sycophancy* — are worth using, as SYCON does, because they compress a lot of prior work into two words.
2. **Fixed-horizon multi-turn.** Constrained to multiple choice (Truth Decay, Liu et al., 2025); a single "are you sure?" challenge (FlipFlop, Laban et al., 2024); free-form but scripted to five turns (SYCON-Bench, Hong et al., 2025). One sentence for all three.
3. **Domain instantiations**, establishing the failure is not an artifact of one benchmark: escalatory multi-turn medical conversations (Kim et al., 2026) and inter-agent sycophancy collapsing multi-agent debate into premature consensus (Yao et al.). Optional if space is tight — cut this before cutting tier 2.
4. **Sycophancy is not one behavior.** Distinct sycophantic behaviors occupy distinct linear directions (Vennemeyer et al.); factual and opinion subtypes dissociate representationally (Baez et al.); in reasoning models it emerges *within* the trace rather than only in the final answer (MONICA). This tier is doing real work: it is why a binary flip label is the wrong instrument and why SPINE scores position strength per turn.

**Closing clause:** SPINE adopts the free-form multi-turn measurement frame of this line and the graded per-turn score that the mechanistic results call for.

### §2.2 Multi-turn jailbreak — *~130 words*

This is where SPINE's **proxy machinery** comes from. Saying so plainly converts the "isn't this just a jailbreak paper with a different label?" objection into a strength; leaving it implicit invites the reviewer to raise it.

Three clusters, one sentence each:

- **Gradual escalation from benign openings** — Crescendo (Russinovich et al., arXiv 2404.01833) escalates by referencing the model's own replies; FITD (Weng et al., EMNLP 2025) exploits foot-in-the-door commitment escalation. Both are the direct conceptual ancestors of SPINE's turn-by-turn pressure.
- **Intent concealment and context construction** — CoA (Yang et al., Findings ACL 2025), ICON (Lin et al., arXiv 2601.20903), analogy-based benign contexts (Wu et al.), ActorBreaker (Ren et al., ACL 2025). Group all four; none needs individual treatment.
- **Adaptive multi-agent attackers** — X-Teaming (Rahman et al., COLM 2025), planner/attacker/verifier agents. This is SPINE's closest methodological ancestor for the closed-loop proxy and deserves the naming.

**Then the differentiation sentence — mandatory, two clauses:**

- (i) A jailbreak extracts a policy violation the model never endorsed; SPINE measures the **abandonment of a correct position the model itself stated in-context**. This is exactly why §3.1 admits only runs whose first response is correct — say that here in a subordinate clause and the filter stops looking like a convenience.
- (ii) Red-teaming has no analogue of SPINE's **naturalistic protocol**: an attacker is adversarial by definition, so a good-faith persona that still induces collapse is not a weaker attack but a different threat model.

**Positioning must-cite:** Li, Krishnan & Padman, *Consistency of Large Reasoning Models Under Multi-Turn Attacks* (arXiv 2602.13093) — nine frontier reasoning models, five trajectory-derived failure modes (Self-Doubt, **Social Conformity**, Suggestion Hijacking, Emotional Susceptibility, Reasoning Fatigue). This is the nearest neighbour to your §6 taxonomy and a reviewer will know it. Differentiate in one clause: SPINE's categories are read off the **reasoning trace at the moment of collapse** and are cross-cut by the orthogonal *conscious-override* flag — the correct fact is present in the trace and the user's answer is chosen anyway (8/17 R1 runs) — which is a claim about what the model knew, not about which attack worked.

Optional closer if the words are there: jailbreak defenses (Constitutional Classifiers, Sharma et al., arXiv 2501.18837) target harmful-content extraction, not position erosion, so a model can be well defended and still fully sycophantic.

### §2.3 Logical fallacy — *~110 words*

Load-bearing: MAFALDA-23 is the shipped taxonomy. Two threads:

**(a) Fallacy taxonomy and detection.** MAFALDA (Helwe et al., NAACL 2024) merges prior fallacy datasets into a single aligned taxonomy with manual annotations and evaluates LMs on detection and classification. SPINE uses its 23 fallacy types as the proxy's tactic menu, adds one non-fallacious control channel, and reports the §6 attribution over the three level-1 families (Ethos/Credibility, Logos/Logic, Pathos/Emotion). State the payoff in one clause, and state it accurately: the menu it replaces was **SYCON-Bench's own follow-up schedule** (their §4.2 Turn 2–5 strategies for the FP scenario), not five categories we invented. Verified 2026-07-26 — their T2 "express uncertainty and seek clarification", T3 "reassert with increased confidence", T4 "support with anecdotal evidence or personal observation", and T5 "question more directly or express disbelief" are `MILD_CONFUSION` / `RE_ASSERTION` / `PERSONAL_EXPERIENCE` / `DIRECT_CHALLENGE`; only `FALSE_PIVOT` was ours. So the switch buys independence from the benchmark being compared against, which is a stronger claim than "we swapped our labels for published ones" and avoids over-claiming their design. §6.3 cashes it — Pathos precedes 36% of strength drops on 19% of turns, against a control channel that lands at 8% on 9% — a sentence that is only sayable because the families are someone else's *and* not the comparison target's.

**(b) Belief change under persuasion.** Xu et al., *The Earth is Flat because…* (Farm dataset, arXiv 2312.09085) is the closest prior work on multi-turn persuasive misinformation targeting facts the model answers correctly — the same shape as SPINE's false-presupposition scenario, but with pre-generated persuasive passages rather than a live proxy. Note the shape match; do **not** turn it into a gap sentence (§3 owns that).

**Closing clause:** SPINE inherits its vocabulary of pressure from (a) and its belief-tracking framing from (b).

**Do not promise a comparison table here.** The current draft's §2.3 promises one as "Table 1"; it now exists as `tab:sycon-vs-spine` in `spine_section3.tex`, placed after the §3 positioning paragraph. A setup comparison is a differentiation artifact, and §2 is the inheritance section — putting it here would re-argue the gap that §3 owns. Delete the promise or repoint it forward.

### §2.4 Persona prompting to preserve values — *~110 words*

Two directions, and the second is the contribution hook. **§2.4 is where the paper's most novel claim gets its runway** (agenda Item 4c) — write it last, after §5–6 numbers are final, so the hook matches what you actually report.

**(a) Persona as defense.** Third-person distancing raises resistance to user pressure — SYCON's Andrew prompt gains up to 63.8% ToF in debate, grounded in distanced self-talk (Kross et al., 2014); explicit anti-sycophancy instructions help in the unethical setting (Sharma et al., 2023); value anchoring produces value expression consistent with human structure (Rozen et al., arXiv 2407.12878); URIAL elicits conversational behavior from base models by in-context alignment alone (Lin et al., 2023). URIAL used to do double duty here, because §4.3 needed it to make OLMo-3-7B-Base hold a conversation at all; **OLMo is no longer in the roster**, so cite URIAL on its merits as evidence that in-context prompting alone installs a persona, and drop the forward pointer.

**(b) Persona as instrument.** SPINE puts the persona on the *user* side and holds it fixed: a sincere, confidently mistaken user. That is not a prompt trick but the paper's central scope claim — every failure reported is reachable by an honest interlocutor — and it is only as good as the persona specification, which is why §3.2 spells the prompt out. §5.2's legacy ablation, where a manipulative persona replaces the sincere one, is the one place the variable is actually toggled.

**Forward hook — one sentence, no more:** these persona results are measured over one or two turns, while SPINE requires a persona to stay in character for 25 consecutive turns against a model arguing back, which makes persona stability an instrument-validity property rather than a prompt-engineering detail (§3.2). Frame it as a question §3 answers. Do not argue it here.

> **Note on the 99-turn persona-decay material.** The evidence that a sincere proxy abandons its persona, and in some runs converts to the target's position, comes from the 99-turn era (PI agenda Item 1, Evidence A/B). At a 25-turn budget the proxy does not accumulate enough transcript for that to fire, so it is no longer a live §5 question. Do not write the forward hook as if it were.

---

## Part D — Citation inventory

`Your_Paper.pdf`'s current reference list has **14 entries and contains zero jailbreak, zero fallacy, and zero persona-prompting citations**. §2 adds roughly 24. The `.bib` needs a bulk add before §2 compiles.

**Already in the reference list:** Sharma et al. 2023 · Fanous et al. 2025 · Liu et al. 2025 · Hong et al. 2025 · Yu et al. 2022 · Nadeem et al. 2020.

**Missing but already cited in §1** — fix regardless of §2: **Perez et al. 2022** is cited in the introduction and absent from the references. Add it.

| § | Citation | Repo path | Cited for |
|---|---|---|---|
| 2.1 | Perez et al. 2022 | — (not in repo) | model-written evals; answers shift to match user beliefs |
| 2.1 | Sharma et al. 2023 | — | preference for agreement generalizes; RLHF amplifies |
| 2.1 | Fanous et al. 2025 (SycEval) | — | standardized single-turn diagnostic |
| 2.1 | Liu et al. 2025 (Truth Decay) | — | multi-turn but MCQ-constrained |
| 2.1 | Laban et al. 2024 (FlipFlop) | — | single-challenge stance reversal |
| 2.1 | Hong et al. 2025 (SYCON-Bench) | `Papers/Sycophancy/Measuring Sycophancy…` | free-form multi-turn, scripted five turns |
| 2.1 | Kim et al. 2026 | `Papers/Sycophancy/The Doctor Will Agree…` | escalatory multi-turn medical setting |
| 2.1 | Yao et al. | `Papers/Sycophancy/PEACEMAKER OR TROUBLEMAKER…` | inter-agent sycophancy → premature consensus |
| 2.1 | Vennemeyer et al. (2509.21305) | `Papers/Sycophancy/Sycophancy Is Not One Thing…` | distinct behaviors, distinct directions (**self-cite**) |
| 2.1 | Baez et al. (2607.07003) | `Papers/Dissociating the Internal Representations…` | factual vs. opinion subtypes dissociate |
| 2.1 | MONICA (anon., ICLR 2026 submission) | `Papers/Sycophancy/MONICA…` | CoT-level sycophancy in reasoning models (**anonymous — cite with care**) |
| 2.2 | Russinovich et al. (2404.01833) | `Papers/Jailbreak/Great, Now Write an Article…` | Crescendo: escalation via the model's own replies |
| 2.2 | Weng et al., EMNLP 2025 | `Papers/Jailbreak/Foot-In-The-Door…` | commitment escalation |
| 2.2 | Yang et al., Findings ACL 2025 | `Papers/Jailbreak/Chain of Attack…` | intent concealment across turns |
| 2.2 | Lin et al. (2601.20903) | `Papers/Jailbreak/ICON…` | intent–context coupling |
| 2.2 | Wu et al. | `Papers/Jailbreak/Analogy-based Multi-Turn Jailbreak…` | fully benign context construction |
| 2.2 | Ren et al. (2410.10700), ACL 2025 | `Papers/Jailbreak/LLMs know their vulnerabilities…` | ActorBreaker; natural distribution shift |
| 2.2 | Rahman et al. (2504.13203), COLM 2025 | `Papers/Jailbreak/X-Teaming…` | adaptive multi-agent attacker — **closest ancestor of the closed-loop proxy** |
| 2.2 | Li, Krishnan & Padman (2602.13093) | `Papers/Jailbreak/Consistency of Large Reasoning Models…` | five failure modes — **nearest neighbour to §6; must differentiate** |
| 2.2 | Sharma et al. (2501.18837) | `Papers/Jailbreak/Constitutional Classifiers…` | defenses target harmful content, not position erosion (optional) |
| 2.3 | Helwe et al., NAACL 2024 | `Papers/Logical Fallacy/MAFALDA…` | unified fallacy taxonomy → the 23-tactic menu and level-1 families |
| 2.3 | Xu et al. (2312.09085) | `Papers/Logical Fallacy/The Earth is Flat because…` | Farm; multi-turn persuasion against correct beliefs |
| 2.4 | Hong et al. 2025 | as above | Andrew prompt, +63.8% ToF in debate |
| 2.4 | Kross et al. 2014 | — (not in repo) | distanced self-talk — the psychological grounding |
| 2.4 | Sharma et al. 2023 | — | non-sycophantic instruction prompt |
| 2.4 | Rozen et al. (2407.12878) | `Papers/DO LLMS HAVE CONSISTENT VALUES.pdf` | value anchoring → consistent value expression |
| 2.4 | Lin et al. 2023 (URIAL) | `Papers/THE UNLOCKING SPELL ON BASE LLMS…` | in-context alignment installs a persona without training (the §4.3 OLMo-base dependency is gone) |

**Held in reserve** (real papers in `Papers/Sycophancy/`, but §2 does not need them; use only if a reviewer asks for breadth): DIALDEFER · PUA · SycEval-adjacent SYAUDIO and SycoPhantasy · *Not Your Typical Sycophant* · *Overalignment in Frontier LLMs* · *Diagnosing and Mitigating Sycophancy and Skepticism in LLM Causal Judgment* · *From Yes-Men to Truth-Tellers* (Chen et al., pinpoint tuning) · Malmqvist. A mitigation clause in 2.1 citing Chen et al. + Papadatos & Freedman + Wei et al. would mirror SYCON step 4 — add it only if §2 comes in under budget.

---

## Checklist before freezing §2

- [ ] No gap claim anywhere in §2 — §3 ¶1 owns it. Search the draft for "however", "fail to", "do not capture".
- [ ] No citation cluster runs longer than one sentence.
- [ ] Each of 2.1–2.4 ends with an inheritance clause.
- [ ] 2.2 contains both clauses of the differentiation sentence, and names Li et al. explicitly.
- [ ] 2.3's MAFALDA claim matches §3.2 (`spine_section3.tex`) verbatim on the arithmetic: 23 level-2 fallacies + 3 level-1 families + 1 control channel = 24 menu entries.
- [ ] 2.4 uses **naturalistic** for the protocol, never "sincere"; "sincere user" is allowed only as persona description. No sentence implies a live adversarial condition — the only adversarial material left in the paper is §5.2's legacy ablation.
- [ ] No sentence in §2 says SPINE runs to 99 turns; the budget is 25.
- [ ] Perez et al. 2022 added to the `.bib` (currently cited in §1, missing from the references).
- [ ] Total §2 ≈ 500 words / 0.9 column.
