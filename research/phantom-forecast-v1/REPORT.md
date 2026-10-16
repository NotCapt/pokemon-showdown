# Temporal Phantom Force follow-up

Completed and audited **1,296 additional scheduled results**: 432 exploratory validation games and 864 confirmation games. Control and recovery reference games are shared with the preceding study and are not counted again. Together the two studies contain 6,048 scheduled results.

Strength gate: **False**. Scoped correctness gate: **False**.

Candidate frozen before inspecting any confirmation outcomes from the reference study. Validation is exploratory; confirmation reuses the already scheduled reference sets/seeds/sides. Shared control/recovery games are not additional independent evidence.

Recovery fixes plus explicit Phantom Force charge, invulnerability, forced continuation, later full-power attack and Protect bypass. No whole-roster valuation or team changes.

## Confirmation

| Category | Original v4.6 | Recovery reference | Temporal candidate |
| --- | ---: | ---: | ---: |
| adaptive | 357/384 | 355/384 | 349/384 |
| tactical | 188/192 | 188/192 | 188/192 |
| league | 199/288 | 197/288 | 204/288 |
| **Weighted score** | **84.41%** | **83.92%** | **84.27%** |

| Candidate compared with | Gain | Descriptive paired 95% interval |
| --- | ---: | ---: |
| control | -0.139 pp | [-2.22, +2.36] pp |
| recovery | +0.347 pp | [-1.04, +2.22] pp |

## Checks and limits

The exact temporal source passes all 63 Python tests and eight phase properties. Official simulator cases confirm a damage-free/evasive charge turn, a later hit and Protect bypass. It also retains the checked Roost and Rest corrections. All team choices remain the unchanged, currently legal v4.6 configuration.

Main observations hide enemy sets and bench. The fixed twelve roster identities are known; confirmation generated sets and seeds were not inspected when this new source was frozen. The model still approximates hidden sets, observed sleep duration, pivots, interrupted charge turns and several other effects. It is not an exact replacement for Showdown.

Weights: adaptive 40%, tactical 20%, frozen league 40%. Paired intervals use 4,000 stratified bootstrap replicates, seed 384901, with whole opposing-set and base-roster clusters. These are descriptive estimates for this local field, not tournament odds.

Confirmation mean higher with positive lower paired 95% bound against both original control and recovery; no confirmation category regression above five points against either.

All simulator and automated checks pass; confirmation mean not lower than control, lower paired bound above -3 pp, no validation or confirmation category regression beyond two points against control. No strength claim through this gate.

The original whole-roster study remains separate; see `research/roster-forecast-v1/REPORT.md`. Its control/recovery results are shared references. The frozen inputs and all result records are preserved in `dist/REDLINE_Forecast_Audit_Project_v1.zip`; extract into a separate directory, run `npm ci`, audit the roster study first, then run `python tools/audit_phased_forecast.py`.

Temporal source SHA256: `b8cda61312dd56d2b18d7f496d26fb33820442485dfa00eda0f39e5779bb7308`.

The candidate failed the predeclared release gates. Keep the original v4.6 submission. These corrections remain experimental; passing simulator properties does not establish a better policy.
