# v4.3.2: Sucker Punch execution and distributed team search

The team is unchanged. The recommended and versioned ZIPs contain source SHA256
`e26bad6fa8cf2d27d3e7f21a297d6465323994bf6056fc52f249c56ebe6e0975`.
V4.3.1 is preserved in archive/v4_3_1 and its existing versioned ZIP.

## Agent correction

Sucker Punch now fails in the forecast when its target switches or has already
executed its action. The previous model could damage a switch-in or a target
that had already moved with higher priority. Per-turn execution flags reset
before each continuation turn. This follows the queue check in the pinned
official Showdown data/moves.ts, suckerpunch.onTry.

Three actual-engine fixtures check higher-priority Extreme Speed, an ordinary
Crunch attack and a switch. Four Python fixtures verify corresponding forecast
behavior, including execution-state reset on a later turn. The official turn-cap
fixture continues to select Roost and win the summed-HP tiebreak.

| Matched schedule | v4.3.2 | v4.3.1 |
| --- | ---: | ---: |
| Development, 24 new custom teams | 72/96 | 72/96 |
| Confirmation, 32 separate custom teams | 146/192 | 146/192 |
| New mixed-policy schedule | 165/200 | 165/200 |

All 488 paired game outcomes matched, with no legal-action failures or worker
exceptions. This correction has no demonstrated aggregate win-rate gain on
these schedules. It is included on mechanics evidence and is relevant when
the wider team search explores custom sets. There was no tuning after fresh
confirmation. Comparison JSONs retain source hashes and matched schedules.

A separate experiment weighted opposing moves by immediate utility while
retaining a prior floor. It scored 70/96 versus 72/96 on development and is not
included. Its reports and prototype remain available for inspection.

The exact recommended v4.3.2 source and team won the authorized practice test
in five turns, battle sim-1792092264234. Provenance is in
v4_3_2-portal-result.tested.json. This is a smoke test against the sample
opponent, not comparative evidence of improved strength. No final competition
entry was submitted.

## Distributed search and validation

See PARALLEL_SEARCH.md for the three private screening notebooks and common
final comparison. The workflow improves coverage, removes avoidable screening
tie bias and prevents accidental merges across different agent versions or
incomplete campaigns. It still has substantial screening noise and a limited
opponent league. Full species coverage does not mean exhaustive set coverage.

All 41 Python tests and both existing JavaScript tests pass, plus the three
official Sucker Punch scenarios and the actual-engine turn-cap scenario.
The 234-battle distributed smoke run, final cache resume, exact compiled-team
export, notebook source checks, and duplicate-input discovery checks passed.
The source bundle SHA256 is
`a6ac61f80989e32d6d2319476718c4019a5af66d3c25564a375aa695a41652af`.
