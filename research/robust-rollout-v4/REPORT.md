# Targeted recovery-override study

**2,760 fresh games audited.** Includes 2,376 field games and 384 direct-match guard games. All policies use the same team and exact v4.7 reference. Sources, opponents, seeds, weights and gates were frozen before outcomes.

Validation-selected challenger: **recovery_guard**. Fixed gates recommend **control**.

| Phase | Policy | Wins / games | Weighted score | Adaptive | New-team v4.7 policy | Known league |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| validation | recovery_guard | 228/264 | 87.29% | 93.75% | 81.25% | 83.33% |
| validation | control | 226/264 | 86.74% | 93.75% | 81.25% | 80.56% |
| validation | recovery_cycle | 226/264 | 86.35% | 91.67% | 81.25% | 83.33% |
| confirmation | recovery_guard | 478/528 | 91.77% | 95.83% | 93.75% | 79.17% |
| confirmation | recovery_cycle | 477/528 | 91.63% | 95.83% | 93.75% | 78.47% |
| confirmation | control | 474/528 | 91.04% | 95.83% | 91.67% | 79.17% |

| Confirmation comparison versus v4.7 | Weighted gain | Descriptive paired 95% interval |
| --- | ---: | ---: |
| recovery_guard | +0.729 pp | [+0.00, +1.82] pp |
| recovery_cycle | +0.590 pp | [-0.28, +1.68] pp |

The validation-selected candidate improves 4 paired outcomes and regresses 0. A lower interval bound of exactly zero does not satisfy the predeclared strictly-positive strength gate; it must not be rounded into a release qualification.

## Direct guard games

| Matchup | Wins-losses-draws | Score |
| --- | ---: | ---: |
| selected-vs-v4_7 | 57-71-0 | 44.53% |
| selected-vs-v4_6 | 120-8-0 | 93.75% |
| control-vs-v4_6 | 115-13-0 | 89.84% |

| Matchup | Games reaching turn-limit adjudication | Losses among those games |
| --- | ---: | ---: |
| selected-vs-v4_7 | 35 | 18 |
| selected-vs-v4_6 | 12 | 4 |
| control-vs-v4_6 | 16 | 8 |

These counts describe the unchanged local harness cutoff at turn 101; they do not add games or alter the release gates.

Gates: `{"categories": true, "direct": false, "promote": false, "runtime": true, "strength": false}`. Only an eligible validation-selected challenger can be promoted; no post-hoc confirmation substitution.

## Decision policy

The core, priors and 96-rollout/six-turn UCB budget remain v4.7. Recovery guard uses the tactical choice when Monte Carlo alone proposes Rest above 65% HP or while the tactical baseline prefers a switch, or when a healing override replaces an attack whose low-roll default-model damage is at least 125% of the observed enemy HP. The latter is a pressure heuristic under unknown sets, not a guaranteed KO. Tactical recovery choices and other MC attack/setup/switch decisions remain available.

Recovery cycle adds a public-history veto for repeated MC switch overrides with the same own/replacement/opponent species within 12 turns when enemy HP has not fallen by more than two points and summed own HP has not risen by more than two. Vetoes fall back to the original tactical action. Preview resets this memory; productive cycling and baseline switches remain available.

Both exact candidates pass 63 Python tests and both JavaScript checks, deterministic/legal output and observation/static-data checks. Real historical observation streams verify avoidance of three earlier bad healing overrides while preserving a beneficial MC switch. Those counterfactual observation replays are development checks, not extra won battles or independent strength estimates.

## Earlier attempts and limitations

Broader corrected-model v1 was stopped for a last-PP forced Phantom Force forecast bug after 376 completed games, preserved and excluded. Corrected v2 passed the added regression property but failed validation in 792 games: guarded league 51/72 versus 55/72; aware adaptive 90/96 versus 94/96. Its scheduled continuation stopped for logical futility. Blanket-margin v3 scored 233/264 for both candidates versus 241/264 for control, failing adaptive and league guards. All 1,000 completed v3 records are preserved, including 208 subsequent records excluded from development selection/strength claims. Earlier early stops are transparently recorded protocol deviations; none earned promotion.

Those attempts informed development, not this trial's validation selection or held-out strength estimates. This policy retains v4.7's Roost/Rest, PP, hidden-bench and other transition approximations. The predicates are heuristics, not exact battle dynamics or an equilibrium solution. Better-looking internal forecasts did not automatically produce stronger tested policies.

## Controlled runtime

| Policy | Median | p95 | Maximum |
| --- | ---: | ---: | ---: |
| control | 25.48 ms | 132.23 ms | 242.28 ms |
| recovery_guard | 26.17 ms | 132.39 ms | 244.00 ms |
| recovery_cycle | 25.73 ms | 135.13 ms | 254.17 ms |

72 public synthetic positions, two interleaved repetitions after all battle/unit workers end; import/init/copy excluded; not strength evidence.

## Method and reproduction

Weights: adaptive 45%, new-team v4.7 policies 35%, familiar twelve-roster league 20%. 216 generated opposing builds and new actual simulator seed tags are disjoint from inspected earlier records/suites. New-team opponents use the v4.7 core compiled with fresh own configurations. All three cyclic leads are tested on the known league. Field policies share enemy sets, seeds and sides; observations hide enemy sets/bench and omit own boosts. Field intervals use 4,000 paired stratified whole-build/base-roster bootstrap samples, seed 384901. Direct schedules use different seed tags across roles; their percentages are unpaired empirical reference checks, despite the protocol calling the v4.6 reference matched. Their point-based gates are unchanged, and no paired direct improvement claim is made. See EVALUATION_NOTES.md. Scores concern this local conditional field, not tournament win odds.

On Windows, extract `dist/REDLINE_Recovery_Guard_Project_v4.zip` into a separate directory; run `npm ci`, `python tools/evaluate_recovery_guard.py --audit`, and `python tools/audit_robust_history.py`. Frozen manifests retain some Windows-native input paths; original audits require Windows. Exact sources, manifests, schedules and raw results, including excluded earlier attempts, are preserved.

**Retain v4.7.** No candidate earned promotion under these rules.

No practice upload or final competition entry was performed for this source.
