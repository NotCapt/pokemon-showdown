# Robust rollout experiment, version 1

Freeze all source, model, checks, timing, team, opponents, seeds, schedules and
gates before new battle outcomes. Historical diagnostic replays are development
evidence only. No source changes or tuning after the manifest is frozen.

Three same-team policies: exact v4.7 control; guarded recovery/PP/public-sleep
memory, broader legal set priors, balanced 96-sample risk-aware Monte Carlo,
and capped summed-HP scoring; aware adds sampled availability of previously
seen possible enemy reserves and voluntary switching in both continuations.
Enemy reserves are hypotheses from public history, not actual hidden state.
Both choices precede reveal. Unknown unseen enemy species are not invented.

Validation: each policy plays adaptive 96, strong 96, known league 72 games.
Confirmation: adaptive 192, strong 192, known league 144 each. Total 2,376
scheduled field games. Select exactly one challenger by validation weighted
score, HP margin, then prefer guarded. Save selection before confirmation.
Only that challenger is eligible; other confirmation comparisons explain tradeoffs.

Adaptive opponents use their own true state and public enemy information.
Strong opponents use exact v4.7 policy with fresh compiled own sets/teams.
Known league: the earlier twelve frozen rosters, all three cyclic leads.
216 fresh generated builds and new simulator seed tags; same builds, seeds
and sides across candidates. Enemy sets/bench hidden and own boosts sparse.
Weights: adaptive 45%, strong 35%, known league 20%. Random-action and uniform
weak-set ceilings do not enter the primary score. Not an equal-CPU comparison.

Promotion: selected confirmation weighted gain versus v4.7 >0 and lower paired
95% bound >0; no validation/confirmation adaptive or strong category regression
over 2 pp, and no known-league regression over 5 pp. Runtime on frozen public
synthetic observations: median <2.5x control, p95 <4x control, max <1000ms.
These are project gates, not organizer-published limits. All properties,
historical unit tests, source/schedule/outcome audits and package checks must pass.

After confirmation, selected-v4.7, selected-v4.6 and control-v4.6 each play
128 fresh direct games (384 extra). Require selected score >=45% versus v4.7
and no >10 pp mean regression versus v4.6 compared with matched control.
No source selection or tuning from these direct tests; failing means retain v4.7.
Total including direct tests: 2,760 games.

Paired field intervals: 4,000 stratified whole opposing-build/base-roster bootstrap
replicates, seed 384901. The twelve league roster identities are familiar.
Keep all outcomes and regressions; no cherry-picking or hypothetical tournament
odds. No external practice upload or final competition submission in this study.
