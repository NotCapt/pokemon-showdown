# Recovery and roster forecasting: frozen ablation protocol

Keep the exact v4.6 team and original release bytes as the control. Build four
policies before any new battle results: control, recovery fixes only, roster
forecast only, and combined recovery/roster changes. Recovery fixes model
successful Roost grounding until turn end, two blocked turns after modeled
Rest, and the failure of full-HP Rest. The combined forecast retains the
current Choice-lock, Sucker Punch, hazard, reserve-loss and preview-reset fixes.

The roster-only build is explanatory and cannot be promoted. Always evaluate
control, recovery and combined on both later phases; no candidate is selected,
retuned or replaced using development outcomes.

| Phase | Builds | Adaptive games each | Tactical games each | Frozen league each |
| --- | ---: | ---: | ---: | ---: |
| Development | 4 | 96 | 48 | 72 |
| Validation | 3 | 192 | 96 | 144 |
| Confirmation | 3 | 384 | 192 | 288 |

Total primary scheduled results: **4,752**. Weights remain adaptive 40%,
tactical 20%, league 40%. The twelve known rosters cover all 24 species;
all three cyclic leads are retained. The 504 generated builds and simulator
seeds are new and separate from earlier campaigns and from each other across
phases. Enemy bench and sets remain hidden. The adaptive reference knows its
own state but infers its opponent from public telemetry.

Use 4,000 paired stratified bootstrap replicates, seed 384901. Generated opposing
build pairs form clusters; complete frozen base rosters keep all leads, seeds
and sides together. These are descriptive intervals for this finite league.

Strength promotion requires combined to beat **both** control and recovery on
confirmation mean with positive lower paired 95% bounds. No validation or
confirmation category may regress more than five points against either.

The recovery-only build has a separate scoped correctness gate: all targeted
simulator properties and automated checks pass, confirmation mean is not
lower, its paired lower bound is above -3 points, and no validation/confirmation
category regresses more than two points against control. A release through
this gate must not claim a demonstrated strength gain.

If neither gate passes, preserve v4.6 and report the rejected experiments and
known modeling limitations. Any selected artifact needs a complete schedule
and source audit, final contract checks and an execution-mode check before
release. No portal upload or competition entry is performed by this campaign.
