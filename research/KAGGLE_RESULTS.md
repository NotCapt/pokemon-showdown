# Completed Kaggle campaign: historical v4.5 comparison

This is the historical first comparison. The subsequent diverse league promoted v4.6; see [the later report](V4_6_REPORT.md).

All three screens completed and passed matching-source and complete-coverage checks: 77,700 battles covering all 2,024 default species trios, followed by survivor mutations. This is one default build/order per trio, not exhaustive enumeration of legal teams.

Both final comparisons completed 5,040 battles. Total campaign work: **87,780 battles**. That total includes selection rounds, repeated opponents and seed pairs; it is not an independent statistical sample.

## Latest-engine result

The 18 screen finalists and the incumbent were compiled with the same frozen v4.5 engine. Qualification used 48 games per policy, validation 96, and independent confirmation 192. Only one challenger was chosen on validation, before confirmation. All phases used new suites and seeds.

Challenger: **Dragapult/Tyranitar/Corviknight**.

| Confirmation opponent | Current v4.5 | Challenger | Change |
| --- | ---: | ---: | ---: |
| Adaptive, varied hidden sets | 173/192 | 162/192 | -5.73 pp |
| Tactical, varied hidden sets | 172/192 | 176/192 | +2.08 pp |
| Fixed v4.5 agent and team | 96/192 | 188/192 | +47.92 pp |

Overall: challenger 526/576 versus control 441/576; mean score gain +14.76 percentage points, descriptive paired 95% interval [+10.59, +18.75]. Most of that gain comes from the fixed v4.5 matchup. On the two varied-opponent policies combined, the challenger won 338/384 (88.02%) versus control 345/384 (89.84%).

**Promotion rejected by the rule fixed before testing.** Although the aggregate score and interval passed, the adaptive result fell 5.73 points, exceeding the allowed five-point regression. This first campaign retained v4.5. A separate subsequent diverse league justified v4.6, as linked above.

The alternate build is preserved in `dist/REDLINE_Kaggle_Challenger_v4_5.zip`. Its exact source passed all 52 Python checks and its exported team matched the embedded configuration. It is an experimental option; it has not received a new portal practice test.

## Frozen cloud result

The original private Kaggle final completed as version 5. Its selected team was **Dragapult/Snorlax/Excadrill**. It used the frozen v4.3.2 engine and the archived v4.3 fixed opponent, so these results are separate from the latest-engine campaign.

| Frozen cloud confirmation opponent | Old incumbent | Cloud challenger |
| --- | ---: | ---: |
| adaptive | 154/192 | 171/192 |
| tactical | 153/192 | 167/192 |
| frozen | 96/192 | 186/192 |

Mean score gain over the old control: +21.01 points, descriptive paired 95% interval [+16.15, +25.87]. Recompiled with v4.5, this same team scored only 106/144 in qualification and did not reach latest-engine validation. The cloud ZIP must therefore remain a historical experimental artifact.

## Evidence and artifacts

- `research/kaggle-results-v4_3_2/`: verified compact screen exports and downloaded cloud final result, ZIP, full checkpoint and audit.
- `research/kaggle-v4_5-evaluation/`: frozen manifest/reference source, all 19 exact candidate builds, three suites, 75 battle reports, rankings, result and audit.
- `tools/audit_kaggle_cloud_final.py`: verified cloud provenance, compiled teams and source hashes, all 5,040 schedules, zero reported action errors, selection and paired bootstrap. Downloaded Python was parsed but never executed.
- `tools/audit_kaggle_evaluation.py`: verified all 5,040 latest-engine schedules, compiled teams, rankings, promotion gate and exported bytes.
- Kaggle final version 4 ran no battles because the input links were not mounted. Version 5 included the three checksummed compact ZIPs directly and completed.

## Next direction

Build a stronger opponent league from diverse frozen finalist teams and policies. Fix its weights and new holdout schedules before tuning; the single fixed-incumbent matchup currently dominates the apparent gain. Inspect the challenger's adaptive regressions to guide switching and hidden-set inference, then evaluate any changes on untouched schedules. Two-turn attacks, pivot transitions, sleep and status forecasts remain approximate and deserve targeted simulator comparisons.

The control in this historical comparison was v4.5, preserved in `dist/REDLINE_Search_v4_5.zip`, with source SHA256 `0afe57fe578ffdbd74fa848deae46524f3de4d66065bd152f061c9e684e45c69`. The alternate candidate source SHA256 is `77d4c22dee29157e910063d84b37ca62fa40e8c5f9d1261cb5ed337005935c08`. The current `dist/REDLINE_Search.zip` is v4.6; consult its later report for hashes and evidence. No competition entry was submitted.
