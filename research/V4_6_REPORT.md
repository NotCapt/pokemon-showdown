# Diverse league results

Recommended by the frozen selection rule: **Dragapult/Snorlax/Corviknight**.

Promotion gate passed: **True**. All 8,856 scheduled games and 1,362 reports passed the schedule/source audit. The source engine is unchanged v4.5; this campaign compares team builds, not newly trained decision models.

## Independent confirmation

The challenger **Dragapult/Snorlax/Corviknight** was selected on validation before confirmation. Each final build played 864 fresh confirmation games. Qualification and validation games are excluded from the confirmation comparison.

| Opponent category | Weight | Incumbent wins | Challenger wins | Score gain |
| --- | ---: | ---: | ---: | ---: |
| adaptive | 40% | 331/384 | 370/384 | +10.16 pp |
| tactical | 20% | 169/192 | 188/192 | +9.90 pp |
| league | 40% | 148/288 | 181/288 | +11.46 pp |

Weighted score: incumbent 72.64%, challenger 83.26%. Weighted gain +10.625 points; descriptive paired 95% interval [+3.68, +18.23]. Improved game outcomes: 145; regressed outcomes: 54.

The score is the weighted mean above, with no weakest-category term. Each of the twelve fixed teams contributes only 3.33% of the total score. The incumbent and earlier 188–4 challenger are both in that roster.

## Fixed opponents, all three lead choices

| Opponent team | Incumbent wins | Challenger wins | Games each |
| --- | ---: | ---: | ---: |
| Dragonite/Dragapult/Arcanine | 4 | 8 | 24 |
| Dragapult/Tyranitar/Corviknight | 0 | 5 | 24 |
| Dragapult/Snorlax/Excadrill | 12 | 24 | 24 |
| Dragapult/Snorlax/Corviknight | 4 | 11 | 24 |
| Salamence/Dragapult/Snorlax | 14 | 8 | 24 |
| Dragapult/Gyarados/Snorlax | 4 | 22 | 24 |
| Togekiss/Metagross/Volcarona | 20 | 18 | 24 |
| Gengar/Gyarados/Ferrothorn | 22 | 14 | 24 |
| Alakazam/Arcanine/Garchomp | 16 | 22 | 24 |
| Greninja/Scizor/Hydreigon | 22 | 24 | 24 |
| Lapras/Corviknight/Lucario | 6 | 3 | 24 |
| Venusaur/Charizard/Blastoise | 24 | 22 | 24 |

## Selection path

| Validation team | Weighted score | Wins / games |
| --- | ---: | ---: |
| Dragapult/Snorlax/Corviknight | 85.00% | 372/432 |
| Dragapult/Tyranitar/Corviknight | 75.69% | 331/432 |
| Dragonite/Dragapult/Arcanine | 72.36% | 322/432 |
| Lapras/Corviknight/Lucario | 70.42% | 311/432 |

Twenty-five candidates played qualification, then three non-incumbents plus the incumbent played validation. One challenger was chosen there. Confirmation used separate generated opposing teams and random seeds. The fixed roster identities remain shared and known.

## Selected configuration

- Dragapult: Choice Band / Clear Body, Jolly, Physical Sweeper (252 Atk / 252 Spe / 4 SpD). Moves: Dragon Darts, Phantom Force, Flamethrower, U-turn.
- Snorlax: Leftovers / Thick Fat, Careful, Special Wall (252 HP / 252 SpD / 4 Def). Moves: Body Slam, Earthquake, Crunch, Rest.
- Corviknight: Leftovers / Mirror Armor, Impish, Physical Wall (252 HP / 252 Def / 4 SpD). Moves: Brave Bird, Body Press, Roost, Iron Defense.

Selected source SHA256: `07b1e968db139b43ebf4dcf49900719977096ac42434d217f1f8534984183ac5`.
Export ZIP SHA256: `c15f9c6ce60c6de0eb13ef2df05755d52ad109afcc54f4fa1b189012e69b864f`.

## Rules, evidence and limits

Promotion required a higher confirmation score, a positive lower paired interval, and no category regression above five percentage points. The rule, weights, all candidates and all opponent schedules were recorded before this campaign. A failed gate retains the incumbent.

4000 paired stratified bootstrap replicates, seed 384901. Resample opposing-set pairs for adaptive/tactical and complete base-roster clusters (all leads and seeds together) for the fixed league. Descriptive interval conditional on this experimental population.

The twelve frozen teams cover all 24 allowed species. Opponents use the same restricted public enemy observations; generated sets and the enemy bench remain hidden. All compiled team configurations, hashes, simulator seeds, player sides, opposing sets, score calculations, selection path and exported bytes were verified. There were zero reported action errors or worker exceptions.

The fixed team population and candidate pool were informed by earlier results. Fresh seeds measure repeated-match robustness, while the varied generated suites add new sets. This does not establish superiority against an unknown tournament field. The league still contains only three policy families; stronger independent policies and further untouched tests remain useful.

Four diagnostic games outside this league reproduced a prior losing pair and tested a forced alternate opening. They are excluded from scores and independent strength evidence. The alternative still lost; see diagnostics/REPORT.md.

To reproduce, extract `dist/REDLINE_Diverse_League_Project_v1.zip` into a separate Windows directory; the promoted working tree no longer has the original v4.5 control inputs. In that directory, run `python tools/run_diverse_league.py --workers 6`, then `python tools/audit_diverse_league.py` and `python tools/summarize_diverse_league.py`. The manifest rejects changed policy or schedule inputs. An output-only Windows file-lock retry adapter is separately hashed and audited.

## Execution persistence diagnostic

The first four confirmation adaptive chunks were replayed with a fresh agent instance on every request. Opposing sets, seeds and sides were paired to the existing stateful cohorts. These 192 extra mode-check games do not change the frozen league score or selection.

| Build | Stateful wins | Fresh instance wins | Games per mode |
| --- | ---: | ---: | ---: |
| Dragonite/Dragapult/Arcanine | 77 | 75 | 96 |
| Dragapult/Snorlax/Corviknight | 92 | 94 | 96 |

Exact selected source checks passed: 55 Python tests, 2 JavaScript checks, and exported team-text consistency.

## Release

Promoted as v4.6; recommended artifact: dist/REDLINE_Search.zip. Versioned artifact: dist/REDLINE_Search_v4_6.zip.

## Practice compatibility check

The exact release source and team won one authorized practice battle against Sample Baseline in 8 turns (battle `sim-1792103224232`). The recorded upload hashes match this release. The replay shows one Iron Defense followed by Body Press, plus switches back to Dragapult. This checks service compatibility; a single sample-baseline win adds no reliable tournament-strength estimate and is excluded from the league score.
