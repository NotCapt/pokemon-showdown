# Interpretation and audit notes

The validation-selected recovery guard wins 478/528 confirmation games versus
474/528 for exact v4.7. There are four paired improvements and no paired
regressions. The weighted gain is +0.729 percentage points; its descriptive
paired 95% bootstrap interval is [0.00, +1.82] points. An interval touching
zero fails the predeclared strictly-positive strength gate. Neither the
threshold nor the source is changed after observing this result.

## Direct schedules use independent seed tags

The field comparisons match opponent sets, actual initial simulator seeds
and player sides across all three policies. Their uncertainty estimates
resample whole opposing-build clusters, and whole base-roster clusters for
the familiar league.

The frozen direct planner, however, allocates a different seed tag to every
role/job. Selected-versus-v4.6 and control-versus-v4.6 therefore use different
initial simulator seeds. The protocol's phrase "matched control" is not an
accurate description of seed matching here: the common factors are the
opponent release, team and native order, game count and balanced sides.
These direct percentages are unpaired empirical reference checks. No paired
direct confidence interval or paired direct improvement claim is justified.
The schedules and point-based gates remain unchanged; the field strength
gate already prevents promotion regardless of these direct outcomes.

## Scope

"Strong" opponents use the v4.7 decision core compiled with fresh own teams.
Their builds are new, but they are not new independently written policies.
The twelve base-roster league identities remain familiar. A local score is
not an estimate of tournament win probability.

Historical observation replays verify selected action changes under a forced
observation stream. They are development diagnostics, not new won battles.
The current candidate retains v4.7's recovery, finite-PP and hidden-bench
forecast approximations. No exact battle-model or equilibrium claim follows
from the guard.

A useful follow-up would freeze this exact recovery guard and compare it with
v4.7 on a larger independent new-team field. The current validation and
confirmation records would become development evidence for that study.
Any future direct comparison intended to be paired must explicitly share
actual simulator seed tags across the selected and control roles.

The frozen manifests retain some Windows-native input paths. Use Windows
for their original audit tools. ZIP member names are canonical forward-slash
paths; the data and standalone submission source remain readable elsewhere.
