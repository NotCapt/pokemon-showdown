# Diverse opponent league: frozen protocol

This follow-up addresses the large influence of one fixed incumbent in the
original team search. It uses the unchanged v4.5 decision engine and 25 legal
team configurations: all 19 builds from the preceding finalist comparison,
plus six balanced builds declared before this campaign's battles.

The schedule, compiled sources, suites and selection rules are frozen in
`research/diverse-league-v1/manifest.json`. The preflight audit passed before
execution. The source engine SHA256 is
`cead5d7101baaeb20509eaf16aa455108b3309102c6f50d25be9e02ce5e7dfc9`.

## Opponents and score

- 40%: an independent adaptive policy with fresh generated hidden sets.
- 20%: the tactical policy with separate fresh generated hidden sets.
- 40%: an equally weighted league of 12 frozen teams, each compiled with the
  same v4.5 engine and evaluated with all three cyclic lead choices.

The fixed league contains the incumbent, the earlier local challenger, the
cloud winner recompiled with v4.5, three other strong finalist configurations,
and six balanced configurations. Together they cover all 24 allowed species.
The incumbent is only one twelfth of the 40% league category: **3.33% of the
total score**. There is no weakest-category term in the ranking score.

Qualification, validation and confirmation use distinct generated team suites
and seeds. The 504 generated opposing configurations are disjoint across the
three phases and the two policies. Fixed roster compositions are deliberately
shared; their lead and random-seed results are new, but their identities are
known. No candidate receives hidden opposing set or bench information.

## Selection and confirmation

| Phase | Candidates | Adaptive games each | Tactical games each | Fixed league games each |
| --- | ---: | ---: | ---: | ---: |
| Qualification | 25 | 96 | 48 | 72 |
| Validation | 4 | 192 | 96 | 144 |
| Confirmation | 2 | 384 | 192 | 288 |

Total scheduled work is 8,856 actual Showdown games. The top three
non-incumbents and incumbent reach validation. Exactly one challenger selected
on validation meets the incumbent on the separate confirmation schedule.

Promotion requires a higher confirmation weighted mean, a positive lower paired
95% bootstrap interval, and no category regression exceeding five percentage
points. Otherwise retain the incumbent. Tied rankings use HP margin, then
incumbent preference. These rules were fixed before qualification results.

The interval uses 4,000 paired stratified bootstrap replicates, seed 384901.
Generated opposing-set pairs form clusters for adaptive and tactical play.
Complete base-roster groups keep all three lead orders and all seeds together
in the fixed league, avoiding an assumption that repeated games against one
team are independent. This is an experimental league estimate, not a
tournament win probability.

## Reproduction and artifacts

The completed campaign promoted v4.6; see [the audited results](V4_6_REPORT.md).
Extract `dist/REDLINE_Diverse_League_Project_v1.zip` into a separate Windows
directory to reproduce the original frozen inputs. The promoted working tree
has a new submission and team, so it cannot start the historical campaign.

Inside that extracted directory, `python tools/run_diverse_league.py --workers 6` runs or resumes the
campaign, checking input hashes before each phase. A changed input requires
another output directory and an explicitly updated protocol. No previous
results are overwritten.

The runner records an output-only adapter in `execution-adapter.json`. It
retries transient Windows file-lock errors while replacing progress or stamp
files. The original evaluation script, manifest, source hashes, schedules and
selection rules remain unchanged, and completed battle jobs are reused.

`python tools/audit_diverse_league.py --preflight` checks candidates, source
hashes, roster rotations, legal sets, disjoint generated suites and scoring
weights. After completion, run `python tools/audit_diverse_league.py` to audit
every schedule, source, ranking, paired comparison, selection gate and ZIP.

The final Kaggle version 5 was already downloaded and audited before this
campaign. Its v4.3.2 result remains separate in
`research/kaggle-results-v4_3_2/final`. Its selected team is included in the new
league using the v4.5 engine. See [previous results](KAGGLE_RESULTS.md).
