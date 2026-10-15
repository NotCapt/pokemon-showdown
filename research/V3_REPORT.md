# V3 release evaluation

Historical report: v4 is now the main release for the tested persistent service.
V3 remains the stateless fallback. See `research/V4_REPORT.md` for current
comparisons and limitations.

V3 is the recommended release. It replaces the main ZIP; v1 and v2 source/team
snapshots remain under `archive/`. This report supersedes historical statements
about the recommended ZIP in earlier version reports.

## Changes selected by testing

The primary strength improvement is team configuration: Adamant Choice Band
Dragonite uses Extreme Speed / Earthquake / Ice Spinner / Fire Punch. This gives
immediate damage and retains priority without spending a turn on setup. Dragapult
and Corviknight keep their previous configurations. A Jolly Choice Band variant
was screened but performed worse on the development schedule (24/40 versus
28/40 for Adamant against v1) and was not selected.

V3 keeps the v2 policy and mechanics except for explicit 50/50 first-turn speed
ties and a cheaper search-state clone. Immutable stats/types/moves are shared;
mutable boost dictionaries are copied. Sixteen tests passed, including clone
isolation, both speed-tie orders and all prior mechanics/legality regressions.

A broader continuation search was implemented and tested, then rejected:
17/40 versus v1 and 30/40 on the custom tactical suite. Its local p95 latency
reached hundreds of milliseconds. Source and agent are preserved as
`research/extended_search_core.py` and `research/extended_search_agent.py`.
It is not part of the promoted release. Public coherent enemy-set hypotheses
were prepared experimentally but are not used in live v3 decisions.

## Final exact-artifact results

| Opponent / conditions | V3 wins | Local median / p95 |
| --- | ---: | ---: |
| Saved v1 on its original team, empty own boost telemetry | 62/100 | 15.5 / 45.4 ms |
| Saved v2 on its original team, empty own boost telemetry | 66/100 | 17.2 / 43.0 ms |
| Six custom teams, frozen tactical policy, empty boosts | 56/60 | 19.7 / 56.1 ms |
| Tactical policy, empty boosts, fresh instance every decision | 38/40 | 21.0 / 50.4 ms |

No illegal actions or decision exceptions occurred in these 300 games. All four
reports have the same agent SHA-256, checked by `tools/summarize_v3.py` against
the generated release file. Reports preserve seeds, opponent configurations,
outcomes, latency, and simulator version (Pokémon Showdown 0.11.11).

The frozen v1 control scored 56/60 on the same custom tactical schedule; frozen
v2 scored 54/60. V3 therefore matches v1 on that suite and improves over v2 by
two games. This is not evidence that every matchup improves.

The selected candidate was first screened on a 40-game development schedule.
The 100-game v1/v2 schedules used different seeds; after the speed-tie change,
those schedules were reused for regression verification. They should not be
described as wholly untouched blind tests. The separate stateless robustness
schedule was not used to select the team.

Each matchup is played twice with player positions reversed. Cluster bootstrap
resampling of these two-game pairs gives descriptive 95% intervals of 53–70%
against v1 and 58–74% against v2. These intervals do not adjust for team selection
or systematic simulator/model errors. Full summary: `research/v3-summary.json`.

## Live practice

The latest normal test with the final source and final team was accepted by the
competition practice service: battle `sim-1792073295040`, REDLINE Search won in
seven turns. This is an integration smoke test, not a measured portal win rate.
The response/replay are preserved in `research/v3-portal-result.json`,
`research/v3-portal-replay.html` and `research/v3-portal-battle.log`.

## Interpretation and limitations

There is now measured improvement against both saved submissions, unlike the
previous v2 candidate. Most of that improvement comes from the team rather than
deeper search. Both saved opponents share modeling assumptions with v3. The
custom tactical opponent uses the frozen v1 damage model and still estimates
hidden/default sets imperfectly. No independent top-tier external agent has been
benchmarked, so these results cannot establish tournament-winning strength.

The harness shares no private opponent item, ability, EVs, moves or bench state
with either decision policy. Own team configuration is embedded in each agent.
The custom tactical policy is deliberately simple and does not know all of its
own customized stats/items; this is held constant between version comparisons
but limits absolute performance claims. Root damage outcomes use three shared
quantiles; independent damage rolls and secondary effects are not fully expanded.
Later continuations still use greedy attacks and approximate chance outcomes.

Portal boost memory, imperfect enemy set assumptions, future switching, hazard
state, status duration and many volatile effects remain open areas. In particular,
remembered setup/stat drops describe attempts and can be wrong after a failed
move. V3 is a stronger tested submission, with substantial room for improvement.
