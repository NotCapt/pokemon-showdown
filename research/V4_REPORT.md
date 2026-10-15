# V4 release: Arcanine team and entry-effect/chance corrections

V4 is recommended for the tested competition service, which preserved agent
instances in the controlled diagnostic. It is not uniformly better than v3.
Keep `dist/REDLINE_Search_v3.zip` as the tested fallback if the execution service
starts creating a fresh agent every turn.

## Final selected team and changes

Dragonite (Choice Band, Adamant) and Dragapult (Choice Specs, Timid) retain their
v3 sets. Arcanine replaces Corviknight:

- Assault Vest, Intimidate, Adamant.
- 252 HP / 252 Atk / 4 SpD.
- Flare Blitz / Extreme Speed / Crunch / Play Rough.

This combines Fire resistance and physical attack reduction with special bulk
and immediate coverage. It avoids the Scizor vulnerability introduced by the
experimental Togekiss offense team.

First-turn flinches now branch probabilistically, conditional on the move
hitting and moving first. A flinch cancels the complete reply, including healing,
setup and recoil. The root respects Inner Focus and doubles relevant flinch
probability for Serene Grace. Later greedy continuations retain the earlier
approximation, and secondary lists beyond the supported `secondary` field are
not fully modeled.

Own switch-in Intimidate now handles Clear Body and Inner Focus immunity, and
Mirror Armor reflection. Expected entry boosts persist between decisions when
the portal omits boost fields, resetting when the enemy changes. Supplied boost
telemetry takes precedence. This still assumes the enemy's default ability when
its actual ability is unknown, and does not reconstruct every opposing entry
effect or unobserved boost/reset.

## Exact release results

All five final reports use SHA-256
`4af73c4ca0c20e67777b360c2d2a5cd03b2d6786ad92542c7b89834a1e404d26`.
The archive contains that exact source plus the matching team text.

| Test | V4 | V3 control where available |
| --- | ---: | ---: |
| Direct head-to-head, original v3 team | 70/120 | 50/120 |
| Six custom teams, frozen tactical policy, same schedule | 59/60 | 56/60 |
| Saved v1, seed 41723 | 69/100 | 62/100 |
| Saved v2, seed 57119 | 65/100 | 69/100 |
| Fresh instance every decision, seed 64513 | 31/40 | 38/40 |

All 420 final v4 battles completed without illegal actions or decision
exceptions. Twenty release tests passed. The separate two tests for rejected
belief-model experiments also pass, but are not counted as release tests.
Local median decisions were approximately 8–10 ms and p95 26–38 ms across the
final runs. Timings are hardware/load-specific, not a hosting-service guarantee.

`research/v4-summary.json` contains matched-pair bootstrap intervals and report
paths. For direct v3 comparison, the descriptive interval is approximately
53.3–63.3% for v4. Each two-game pair reverses player position; bootstrap samples
whole pairs. These intervals do not account for candidate selection, model
systematic error or the narrow opponent pool.

## Promotion rationale and limits

V4 won the direct v3 matchup and improved the custom-team and v1 results. It
lost four games relative to v3 on the same v2 schedule and seven on the stateless
schedule. The real portal diagnostic preserved state, so v4 is selected for that
observed service behavior. If that contract changes, use v3 until revalidated.
There is no claim of universal dominance or tournament-winning probability.

The v3-comparison seed differs from the 40-game development screen. The custom
suite and some older-agent schedules were reused during candidate selection;
they are regression/selection evidence, not untouched blind tests. The same
120-game schedule was also used to assess a different Togekiss candidate, so the
Arcanine validation should not be portrayed as wholly independent of development.

The custom tactical opponent uses a frozen simple policy with imperfect default
set assumptions, including imperfect knowledge of its own customized builds.
The saved versions share substantial modeling assumptions. No independent
top-tier Pokémon agent has been benchmarked. All decision inputs remain limited
to the portal-like schema; no private opponent moves/items/stats/bench are exposed.

## Live practice

Final Arcanine source/team were accepted by the practice service and won in
seven turns, battle `sim-1792075067657`. Response and replay are preserved in
`research/v4-portal-result.json`, `research/v4-portal-replay.html`, and
`research/v4-portal-battle.log`. This single smoke test confirms integration,
not a meaningful win-rate estimate. No final competition entry was submitted.

## Experiments evaluated and rejected

Several ideas were implemented rather than assumed to help:

| Candidate | Direct v3 development result | Other evidence |
| --- | ---: | --- |
| Coherent enemy-set mixture, broad initial uncertainty | 9/40 | Too defensive |
| Weighted likelihood/robustness variants | 22/40 | Custom suite 46/60 for sharper variant |
| MAP set update, conservative default policy | 20/40 | No demonstrated gain |
| Previously seen enemy switch hypotheses | 16/40 | Custom suite 56/60 |
| Last-Pokémon penalty and cheaper switching | 20/40 | No demonstrated gain |
| Jolly Band Dragonite | 23/40 | Not selected |
| Corviknight lead | 24/40 | Not selected |
| Togekiss replacing Corviknight | 26/40; 74/120 validation | v1 95/100; custom regression to 48/60 |
| Togekiss replacing Dragapult | 17/40 | Custom 56/60 |
| Two Choice Scarf attackers | 23/40 | Custom 42/60 |
| Assault Vest Arcanine | 23/40; 70/120 validation | Custom 59/60; selected |

The belief prototype updates coherent candidate-set probabilities from
uncomplicated HP changes, with skips for recoil/status confounding. It remains
under `research/v4-beliefs-switch-core.py` and related generated agents and
tests. Partial observations and ambiguous move outcomes made its policy changes
unreliable. It is absent from the selected agent. Experimental `enemy_sets` data
remain embedded as unused data only.

Future gains still require stronger independent opponents, better observation
tracking, a more faithful simulator and careful handling of opponent switching.
Unmodeled hazards, volatile states, crits, several status effects, independent
damage-roll combinations and long-horizon team consequences remain limitations.
