# Recovery fixes and whole-roster forecast: results

Completed and audited **4,752 scheduled games and 492 reports**. Selected by the predeclared rule: **control**. Strength gate: **False**. Scoped recovery-correctness gate: **False**.

All policies use the identical v4.6 Dragapult / Snorlax / Corviknight team. This campaign tests code changes, not a new team or trained neural weights. The original release is preserved byte-for-byte as control. No candidate was retuned using these outcomes.

## Confirmation

| Category | Original v4.6 | Recovery fixes | Recovery plus roster forecast |
| --- | ---: | ---: | ---: |
| adaptive | 357/384 | 355/384 | 351/384 |
| tactical | 188/192 | 188/192 | 186/192 |
| league | 199/288 | 197/288 | 192/288 |
| **Weighted score** | **84.41%** | **83.92%** | **82.60%** |

| Paired confirmation contrast | Gain | Descriptive 95% interval |
| --- | ---: | ---: |
| recovery-vs-control | -0.486 pp | [-1.67, +0.62] pp |
| combined-vs-control | -1.806 pp | [-3.61, -0.07] pp |
| combined-vs-recovery | -1.319 pp | [-2.99, +0.28] pp |

## What changed

- Recovery: successful Roost removes Flying typing until turn end; modeled Rest prevents attacks for the following two turns; full-HP Rest fails instead of creating sleep.
- Roster: evaluate the known own roster, restore the outgoing member's full move choices after switching, and simulate a legal own replacement after a predicted faint. Entry hazards, Choice locks, Sucker Punch execution, reserve-loss penalty and preview-memory reset remain.
- Combined contains both. Roster-only was tested on development for explanation and was not eligible for release.

The model still approximates unknown observed sleep duration, two-turn attacks, pivots, status effects and the hidden enemy bench. The recovery fixtures establish only the checked mechanics, not a complete exact simulator.

## Earlier phases

| Phase | Build | Wins / games | Weighted score |
| --- | --- | ---: | ---: |
| development | control | 191/216 | 86.39% |
| development | roster | 188/216 | 85.28% |
| development | recovery | 188/216 | 85.00% |
| development | combined | 184/216 | 83.06% |
| validation | control | 382/432 | 86.94% |
| validation | recovery | 374/432 | 84.86% |
| validation | combined | 372/432 | 84.72% |

## Checks and method

All four exact sources pass 63 Python checks. Both recovery builds pass official-simulator properties for Roost grounding/type restoration and Rest timing/failure. The original policy is the already audited v4.6 source. A historical exact-action fixture remains pinned to its original engine and team because changing Rest legitimately changes that old forecast ranking.

The rule and all sources, configurations, schedules and weights were frozen before this study. There are 504 fresh generated opposing builds, disjoint across phases and from the preceding campaigns, plus twelve known rosters covering all 24 allowed species and all three cyclic leads. Main observations hide enemy sets and reserves and supply sparse own boosts. Weights are adaptive 40%, tactical 20%, frozen league 40%.

4000 paired stratified bootstrap replicates, seed 384901. Whole opposing-set and base-roster clusters as in the earlier diverse-league method.

Combined must beat both control and recovery on confirmation mean with lower paired 95% intervals above zero. No validation/confirmation category may regress more than 5 pp against either reference.

Recovery-only candidate may be released as a scoped correctness fix if all simulator properties/checks pass, confirmation mean is not lower, lower paired interval is above -3 pp, and no validation/confirmation category regression exceeds 2 pp. Do not claim a demonstrated strength gain.

The audit verified every source/hash, exact opposing configuration, random seed, player side, outcome count, ranking, paired interval and gate. Completed reports contained zero illegal actions. These are conditional local-league estimates, not tournament win probabilities.

## Reproduction

The frozen inputs and all result records are preserved in `dist/REDLINE_Forecast_Audit_Project_v1.zip`. Extract into a separate directory, run `npm ci`, then `python tools/audit_roster_forecast.py` and `python tools/summarize_roster_forecast.py` to verify the existing results. `python tools/evaluate_roster_forecast.py --run --workers 6` resumes or, after removing only extracted job records, reruns the scheduled battles. Changing a frozen input is rejected. No fresh-instance execution diagnostic was run for these rejected candidates.
