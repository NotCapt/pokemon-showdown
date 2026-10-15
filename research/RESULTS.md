# Final validation results

Historical v1 results. Current release and comparisons are documented in
`research/V3_REPORT.md`; the main ZIP now contains v3.

Agent SHA-256: `38e2a25fcbb3e55bc2f24b77e024266e201175e39b673f80f37339e5650c363b`

All rows below use this exact generated file and Pokémon Showdown 0.11.11.

| Opponent / observation | Wins | Losses | Draws | Median / p95 decision time |
| --- | ---: | ---: | ---: | --- |
| Damage-calculating tactical baseline | 84/100 | 16 | 0 | 53.6 / 115.7 ms |
| Same search policy on portal-default teams | 36/40 | 4 | 0 | 51.5 / 112.8 ms |
| Tactical baseline; empty boosts and fresh agent every decision | 48/60 | 12 | 0 | 40.5 / 101.1 ms |

Latest normal portal practice: **REDLINE Search won in 8 turns**, battle `sim-1792071337781`.
Ten unittest tests passed, including 100 generated legality states, forced switches, immunities, priority knockouts, Focus Sash, burns and setup caps.
No illegal actions or decision exceptions occurred in the final 200 local battles.

## How to interpret this

These are wins against specific local opponents, not an estimated probability of winning the tournament. All opposing teams used portal-default sets; no independent top-tier competitive bot was benchmarked. The search opponent is a copy of our own policy, not FoulPlay.
Team-selection runs used 40 battles per candidate. Evaluation uses separate seeds, with the first four opposing team compositions fixed and subsequent teams sampled from the roster. Each pair reverses player position on the same matchup and simulator seed. Evaluation seeds were reused for regression checks after compatibility fixes; this is not an untouched final blind test.
JSON reports include per-game seeds, teams, outcomes and latencies. Their simple Wilson intervals do not adjust for paired/correlated matches or team selection and should be read only as descriptive approximations.
Timing was measured locally while several benchmark processes shared CPU. It does not establish the hosting service deadline.
The harness supplies only documented observable fields: it does not leak the opponent's private moves, items, abilities, EVs or bench state. The sparse test additionally removes our own boosts and discards agent-instance memory.

## Portal observations

Normal production tests won in 29, 11, 5 and 8 turns across iterations. These four games are integration smoke tests, not a representative win-rate sample. Replay inspection found excess setup; final safeguards limit it under missing or stateless telemetry.
An approved diagnostic exception returned a service Runtime.ExitError. An approved invalid-action probe was silently replaced by fallback moves and finished a battle; that diagnostic result is excluded from normal test results. It did not reveal the raw observation.
The latest normal replay and result are preserved locally. The remote replay URL may be ephemeral; use the saved response as the durable record.
