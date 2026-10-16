# Monte Carlo rollout study, version 1

Freeze sources, checks, timing, team, suites, seeds, schedules, weights and rules
before any battle results. No source changes or tuning after freeze.

All builds equip the exact v4.6 Dragapult/Snorlax/Corviknight team:

- control: original v4.6.
- phased: the previously tested recovery/Phantom Force corrections.
- mc: original v4.6 plus bounded hybrid Monte Carlo rollout search.
- phased_mc: identical Monte Carlo search on the corrected temporal model.

The new algorithm is root-bandit Monte Carlo, not full tree MCTS, an exact
simulator, equilibrium solver or learned neural model. It reranks at most three
nearby base choices using 96 adaptively allocated rollouts, up to six turns,
seeded from public observations. Half the sampled hidden sets use curated
defaults; half sample the 38 complete presets that pass current roster options.
Neither rollout policy sees the other player's sampled hidden configuration.
Each simulated player chooses before the other action is revealed. No unseen
enemy bench or voluntary enemy switch is invented; known own faint replacements
are modeled. Continuation policies use move heuristics, not a new search tree.
The root score blends 65% existing score and 35% Monte Carlo estimate; overrides
also need a positive paired-sample margin. That internal margin is a heuristic,
not a statistical strength certificate. Capped-HP endgames, forced entries,
Choice locks and healthy-reserve safety guards remain protected.

Each build plays development 216, validation 432 and confirmation 864 games:
6,048 scheduled games total, with 504 fresh generated enemy builds plus the
known twelve frozen rosters covering all 24 species and three cyclic leads.
Generated builds and actual simulator seeds must be disjoint from all preceding
campaigns. Same opposing builds, seeds and sides across candidate and references.
Enemy sets/bench remain hidden and own boosts sparse. This is a CPU experiment.

Weights: adaptive 40%, tactical 20%, frozen league 40%. Select exactly one new
challenger (mc or phased_mc) by validation weighted score, then HP margin, then
prefer mc. Record selection before starting any confirmation games. Both are
still evaluated on confirmation, but only the validation-selected challenger
can be promoted in this study. Other contrasts are explanatory.

Promotion requires all automated checks and source/schedule audits, higher
confirmation weighted mean versus control with positive lower paired 95% bound,
and no validation/confirmation category regression over five percentage points.
Also require a positive confirmation mean gain versus its own parent engine;
this attribution comparison is descriptive. Runtime must have median below
twice control and p95 below four times control on the frozen synthetic workload,
with max below 500 ms. These are project gates, not organizer-published limits.
Monte Carlo receives additional CPU work; this is not an equal-CPU comparison.

Use 4,000 paired stratified bootstrap replicates, seed 384901, whole enemy-build
clusters and whole base-roster clusters. Local conditional scores are not unknown
tournament win probabilities. If gates fail retain v4.6, with its documented
forecasting limitations. Do not retune on confirmation or promote the other
candidate post hoc. No practice uploads or final entry submission in this study.
