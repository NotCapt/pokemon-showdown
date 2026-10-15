# Kaggle finalists evaluated with v4.5

All three original screens completed: 77,700 battles, 2,024 default species trios, six finalists per shard. Their source bundle and complete, disjoint coverage were verified before import.

The 18 nominated teams and the v4.5 incumbent were recompiled with the exact same frozen v4.5 engine. These are new battles; old screening scores were not reused.

Qualification used 48 games per policy for all 19 builds; three challengers and incumbent reached validation at 96 per policy. One challenger selected on validation met the incumbent on independent confirmation at 192 per policy. Policies were adaptive, tactical and the exact frozen v4.5 incumbent. Qualification, validation and confirmation use distinct generated team suites and seeds.

| Confirmation policy | Incumbent wins | Challenger wins | Games each |
| --- | ---: | ---: | ---: |
| adaptive | 173 | 162 | 192 |
| tactical | 172 | 176 | 192 |
| frozen | 96 | 188 | 192 |

Mean score gain: +14.76 percentage points; descriptive paired 95% interval [+10.59, +18.75]. Improved games: 123; regressed games: 38.

Promotion criterion passed: **False**. The rule was fixed before qualification: higher confirmation composite score, positive lower paired interval, and no per-policy regression exceeding five percentage points. A failed rule retains the incumbent.

## Selected team

- Dragonite: Choice Band, Multiscale, Adamant; Physical Sweeper (252 Atk / 252 Spe / 4 SpD); moves: Extreme Speed, Earthquake, Ice Spinner, Fire Punch.
- Dragapult: Choice Band, Clear Body, Adamant; Physical Sweeper (252 Atk / 252 Spe / 4 SpD); moves: Dragon Darts, Sucker Punch, Psychic Fangs, Flamethrower.
- Arcanine: Assault Vest, Intimidate, Adamant; Bulky Attacker (252 HP / 252 Atk / 4 SpD); moves: Flare Blitz, Extreme Speed, Crunch, Play Rough.

Selected source SHA256: `0afe57fe578ffdbd74fa848deae46524f3de4d66065bd152f061c9e684e45c69`.
Selected ZIP SHA256: `51672a30308807e56f2dc05b25396b7f0a0279c3692fed84e646adb7d7864b9a`.

Audit: 5,040 new engine battles, 75 complete reports, zero illegal actions or worker exceptions. Every compiled OWN config, opponent set, seed, player side and exported ZIP byte was verified.

The parallel Kaggle final retains its original v4.3.2 engine and separate incumbent. Its outcome is a different experiment and cannot be used as a latest-engine result. Selection here is conditional on a small experimental policy league, not a tournament win probability or proof of an exhaustive set search. Hidden sets, opponent switching and volatile effects remain approximate.

Reproduce with tools/evaluate_kaggle_finalists.py --run, then tools/audit_kaggle_evaluation.py. Source changes require a new evaluation directory.
