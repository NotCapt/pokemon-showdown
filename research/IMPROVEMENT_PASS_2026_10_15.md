# Repository publication and expanded evaluation

The project was added to https://github.com/NotCapt/pokemon-showdown on `main`.
The recommended competition artifact remains v4.1: `dist/REDLINE_Search.zip`.
No competition entry was submitted. The release source, core, team and ZIP are
also preserved in `archive/v4_1`.

## New evaluation infrastructure

- `tools/opponents.js`: independent JavaScript policy using official Showdown
  damage calculations in a separate inferred battle. It can attack, switch,
  set up and heal. It knows its own exact set, HP, boosts, status and item, so its
  own information is richer than the lossy agent API. Enemy species, types and
  rounded HP are public; enemy item/ability/moves/stats are curated defaults.
  It receives no actual enemy bench. This is still a heuristic opponent, not a
  claim of strength against independent tournament entrants.
- `tests/opponents.test.js`: changing hidden enemy ability/item/moves/nature and
  reserve species leaves the decision unchanged; evaluating the policy also
  leaves the real battle state unchanged. This is a targeted invariance check,
  not a formal proof that every possible information leak is absent.
- `tools/make_eval_teams.py`: 24 development teams (seed 81283) and 24 holdout
  teams (seed 57991), each with three unique curated species, legal moves,
  abilities, items, natures and EV presets. These are diversified synthetic sets,
  not optimized opponent teams or a uniform sample of all legal configurations.
- `tools/run_eval.py`: clears inherited benchmark settings, enforces side pairs,
  and selects a fixed seed, team, source and policy explicitly.
- `tools/compare_reports.py`: verifies matched per-game seeds, opposing sets,
  sides and policies, and can verify source hashes. Confidence intervals resample
  whole opposing-team/set clusters, retaining dependence across repeated teams.
- `npm test` runs the 23 release Python tests and opponent invariance check.
  GitHub Actions and `tools/verify_release.py` verify the ZIP and manifest.

The new baseline does not dominate the old tactical baseline: on the development
custom suite, v4.1 won 80/96 against adaptive and 79/96 against tactical. Its value
is independent mechanics, richer own-state information and switching behavior.
Adaptive made 135 voluntary switches in the v4.1 development run.

## Experiments and selection

All counts below use actual Showdown battles, not the internal approximate model.
Every completed report records zero illegal actions. Tests deliberately omit own
boost telemetry; opponent sets are never passed to the submitted Python policy.

| Candidate | Mixed development /160 | Mixed holdout /200 | Adaptive development /96 | Adaptive holdout /192 | Original custom /60 | Stateless /40 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Recommended v4.1 | 125 | 151 | 80 | 151 | 59 | 31 |
| Dragapult lead, same sets/core | 136 | 175 | 83 | 162 | 37 | 31 |
| Status-memory correction | — | 147 | — | 151 | 59 | 31 |

Mixed seeds are 53047 and 61979. Adaptive seeds are 30931 and 44017. Original
custom seed is 42817, stateless seed 64513. Adaptive custom teams repeat four
games per development team and eight per holdout team; repeated games are not
independent team samples.

The Dragapult lead gained 12 percentage points on the mixed holdout, with a
team-cluster bootstrap 95% interval of +3.5 to +20.5 points. Its adaptive holdout
gain of 5.73 points has a much wider interval of -8.85 to +19.79 points. It
regressed heavily on the original six customized teams: 37/60 versus 59/60,
including 0/10 against the Choice Scarf Garchomp-led team. It was not promoted.
The generated candidate and team remain under `research/v5-pult-lead` and
`research/team-dragapult-lead.json`. The code is not a new recommended release.

Reserve preservation adds a heuristic value for a unique remaining answer to
observed opponents and a weak memory of departed opponents. It tied v4.1 at
48/60 on the default-set adaptive screen and 80/96 on development custom sets.
It was not promoted; source and generated candidate are under `v5-reserves*`.

Status memory retains an own Pokémon's last observed status when a later switch
observation omits it, respects explicit status/condition updates, and resets
between battles. Its two targeted tests pass. However, its mixed holdout fell
from 151/200 to 147/200: four regressed outcomes and no improved outcomes. The
heuristic policy needs retuning to benefit from that more accurate state. It was
not promoted. Source and generated agent are under `v4_2-status*`, and tests are
in `test_status_memory.py`. The label identifies an experiment, not a release.

An additional Dragapult-lead tactical-only holdout scored 162/200; no matched
v4.1 tactical-only control was run, so it is not evidence of improvement.

## Current conclusion

Keep v4.1 as the submission. The new results show that initial ordering and
hidden Choice Scarf sets materially affect outcomes, and that improving one
win-rate average can conceal severe matchup regressions. Further work should
address speed/item uncertainty and team-wide continuation value, then repeat
the expanded evaluations. Neither the current agent nor the evaluation policies
establish a probability of winning the competition.
