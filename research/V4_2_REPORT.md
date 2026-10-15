# V4.2: correct the 100-turn objective and search horizon

Recommended artifact: `dist/REDLINE_Search.zip`, also saved as
`dist/REDLINE_Search_v4_2.zip`. Team and ordering remain Dragonite / Dragapult /
Arcanine. This is a small endgame correction to v4.1. It does not include the
earlier `v4_2-status` experiment or the newer `v6-*` research candidates.

## Included changes

V4.1 applied the normal HP-plus-KO valuation to its last-turn decisions and
simulated extra actions after turn 100. Both can disagree with the competition's
summed-HP tiebreak.

From turn 98, v4.2 evaluates the predicted change in summed HP percentages.
Untouched reserves cancel when comparing actions, so this is the active own
member's HP change minus the enemy's HP change. There is no extra reward for
KO count or survivors at the cap. The existing three-step model is clipped to
the remaining turns. A forced replacement is a free entry before that turn's
action; a replacement on turn 100 still gets to act on turn 100.

The model remains approximate: enemy switches, unknown enemy reserves, many
volatile effects, and continuation after a predicted own faint are not fully
modeled. This corrects the objective within the existing forecast, rather than
solving every possible endgame. Before turn 98, v4.1's policy is preserved.

## Actual simulator counterexample

`node tools/check_cap_scenario.js` constructs a legal curated endgame at turn
100, using Corviknight as the active own Pokémon rather than the recommended
three-Pokémon team. The fixture is a scoped policy test, not a tournament game.
Corviknight and Tyranitar are each at approximately 1% HP; own Dragonite is at
70%, enemy Arcanine is at 80%, and each side has one fainted member. The enemy
chooses Stone Edge. The agent sees the documented public fields only.

| Policy | Action | Own total HP | Enemy total HP | Tiebreak |
| --- | --- | ---: | ---: | --- |
| Archived v4.1 | Body Press | 77.219% | 79.948% | Loss |
| V4.2 | Roost | 99.969% | 87.126% | Win |

These are actual official Showdown 0.11.11 outcomes after the last turn, scored
using the documented cap rule. The fixture does not assert that Roost beats
every possible enemy move. Its source hashes and results are saved in
`research/cap-scenario.json`.

## Regression and portal evidence

| Matched schedule | V4.2 | V4.1 | Seed |
| --- | ---: | ---: | ---: |
| Mixed power/STAB/tactical, 200 games | 151 | 151 | 61979 |
| Independent switching policy, 192 games | 151 | 151 | 44017 |
| Original six custom teams, 60 games | 59 | 59 | 42817 |
| Stateless tactical, 40 games | 31 | 31 | 64513 |

All 492 selected-agent games completed without illegal actions or worker
exceptions. Each matched outcome and turn count equals v4.1. None reached turn
98, so these are regression checks, not evidence of greater ordinary-game win
rate. Medians were 35–37 ms, p95 101–114 ms under concurrent local load; these
are hardware/load-dependent timings, not a service guarantee.

All 27 release Python tests and the JavaScript opponent isolation test pass.
The new tests cover HP versus KO valuation, clipping the horizon, a forced entry
at turn 100, and exact action agreement with v4.1 over 36 generated pre-cap
states. `tools/summarize_v4_2.py` verifies hashes and matched schedules before
writing `v4_2-summary.json`.

The authorized practice upload won in six turns, battle
`sim-1792080357662`. Response, replay, extracted log and source/team provenance
are saved under `v4_2-portal-*`; no error/fallback strings were found in the
extracted battle log. A smoke test cannot prove the absence of every fallback.
No final competition entry was submitted.

Release source SHA256:
`65f866cf17ace2330e8856434706839320cf43338d70203348163679ea9f2457`.

## Larger research candidates not selected

The `v6-revenge*` candidates continue a modeled duel after an own faint, select
a live reserve, apply entry Intimidate, retain the fainted member's loss in
whole-team value, and resume combat. Immutable preparation was moved out of
chance branches to reduce repeated work. This is bounded own-team continuation,
not a full battle simulator or a model of the hidden enemy team.

The `v6-scarf*` candidates additionally consider a 12% Choice Scarf hypothesis
when speed order could change for a living own member. Worst-case penalties
are weighted within each item hypothesis. The prior was fixed before testing;
it is not a learned posterior or confirmed enemy item. The `v6-release-*` name
was provisional: those files were not promoted.

| Prototype | Mixed holdout /200 | Adaptive holdout /192 | Custom /60 | Stateless /40 | Direct v4.1 /80 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Own-team continuation plus cap fix (`efficient`) | 154 | 148 | 58 | 34 | 40 |
| Own-team continuation, Scarf hypothesis and cap fix (`release`) | 153 | 152 | 58 | 33 | 40 |
| V4.1 matched controls | 151 | 151 | 59 | 31 | — |

The Scarf candidate gained one point on the mixed holdout, with an opposing-team
cluster bootstrap 95% interval of -6 to +7.5 percentage points. Its adaptive
gain was 0.52 points, interval -6.25 to +6.77. Both candidates tied v4.1 directly
and were slower; the larger version recorded p95 values of roughly 326–435 ms
under load. These results do not establish a competitive advantage sufficient
to replace the ordinary policy. V4.2 therefore includes only the endgame fix.

Development counts are also preserved: the original continuation model scored
129/160 mixed and 82/96 adaptive; adding Scarf scored 129/160 and 84/96.
Those are candidate-selection results, not independent holdouts. The saved
repeated-team comparisons bootstrap whole opposing-team configurations, rather
than treating repeated battles against the same team as independent samples.

Research tests for team loss accounting, reserve entry, non-resurrection and
Scarf eligibility remain under `research/test_revenge.py` and `test_scarf.py`.
`tools/run_eval.py` now supports the archived `v4_1` opponent with an explicit
`--opponent-team archive/v4_1/team.json`, avoiding incorrect hidden-own-set
assumptions when measuring direct comparisons.
