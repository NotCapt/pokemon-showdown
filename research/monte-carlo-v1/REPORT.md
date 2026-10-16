# Monte Carlo rollout search: frozen trial

Completed and audited **6,048 new scheduled games** across four unchanged, same-team policies. Each plays 216 development, 432 validation and 864 confirmation games. The validation-selected challenger is **mc**; recommended by the fixed gates: **mc**.

## Confirmation

| Build | Wins / games | Weighted score | Adaptive | Tactical | Frozen league |
| --- | ---: | ---: | ---: | ---: | ---: |
| mc | 800/864 | 91.84% | 95.83% | 97.40% | 85.07% |
| phased_mc | 792/864 | 90.62% | 96.61% | 97.40% | 81.25% |
| phased | 755/864 | 85.80% | 94.01% | 97.92% | 71.53% |
| control | 746/864 | 84.69% | 92.97% | 97.92% | 69.79% |

| Paired comparison | Weighted gain | Descriptive 95% interval |
| --- | ---: | ---: |
| mc-vs-control | +7.153 pp | [+2.15, +12.95] pp |
| phased_mc-vs-control | +5.938 pp | [+2.60, +9.86] pp |
| phased_mc-vs-phased | +4.826 pp | [+2.01, +7.78] pp |
| phased-vs-control | +1.111 pp | [-1.39, +4.10] pp |

## Decision and cost

Promotion gates: `{"categories": true, "promote": true, "runtime": true, "strength": true}`. Only the challenger selected before confirmation can be promoted; other confirmation contrasts are explanatory. No retuning on results.

| Build | Median decision | p95 | Maximum |
| --- | ---: | ---: | ---: |
| control | 11.78 ms | 27.96 ms | 50.07 ms |
| phased | 12.58 ms | 28.19 ms | 56.75 ms |
| mc | 16.21 ms | 84.03 ms | 124.63 ms |
| phased_mc | 15.69 ms | 99.20 ms | 134.04 ms |

Monte Carlo activated on 28/96 synthetic positions for mc and 22/96 for phased_mc. The timing table includes positions where the guard retained the original search, including forced switches and turn-98+ endgames.

Same 96 public synthetic observations; two randomly interleaved repetitions, no battle workers. Import/init/copy excluded; not strength evidence.

Monte Carlo receives additional computation, not equal CPU. Runtime gates are our engineering choices, not organizer-published limits. Each exact source passed 63 Python tests and two JavaScript checks. Information-isolation, legal-prior, speed-tie, budget, deterministic-repeat, preview-reset and action-legality properties passed.

Both exact Monte Carlo sources also imported and ran under `python -I -S` in empty temporary directories: 144 cases each, all actions legal, requests/static data unchanged, active Monte Carlo searches observed.

## Algorithm and limits

Root-bandit Monte Carlo adds 96 adaptively allocated sampled rollouts of at most six turns when two or more near-leading actions remain. It blends 65% original tactical score with 35% rollout value; an override also needs a positive paired-sample margin. It preserves forced-entry/capped-endgame handling and a conservative healthy-reserve guard. The same policy is tested on original v4.6 mechanics (mc) and the existing recovery/Phantom Force prototype (phased_mc), with both parent engines as controls.

Where legal alternatives exist, enemy sets are sampled with a 50% chance of using one of 38 complete validated presets and a 50% chance of using the organizer defaults. Species without retained alternatives use defaults. Review found that some organizer defaults already used by both parent engines have EV allocations or a nature absent from the selectable options; the default branch is an approximate prior, not entirely validated selectable builds. See default-prior-review.json. Own submission configurations are separately validated. Rollout move policies see their own configuration and public opponent views. They do not select responses after observing the other simultaneous action. Own known faint replacements are modeled. No unseen enemy bench or voluntary enemy switch is invented. This is neither full tree MCTS nor an exact Pokémon simulator or game-theoretic solution. Continuation PP, status durations, pivots and future observation reporting remain approximate. This compares complete hybrid policy bundles, including priors, continuation heuristics and sampled paralysis/flinch handling; it does not isolate random sampling from every other implementation change. No actual hidden enemy state reaches any Python agent.

All four use the identical v4.6 Dragapult / Snorlax / Corviknight team. Generated sets and simulator seeds are new and disjoint from preceding campaigns. The twelve frozen roster identities are known; they cover all 24 allowed species and all three cyclic leads. Main observations hide enemy sets/bench and own boosts. Weights are adaptive 40%, tactical 20%, frozen league 40%. Paired intervals use 4,000 stratified bootstrap replicates with whole opposing-build/base-roster clusters, seed 384901. Scores describe this local league, not tournament win probabilities.

Frozen protocol, manifests, exact sources and all raw result records remain alongside this report. Source/schedule audits verify hashes, seeds, sides, legal execution, ranks, paired comparisons, validation selection and gates. Practice compatibility is recorded separately below. No final competition entry was submitted.

## Development and validation

| Phase | Build | Wins / games | Weighted score |
| --- | --- | ---: | ---: |
| development | phased_mc | 188/216 | 86.39% |
| development | mc | 185/216 | 85.00% |
| development | control | 180/216 | 82.08% |
| development | phased | 176/216 | 79.86% |
| validation | mc | 401/432 | 92.08% |
| validation | phased_mc | 387/432 | 88.06% |
| validation | control | 379/432 | 85.83% |
| validation | phased | 376/432 | 85.00% |

The exact frozen experiment inputs, result records and audit tools are preserved in `dist/REDLINE_Monte_Carlo_Project_v1.zip`. Extract into a separate directory, install the pinned runtime with `npm ci`, then run `python tools/audit_monte_carlo.py`.

## Confirmation fixed rosters

| Opposing team, all three leads | Control | Monte Carlo | Corrected Monte Carlo | Games each |
| --- | ---: | ---: | ---: | ---: |
| Dragonite/Dragapult/Arcanine | 14 | 14 | 14 | 24 |
| Dragapult/Tyranitar/Corviknight | 7 | 22 | 10 | 24 |
| Dragapult/Snorlax/Excadrill | 24 | 24 | 24 | 24 |
| Dragapult/Snorlax/Corviknight | 15 | 23 | 19 | 24 |
| Salamence/Dragapult/Snorlax | 11 | 12 | 14 | 24 |
| Dragapult/Gyarados/Snorlax | 20 | 21 | 19 | 24 |
| Togekiss/Metagross/Volcarona | 20 | 20 | 24 | 24 |
| Gengar/Gyarados/Ferrothorn | 16 | 18 | 18 | 24 |
| Alakazam/Arcanine/Garchomp | 20 | 24 | 24 | 24 |
| Greninja/Scizor/Hydreigon | 24 | 22 | 24 | 24 |
| Lapras/Corviknight/Lucario | 6 | 21 | 20 | 24 |
| Venusaur/Charizard/Blastoise | 24 | 24 | 24 | 24 |

## Release

Promoted as **v4.7**, source SHA256 `5dac01afbde238d621a27ca2c11f8bc4e2ee0e094af26f5bb9c47d0c170b62fb`. Artifact: `dist/REDLINE_Search_v4_7.zip`. The original v4.6 remains archived and its ZIP is unchanged. The selected mc source retains the original Roost/Rest forecasting limitations; the corrected-model Monte Carlo variant was not selected. The local gate does not certify an exact simulator.

The exact packaged source passes 288 isolated legal-action cases. This separate, broader workload measured 30.14 ms median, 272.52 ms p95 and 529.93 ms maximum; these are not the controlled preflight workload. No numeric CPU/memory limit is published in the reviewed rules.
Practice compatibility result: `{"agentSha256": "5dac01afbde238d621a27ca2c11f8bc4e2ee0e094af26f5bb9c47d0c170b62fb", "battleId": "sim-1792166737715", "probe": false, "responseSha256": "5533d183b9696766b5a864f50c2b005e1c6e1226019fedb79694caabd14b5bef", "success": true, "teamSha256": "64277db93575a3453efd91d2c4492f77b059f9b55aa81e74b3630190ef35f624", "turns": 8, "winner": "REDLINE Search", "winnerSlot": "p1"}`. This single sample-baseline game is outside the strength study.
