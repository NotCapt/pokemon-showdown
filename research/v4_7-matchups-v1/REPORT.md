# Fresh v4.7 matchup results

**2,336 new local simulator games**, with sources, schedules, legal execution and native self-play symmetry verified. Exact archived releases; no policy or team changes. These are follow-up tests, not a new release-selection study.

| Matchup | v4.7 wins-losses-draws | Score | Games reaching turn 101 |
| --- | ---: | ---: | ---: |
| v4.7 versus v4.6, native team order | 240-16-0 | 93.75% | 28 |
| v4.7 versus v4.6, all 36 order pairings | 133-10-1 | 92.71% | 15 |
| v4.7 versus itself, native order | 64-64-0 | 50.00% | 36 |
| v4.7 versus itself, all 36 order pairings | 75-69-0 | 52.08% | 43 |

Native head-to-head descriptive paired-seed 95% interval: 90.62% to 96.48%. Side-swapped v4.6 self-play control: 64-64-0. Native self-play pairs must sum to one scored point; this passed for both releases. A roughly 50% self-play score measures symmetry and team-order effects, not strength against outside agents.

## Fresh random opponent builds

Each cohort contains 64 new legal three-Pokémon builds covering all 24 species. Coherent sets favor usable attacks, coverage and EVs; uniformly random sets can have poor synergy. Each build plays both sides under each of three fixed policies. Random actions choose legal moves and the first forced replacement; tactical uses the existing damage heuristic; adaptive models public enemy information and can switch voluntarily.

| Builds | Opponent policy | v4.6 W-L-D | v4.7 W-L-D | v4.7 score gain |
| --- | --- | ---: | ---: | ---: |
| coherent | random | 126-2-0 | 127-1-0 | +0.78 pp |
| coherent | tactical | 123-5-0 | 123-5-0 | +0.00 pp |
| coherent | adaptive | 117-11-0 | 115-13-0 | -1.56 pp |
| uniform | random | 126-2-0 | 128-0-0 | +1.56 pp |
| uniform | tactical | 126-2-0 | 126-2-0 | +0.00 pp |
| uniform | adaptive | 124-4-0 | 122-6-0 | -1.56 pp |

Across the equally weighted six cells (768 games per release), v4.6: **742-26-0**; v4.7: **741-27-0**. Paired gain **-0.130 pp**, descriptive 95% interval **[-1.69, +1.43] pp**. 9 outcomes improved and 10 regressed. Intervals cluster whole builds across all policies and both sides, stratified by cohort (10,000 replicates). Raw wins alone should not be mistaken for performance against well-built tournament teams.

## Team order diagnostics

D = Dragapult, S = Snorlax, C = Corviknight. Rows use v4.7; columns use the opponent. Each cell is wins-losses-draws in four games. Every order contains the same original legal configurations.

### v4.7 versus v4.6

| Own / foe | DSC | DCS | SDC | SCD | CDS | CSD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DSC | 4-0-0 | 4-0-0 | 4-0-0 | 4-0-0 | 3-0-1 | 4-0-0 |
| DCS | 4-0-0 | 4-0-0 | 4-0-0 | 4-0-0 | 4-0-0 | 4-0-0 |
| SDC | 3-1-0 | 4-0-0 | 4-0-0 | 3-1-0 | 4-0-0 | 4-0-0 |
| SCD | 4-0-0 | 3-1-0 | 3-1-0 | 4-0-0 | 4-0-0 | 4-0-0 |
| CDS | 4-0-0 | 4-0-0 | 4-0-0 | 4-0-0 | 3-1-0 | 4-0-0 |
| CSD | 2-2-0 | 2-2-0 | 3-1-0 | 4-0-0 | 4-0-0 | 4-0-0 |

### v4.7 versus v4.7

| Own / foe | DSC | DCS | SDC | SCD | CDS | CSD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DSC | 2-2-0 | 2-2-0 | 3-1-0 | 2-2-0 | 3-1-0 | 1-3-0 |
| DCS | 2-2-0 | 2-2-0 | 3-1-0 | 2-2-0 | 4-0-0 | 2-2-0 |
| SDC | 3-1-0 | 1-3-0 | 2-2-0 | 2-2-0 | 3-1-0 | 3-1-0 |
| SCD | 2-2-0 | 1-3-0 | 2-2-0 | 2-2-0 | 2-2-0 | 2-2-0 |
| CDS | 1-3-0 | 2-2-0 | 2-2-0 | 2-2-0 | 2-2-0 | 2-2-0 |
| CSD | 1-3-0 | 3-1-0 | 2-2-0 | 1-3-0 | 2-2-0 | 2-2-0 |

## Reproduction and limits

Pinned Showdown 0.11.11; Python 3.10; Node 24. Read PROTOCOL.md and plan.json for the frozen inputs and seeds. Reports contain the actual opponent configurations for audit; Python agents never receive them. Enemy bench/sets remain hidden and own boosts sparse. The benchmark adjudicates unfinished games by summed HP after turn 100. Native sources preserve the same Roost/Rest forecasting limitations documented in v4.7. Concurrent decision times are not a controlled latency benchmark. These scores and intervals describe this local test field, not tournament win probabilities.

Run `python tools/test_v4_7_matchups.py --audit` to recompute the report from frozen records, or `--run --workers 6` to resume missing jobs. Existing results require matching plan stamps. No practice upload or final competition entry was performed by this test.
