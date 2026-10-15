# V4.1: opposing entry effects and Protean state

Recommended artifact: `dist/REDLINE_Search.zip`, also saved as
`dist/REDLINE_Search_v4_1.zip`. This is a small correctness update to v4, with
the same Dragonite / Dragapult / Arcanine team. It is not a solved battle agent.

## Included changes

- When a newly observed opponent has the assumed Intimidate ability, estimate
  the attack drop if own boost telemetry is absent. Do not reapply it on later
  observations of that same opponent. Explicit boosts take precedence. Existing
  Clear Body and Inner Focus immunity handling applies.
- Track Protean's once-per-switch type change in simulated continuations. Infer
  an already used type change from observed types differing from species types.
  Subsequent coverage attacks no longer all receive Protean STAB automatically.

Enemy abilities remain assumptions unless provided by the observation. This can
misread a custom Moxie Gyarados or Salamence. An opponent switching out and back
between observations cannot always be detected. Sparse boost reconstruction and
stateless execution remain approximate. The v3 stateless fallback is preserved.

## Matched actual Showdown battles

All tests use the pinned `pokemon-showdown@0.11.11` simulator, documented lossy
observations with own boosts removed, the same teams and seeds for both agents,
and side-reversed pairs. The mixed suite alternates power, STAB and fixed
tactical baselines over default-set teams from the curated roster. These are
simple opponents; these win rates are not estimates against the entrant field.

| Schedule | V4.1 | Archived v4 | Seed |
| --- | ---: | ---: | ---: |
| Mixed development, 160 games | 125 | 123 | 53047 |
| Mixed holdout, 200 games | 151 | 145 | 61979 |
| Six custom teams, 60 games | 59 | 59 | 42817 |
| Stateless tactical, 40 games | 31 | 31 | 64513 |

All 460 selected-agent games completed without illegal choices or worker
exceptions. All 23 release tests passed. Across suites, median decision time was
8.3–17.6 ms and p95 was 34.0–56.8 ms; concurrent processes affect timings.

On the holdout, six outcomes improved and none regressed. The +3 percentage
point difference has a paired bootstrap 95% interval of 0 to +7 points. On the
development schedule, three improved and one regressed; the +1.25 point interval
is -1.25 to +4.375. These intervals are descriptive and do not account for all
earlier candidate selection. This supports a modest update, not a claim of
statistical dominance or near-perfect play.

`tools/summarize_v4_1.py` verifies source hashes, team equality, exact per-game
seeds, sides, opposing sets and policies before producing `v4_1-summary.json`.
The source SHA256 is
`872624e2c86fb677b5aceeed825fca629156582a100116dca967bcccaded1ccf`.

## Portal verification

The authorized practice upload won in six turns, battle
`sim-1792076170722`. Its exact source hash and team are recorded in
`v4_1-portal-tested.json`; the response, replay and extracted battle log are
saved with the same prefix. Replay moves include Ice Spinner, Shadow Ball and
Flare Blitz, with no error/fallback strings found. A single smoke test cannot
prove absence of all service fallbacks. No competition entry was submitted.

## Damage and search experiments not selected

`tools/damage_oracle.js` generates 12,852 curated single-hit fixtures across 27
default/own configurations, using minimum and maximum damage rolls. Critical
hits are disabled. Because direct getDamage skips some action hooks, the harness
explicitly prepares first-attack Protean, Mold Breaker and absorption abilities.
`tools/validate_damage_oracle.js` cross-checks 329 sampled fixtures through full
move execution. All agree; charge moves and conditional Sucker Punch are outside
that execution cross-check. These are scoped damage tests, not a full simulator.

The experimental exact arithmetic model fixes Solar Beam in adverse weather,
Gyro Ball flooring, modifier ordering, Body Press with Choice Band, and rounding
of stats, base power, STAB, type effectiveness and final damage modifiers.
It matches every generated single-hit fixture within floating-point precision;
v4's mean absolute error was 1.178 HP, with two cases above 20 HP. This does not
cover arbitrary items, health states, boosts, weather, critical hits or multihit
transitions. The selected v4.1 release retains the old approximate arithmetic.

Experiments and results are preserved rather than replacing the release:

| Candidate | V1 / 100 | Custom / 60 | Other |
| --- | ---: | ---: | --- |
| Initial rounded model | 64 | — | 30/60 against v4, same team |
| Exact model plus ability state | 64 | 57 | 70/120 against v3 |
| Exact model plus all 16 damage rolls | 68 | 57 | Custom p95 228 ms |
| Historical v4 control | 69 | 59 | 70/120 against v3 |

The above saved-agent comparisons use their previously recorded matched seeds
41723, 42817 and 47933. The 16-roll search is substantially slower and does not
beat the control scores. Candidate source files and generated agents are under
`research/v5-*`; none is the recommended submission. The exact-model regression
suite is `research/test_mechanics.py`, separate from release tests.

Reproduce damage checks with:

```powershell
node tools/damage_oracle.js
node tools/validate_damage_oracle.js
python tools/check_damage.py --agent research/v5-mechanics/agent.py --out research/v5-mechanics-damage-errors.json
python -m unittest discover -s research -p test_mechanics.py
```
