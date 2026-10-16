# Fresh v4.7 matchup tests

Freeze exact v4.6/v4.7 sources, teams, simulator, suites and schedule before results.
No policy/team changes, selection, tuning or release promotion during this test.
Local only; no practice uploads or final competition submission.

- Native head-to-head: 256 games, v4.7 versus v4.6.
- Native self-play: 128 games each for v4.7 and v4.6 (symmetry control).
- All 36 team-order pairings: 4 games each, both v4.7-v4.6 and v4.7-v4.7.
- Fresh random field: 64 coherent builds plus 64 uniformly sampled legal builds,
  each played twice (alternating sides) under random, tactical and adaptive policy,
  for each release. 768 games per release; 2,336 games overall.

All 24 allowed species appear in each random-build cohort. Uniform legal builds
can have poor set synergy; coherent builds use the unchanged independent generator.
Random policy samples legal moves and uses the first legal forced replacement;
tactical policy uses the existing damage heuristic; adaptive policy can switch
voluntarily using its own true state and a model of public enemy information.
Only documented public information reaches Python agents; own boosts are sparse,
enemy sets and bench hidden. Native sources retain their exact compiled own-team
configurations; changing team order does not change any species configuration.

Each two-game seed pair alternates sides. The two releases share the same random
opponents/seeds/sides. New simulator seed tags and build fingerprints do not occur
in inspected earlier stored results/suites. HP adjudicates battles after turn 100.

Report raw wins/losses/draws, win+half-draw scores, game lengths, capped games,
and all-order matrices. Native head intervals resample whole two-game seed pairs.
Random-field gains use 10,000 paired bootstrap samples (seed 260716991), clustering
whole builds across all three policies and sides, stratified by build cohort.
Intervals are descriptive local-field estimates. Self-play is a symmetry and
order diagnostic, not evidence of strength against outside players. Concurrent
battle latency is diagnostic only and is not a controlled performance benchmark.
