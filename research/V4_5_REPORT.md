# v4.5: combined agent and aggregate comparison

The recommended submission is `dist/REDLINE_Search.zip`, also versioned as
`dist/REDLINE_Search_v4_5.zip`. Both contain exactly agent.py and team.txt.

Agent SHA256:
`0afe57fe578ffdbd74fa848deae46524f3de4d66065bd152f061c9e684e45c69`.

ZIP SHA256:
`779da7d7752179b6ffe4f241160abd132fb95f4943f391a5225a69e3399d4625`.

## Change

The release uses Choice Band / Clear Body / Adamant Dragapult with Dragon
Darts, Sucker Punch, Psychic Fangs and Flamethrower. Dragonite and Arcanine
retain the v4.4 sets. The policy keeps v4.4's hazard inference, Choice-lock
continuation, reserve-loss penalty, Sucker Punch and turn-cap mechanics.
Read-only move definitions, cached item multipliers, hoisted speed/accuracy
calculations and a preview memory reset reduce repeated work.

## Fresh comparison

The combined candidate and its team were fixed before 4,512 actual Showdown
battles across 96 jobs. Neither policy nor team was tuned on these results.
The simulator was Pokemon Showdown 0.11.11. Opponents received the same
restricted observations, without hidden enemy sets or reserve information.
All scheduled battles completed without illegal actions or worker exceptions.

Each agent played the same 960-game common-opponent schedule: two independent
64-team custom adaptive suites, a tactical custom suite, mixed default policies,
and the archived v4.3.2 agent/team. Seeds and player sides were paired.

| Agent | Wins / games | Win rate |
| --- | ---: | ---: |
| Combined v4.5 | 770/960 | 80.21% |
| Teammate submission | 758/960 | 78.96% |
| Original v4.4 | 718/960 | 74.79% |

The paired league gain is +5.42 percentage points over v4.4, with a descriptive
clustered 95% interval of +1.71 to +9.09 points. Against the teammate it is
+1.25 points, interval +0.21 to +2.50. The candidate converts 12 teammate losses
into wins without reversing a teammate win on this league.

Intervals use 10,000 bootstrap replicates with seed 502721. Whole ordered
opponent-set clusters retain correlations between repeated seeds, player sides
and policies. Fixed-opponent comparisons resample seed pairs. These intervals
are descriptive, without multiple-comparison adjustment.

| Direct matchup | Left wins | Right wins |
| --- | ---: | ---: |
| Combined vs v4.4 | 163 | 93 |
| Combined vs teammate | 128 | 128 |
| v4.4 vs teammate | 99 | 157 |

Each pair played 128 seed pairs with player sides reversed. There were no draws.
The direct tie with the teammate remains a tie. Across all 6 x 6 complete team
ordering combinations, four games each, the combined agent scored 112/144
against v4.4 and 72/144 against the teammate. Ordering tests are exploratory.

| Execution mode | Combined | Teammate | v4.4 |
| --- | ---: | ---: | ---: |
| Fresh instance per request | 86/96 | 86/96 | 79/96 |
| Accurate own boosts supplied | 80/96 | 77/96 | 80/96 |

Each mode uses its own seed schedule. The main league hides own boosts to
match sparse portal telemetry. Differences between modes do not isolate the
effect of persistence or boost reporting.

## Validation

- All 52 Python tests and both JavaScript tests pass. Three historical policy
  positions explicitly retain their archived team configuration.
- The optimized engine matches the unoptimized engine's actions and memory on
  the same physical team across 859 recorded decisions.
- All 384 official-simulator entry-hazard fixtures match. The controlled hazard
  position preserves HP; both versions still lose that deliberately adverse
  position. The turn-cap HP-objective scenario also passes.
- A separate 720-decision timing run holds the physical team and positions
  constant. Median decision time is about 7.78 ms for the combined engine,
  8.59 ms for the unoptimized reference and 7.82 ms for the teammate. Timings
  vary with load and do not measure battle strength.
- The exact packaged candidate won its authorized practice smoke test in five
  turns, battle sim-1792097210666. This sample-opponent result is separate from
  the strength comparison. No final competition entry was submitted.
- `python tools/verify_release.py` checks the recommended package, manifest,
  generated source, core and team. `python tools/verify_parallel.py` confirms
  the Kaggle campaign still uses its original frozen v4.3.2 source bundle.

## Selection and limits

V4.5 has the highest observed score in this fixed league and retains the
mechanics fixes. Its lead over the teammate is modest. Original v4.4 still wins
more on the mixed schedule, 143/192 versus 138/192, so the selected team has
matchup tradeoffs. These results do not establish universal dominance or a
tournament win probability. Hidden sets, opposing switches, volatile effects
and post-knockout continuation remain approximate.

V4.4 is preserved in archive/v4_4. Future Kaggle finalists must be recompiled
and compared using the selected engine before promotion.
