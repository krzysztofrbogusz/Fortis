Resuming the rule-induction work (see memory file rule-induction-m0.md for full state).

Context: we built M0–M3 of docs/rule_induction_plan.md — the supervised rule inducer at
src/fortis/induction/ (top-level package). Everything is UNCOMMITTED on main; 911 tests pass.
M0 = MDL objective + intervals + append fast path + scoreboard; M1 = greedy boosting loop;
M2 = class-targets + escape ladder + shrink + placement (58% of hand fit-reduction on the real
-100→750 interval); M3 = compose + induced_rules.toml round-trip + CLI (python -m
src.fortis.induction.main) + Phase-B refinement (global + localized).

We paused because the latin_to_french BENCHMARK needs cleanup before the inducer numbers mean
anything. I was going to manually clean the noisiest attested stages — -200 (hand 137/299,
mostly stress-placement conventions) and 750 (hand 78/299).

[Tell me here: did I finish the baseline cleanup? If yes, what changed — new hand-cascade
per-stage accuracy? If not, help me do it: run the analysis and give me the per-stage
"notation-noise vs real-error" report you offered, so I know what to fix.]

Once the baseline is clean, re-run the M3 measurement against it: - Experiment 2: full Phase-A induction (python -m src.fortis.induction.main --project
projects/latin_to_french) → composed final accuracy vs identity + hand baselines. - Then --refine-localized and compare. - Experiment 3: --ignore-stages ablation (never run — this is still TODO).

The KEY open finding to keep in mind: composed teacher-forced cascades collapse at the hard
-100→750 transition (composed goes -100:119/299 → 750:15/299 because over-broad induced rules
AMPLIFY upstream error). Localized Phase B (per-stage residual boosting) only nudged it (6→13/447).
The real fixes are likely (a) better-CONDITIONED candidates so rules don't over-apply, and
(b) inducing each interval from its composed-derived input, not just patching. Worth discussing
direction before more building.

Also still TODO from the plan: M4 (per-interval parallelism — full run is ~17min serial; pair
lookahead; beam) and M5 (--seed-rules, webapp tab). And: decide whether to commit M0–M3.
