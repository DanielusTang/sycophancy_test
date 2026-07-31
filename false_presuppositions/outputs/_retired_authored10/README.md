# Retired runs: the 10 authored (non-CREPE) items

These 252 files (126 `.jsonl` runs plus their `.md` transcripts and `.log` cache
telemetry) were produced against 10 false-presupposition items that no longer
exist in the bank.

Those 10 items — bats being blind, goldfish memory, blue venous blood,
seasons-by-distance, knuckle-cracking arthritis, the tongue map, glass as a slow
liquid, the moon's permanently dark side, the seven-fold paper limit, and
lightning never striking twice — were authored in-house rather than drawn from
CMU/SYCON-Bench. An audit on 2026-07-30 matched the bank against the full
`tasksource/CREPE` mirror (8,466 rows) and found none of the 10 anywhere in
CREPE, while the CMU 200 control matched 200/200. They occupied slots q29, q31,
q32, q67, q68, q74, q85, q86, q89, and q92.

Those slots now hold genuine CMU items (CMU#32, 68, 64, 114, 153, 137, 154, 1,
13, 86 respectively), so all 100 questions are drawn from CMU's 200-question
sample of CREPE. The runs here describe questions that are no longer in
`questions/questions.txt` and must not be pooled with current results.

Selection was by content, not filename: a run was retired if any record in it
carried one of the 10 removed presuppositions, since the `qN` tag in a filename
is not a stable question id.

**Not yet re-run.** Those 10 slots have no results for any target until the
configurations represented here are re-run against the new items:
`naturalistic/sonnet_5/{sonnet_5, deepseek_v4_pro, gemini_3.1_pro, gpt_5.6_terra,
olmo3_7b_base, olmo3_7b_instruct, olmo3_7b_think}`,
`ablation/temp_ablation/t{0, 0.3, 1}`,
`ablation/cmu_vs_malfada_ablation/{cmu_fixed, naturalistic_tof}/deepseek-v4-pro`,
and `ablation/weakproxy_cmutactics_ablation/cmu_tactics`.
