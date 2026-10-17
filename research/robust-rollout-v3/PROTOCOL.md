# Practical-margin rollout study, version 3

Freeze sources, preflight, teams, builds, simulator seeds, schedules, weights
and gates before outcomes. No retuning after freeze. Both candidates retain
exact v4.7 mechanics, priors, 96-sample UCB rollouts and team. Margin requires
at least five blended-score points before MC can override tactical search.
Cycle adds a veto for repeated MC switch overrides with the same own species,
replacement and opposing species within 12 turns, when foe HP has not fallen
by more than 2 points and total known own HP has not risen by more than 2.
The tactical fallback and existing legal-action/reserve guards remain intact.
These are heuristic practical thresholds, not statistical confidence claims.

Historical replays and the earlier corrected-model study are development
information only. V1 stopped for a forced-last-PP Phantom Force forecast bug
(376 games excluded). Corrected v2 failed its fixed validation category guards
in 792 games: guarded league -5.556 pp; aware adaptive -4.167 pp. It was stopped
for logical futility before any completed confirmation reports; no promotion.
Those models/records remain preserved. V3 does not incorporate the broader
mechanics/PP/public-reserve changes. It retains v4.7's known forecast limits.

Validation per policy: adaptive 96, strong 96, known league 72. Confirmation:
adaptive 192, strong 192, known league 144. Total 2,376 fresh field games across
control, margin and cycle. Select one challenger by validation weighted score,
HP margin, prefer margin on ties; save selection before confirmation. Only
that challenger is eligible. No post-hoc substitution from confirmation.

216 new generated legal builds and fresh simulator seed tags, disjoint from
inspected earlier local records/suites. Same opponents, seeds and sides across
policies. Strong opponents use exact v4.7 core with freshly compiled own sets.
Known league uses twelve familiar rosters and all three cyclic leads. Enemy
sets/bench hidden; own boosts sparse. Weights: adaptive 45%, strong 35%, known
league 20%. No random-action ceiling games enter the primary score.

Promotion requires positive selected confirmation weighted gain versus v4.7,
positive lower paired 95% bound, no validation/confirmation adaptive or strong
category regression >2 pp and no league regression >5 pp. Controlled preflight
runtime: median <2.5x control, p95 <4x control, max <1000 ms. All contract,
property, source/schedule/outcome and packaging checks must pass. Runtime gates
are project criteria, not organizer limits. The MC budget remains unchanged.

After confirmation: selected-v4.7, selected-v4.6 and control-v4.6 each play
128 new direct games (384 extra; total 2,760). Selected score must be >=45%
versus v4.7 and at most 10 pp below matched control versus v4.6. No tuning or
source substitution from direct games. Fixed gates failing means retain v4.7.

Intervals: 4,000 paired stratified whole opposing-build/base-roster bootstrap
replicates, seed 384901. Local conditional results are not tournament win odds.
No new practice upload or final competition entry in this experiment.
