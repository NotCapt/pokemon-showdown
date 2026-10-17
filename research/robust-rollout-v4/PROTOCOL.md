# Selective recovery-override study, version 4

Freeze all sources, preflight, team, suites, simulator seeds, schedules, weights
and rules before outcomes. Exact v4.7 control and unchanged team/mechanics,
priors, UCB allocation and 96-rollout/six-turn budget for both candidates.
Recovery guard falls back to the tactical choice when MC alone asks for Rest
above 65% HP or while the tactical baseline prefers a switch, or when a healing
override replaces an attack whose low-roll default-model damage exceeds 125%
of the observed opponent HP. That damage margin is a heuristic under unknown
sets, not a guaranteed KO. Baseline recovery choices are retained. Cycle adds
the same public unproductive-switch guard as v3: repeated own/replacement/foe
species tuple within 12 turns; foe HP decrease <=2 and own summed HP gain <=2.
All other MC attack/setup/switch overrides retain the original acceptance test.

Historical diagnostics and prior failed prototypes inform development only.
V1 was stopped for a technical last-PP forecast bug (376 games). Corrected v2
failed validation category guards (792 games). Blanket-margin v3 also failed
its validation guards; its 792 validation games and any subsequently completed
records remain excluded here. All retained inputs/results remain preserved.
V4 uses new opposing builds and simulator seed tags, with no retuning after
freeze. It retains v4.7's known recovery/PP/hidden-bench model approximations.

Validation per policy: adaptive 96, strong 96, known league 72. Confirmation:
adaptive 192, strong 192, known league 144. Total planned field games 2,376.
Weights: adaptive 45%, strong 35%, familiar twelve-roster league 20%. Select
only among challengers passing the validation category guards: no adaptive
or strong regression >2 pp and no league regression >5 pp. Rank eligible
challengers by weighted score, HP margin, prefer recovery_guard. If none are
eligible, stop for predeclared futility, audit the 792 validation games and
retain v4.7; no confirmation/promotion claim. Otherwise save selection before
confirmation. Other candidate confirmation results are explanatory only.

216 generated builds are fresh against inspected prior local suites/records.
Strong opponents use exact v4.7 core with new compiled own teams; league uses
all three cyclic leads. Same opponents, simulator seeds and sides across
policies; own boosts sparse and enemy sets/bench hidden. No random-action or
uniform weak-set ceiling games enter the main score.

Promotion: selected confirmation weighted gain >0 and lower paired 95% bound
>0; category guards must hold on validation and confirmation. Controlled
runtime median <2.5x control, p95 <4x control, max <1000ms; these are project
criteria, not organizer limits. All contract/property/hash/schedule/outcome
and packaging checks must pass. No post-hoc source selection or gate changes.

After confirmation: selected-v4.7, selected-v4.6, control-v4.6 each play 128
new direct games (384 extra; total planned 2,760). Selected score >=45% versus
v4.7 and no >10 pp point regression versus v4.6 relative to matched control.
Direct tests do not select/retune sources. Intervals use 4,000 paired stratified
whole-build/base-roster bootstrap samples, seed 384901. Local field estimates
are not tournament probabilities. No practice upload or final entry submission.
