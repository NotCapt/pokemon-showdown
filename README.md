# REDLINE Search — v4.7

GitHub: [NotCapt/pokemon-showdown](https://github.com/NotCapt/pokemon-showdown).

The recommended release is `dist/REDLINE_Search.zip` (v4.7), also available as
`dist/REDLINE_Search_v4_7.zip`. Rename the ZIP to your registered team name
before submission. It contains exactly `agent.py` and `team.txt`.

`submission/agent.py`, `submission/team.txt`, `agent_core.py` and `team.json`
all describe this release. V4.6 is preserved in `archive/v4_6` and its versioned
ZIP; earlier releases and experiments remain available.

## V4.7: tactical search with Monte Carlo rollouts

V4.7 keeps the v4.6 team and adds up to 96 sampled continuations, each up to
six turns, when the tactical search has several promising choices. It samples
damage, accuracy, speed ties and plausible opponent sets, then blends the
rollout estimate with the original tactical score. Forced switches and late
turn-cap positions retain their existing handling.

A frozen four-build study completed 6,048 new games. The challenger selected
on validation won 800/864 independent confirmation games against the shared
opponent field, versus original v4.6's 746/864. Weighted scores were 91.84%
and 84.69%: a +7.153-point gain, with a descriptive paired 95% interval of
+2.15 to +12.95 points. Adaptive results improved from 357/384 to 368/384,
frozen league results from 201/288 to 245/288; tactical results slipped from
188/192 to 187/192. These are local field estimates, not tournament win odds.

The controlled timing sample measured 16.21 ms median and 84.03 ms p95 for
v4.7, compared with 11.78 ms and 27.96 ms for v4.6. Monte Carlo uses additional
CPU; the study does not compare equal compute budgets. A separate, broader
288-case isolated contract audit measured 30.14 ms median, 272.52 ms p95 and
529.93 ms maximum. These timings cover different workloads.

All four frozen sources pass 63 Python tests and both JavaScript checks.
The exact v4.7 ZIP passes team legality, two-file layout and isolated execution
checks, and won its authorized practice compatibility battle in eight turns.
That single sample-baseline game is excluded from the strength estimates.

This is bounded Monte Carlo rollout search with an approximate battle model.
It retains v4.6's Roost/Rest forecasting limitations. Hidden enemy bench,
voluntary future enemy switches and several continuation details remain
unmodeled. The separately tested recovery/Phantom Force variant was not the
validation-selected challenger. See [the full report](research/monte-carlo-v1/REPORT.md)
and [the frozen protocol](research/monte-carlo-v1/PROTOCOL.md).
`dist/REDLINE_Monte_Carlo_Project_v1.zip` contains the frozen inputs, every
battle result and the reproducible audit tools.

## V4.6: team selected against a diverse opponent league

V4.6 selects Dragapult / Snorlax / Corviknight using the unchanged v4.5
decision engine. Twenty-five builds competed against fresh generated sets
under adaptive and tactical policies, plus twelve frozen teams covering all
24 allowed species and all three cyclic lead choices. The former incumbent
contributes only 3.33% of the weighted score, and the weakest-category scoring
term has been removed.

On independent confirmation, the selected build won 739/864 games versus
v4.5's 648/864. Weighted scores were 83.26% versus 72.64%: a +10.625-point
gain with a descriptive paired 95% interval of +3.68 to +18.23 points.
All three categories improved: adaptive 370/384 versus 331/384, tactical
188/192 versus 169/192, and the frozen league 181/288 versus 148/288.
These results describe this experimental league, not tournament win odds.

All 8,856 scheduled games and 1,362 reports passed the source/schedule audit.
The exact selected source passes 55 Python tests, both JavaScript checks and
team-text consistency. A matched fresh-instance diagnostic scored 94/96
versus v4.5's 75/96; those extra games are separate from the league score.
The exact release also won its authorized practice compatibility test in eight
turns. That single Sample Baseline game is excluded from the strength estimates.
See [the v4.6 report](research/V4_6_REPORT.md) and
[the frozen protocol](research/DIVERSE_LEAGUE.md).

`dist/REDLINE_Diverse_League_Project_v1.zip` preserves the exact Windows
campaign inputs, compiled agents and schedules. Extract it into a separate
directory to reproduce the study with its original v4.5 control. The full
results and audit records remain in `research/diverse-league-v1` locally.

## Historical v4.6 audit and policy experiments

The current docs, starter guide, event ZIP requirements and live roster options
were checked on 16 October 2026. The original v4.6 ZIP passes the format,
team-text, legality and standalone Python contract checks, including 288 isolated
legal-action cases, the expanded 63 Python checks and both JavaScript checks.
Rename the ZIP to your registered team name before submitting it.

The audit found recovery-model inaccuracies in Roost typing, Rest timing and
full-HP Rest. A 4,752-game frozen study tested corrected recovery and whole-team
forecasts. Neither passed its release gate, so those experiments retained v4.6. A separate
1,296-game temporal follow-up models Phantom Force charging and invulnerability.
Its controls are shared with the first study and are not counted again.
Those experiments did not establish a stronger submission; the later Monte Carlo
study above selected v4.7.

See [the submission audit](research/readiness-v4_6/REPORT.md),
[the recovery/roster study](research/roster-forecast-v1/REPORT.md), and
[the temporal follow-up](research/phantom-forecast-v1/REPORT.md).
The original source and team are also preserved in `archive/v4_6`.
`dist/REDLINE_Forecast_Audit_Project_v1.zip` preserves the frozen experiment
inputs, all 6,048 result records and verification tools. Extract it into a
separate directory to audit or rerun the studies. It is a research package;
the preserved competition artifact for that study is `dist/REDLINE_Search_v4_6.zip`.

## V4.5: combined policy and physical Dragapult

V4.5 uses the teammate's Choice Band / Clear Body / Adamant Dragapult set and
keeps v4.4's hazard, Choice-lock, reserve-preservation and turn-cap mechanics.
Read-only move definitions, cached item multipliers, speed/accuracy hoisting
and a preview memory reset incorporate the teammate's implementation improvements.

In a frozen, fresh 4,512-battle comparison, the combined bot scored 770/960
against common opponents, versus teammate 758/960 and original v4.4 718/960.
It beat v4.4 directly 163-93 and tied the teammate 128-128. The paired league
gain versus the teammate was 1.25 percentage points, with a descriptive clustered
95% interval of +0.21 to +2.50 points. These are local league results, not a
tournament win probability. Original v4.4 still won more games on the mixed
schedule (143/192 versus 138/192), so the change has matchup tradeoffs.

The exact packaged source won its authorized practice smoke test in five turns.
All 52 Python tests and both JavaScript tests pass. Historical policy fixtures
explicitly retain their archived team config. V4.4 is preserved in
`archive/v4_4`. See `research/V4_5_REPORT.md` for the aggregate comparison,
validation results and exact release hashes.

## V4.4: entry damage from public observations

V4.4 learns plausible Stealth Rock and Spikes states from HP changes immediately
after a faint replacement. It then charges entry damage to switch forecasts,
including entries that faint before they can act. Pivot entries are excluded
because another attack can still be queued. Ambiguous observations retain
multiple possible field states and use the minimum shared damage estimate.

The model matches 384 official-simulator entry-damage fixtures. A controlled
last-turn position now avoids a lethal Arcanine entry and preserves 48.73 more
summed HP points; that position still loses. Across 432 matched ordinary and
stateless battles, all outcomes matched v4.3.2. The exact v4.4 source won
its practice test in six turns. This is a scoped forecasting improvement, with
no measured aggregate win-rate gain. See `research/V4_4_REPORT.md` and
`research/v4_4-summary.json` for evidence, rejected experiments and limitations.

## Parallel Kaggle campaign: frozen v4.3.2

Three private CPU notebooks screen disjoint portions of all 2,024 species trios:
[screen 1](https://www.kaggle.com/code/faaizhussain/redline-pokemon-screen-1-v4-3-2),
[screen 2](https://www.kaggle.com/code/faaizhussain/redline-pokemon-screen-2-v4-3-2),
[screen 3](https://www.kaggle.com/code/faaizhussain/redline-pokemon-screen-3-v4-3-2).
The [final comparison](https://www.kaggle.com/code/faaizhussain/redline-pokemon-final-comparison-v4-3-2)
combines completed screen outputs and evaluates finalists together. Each screen
uses a six-hour checkpoint limit and 30,000-game budget. The first screening
round uses eight games per policy; remaining HP breaks tied scores. See
`research/PARALLEL_SEARCH.md` for running, resuming and merging results.

This campaign remains pinned to `archive/v4_3_2` and its original bundle hash
while the recommended release advances. Regenerating its notebooks preserves
that source. Any team emerging from the campaign needs a new comparison using
the latest agent before promotion.

All three screens completed: 77,700 battles covered all 2,024 default species
trios and produced 18 finalists. The compact exports passed source-hash and
coverage checks. The private final comparison completed as version 5, with
the verified compact exports included directly in
`notebooks/REDLINE_Final_Comparison_Completed_Screens.ipynb`. A separate local
campaign evaluated those finalists against the v4.5 incumbent using the frozen
v4.5 engine; old cloud scores were not reused as latest-engine results.

Both final comparisons completed 5,040 battles, bringing campaign work to
87,780 battles. The latest-engine challenger, Dragapult/Tyranitar/Corviknight,
won 188/192 directly against v4.5, but fell from 173/192 to 162/192 against the
varied adaptive opponents. That 5.73-point regression failed the predeclared
five-point limit, so that earlier comparison retained v4.5. The alternate is preserved
as `dist/REDLINE_Kaggle_Challenger_v4_5.zip`. See
[the completed results](research/KAGGLE_RESULTS.md) for both experiments,
audits and the next direction. The cloud winner uses the older engine and is
not promoted.

V4.3.2 corrects Sucker Punch forecasts on switches and after earlier actions.
Three official-simulator fixtures confirm the mechanics. Across 488 matched
benchmark battles it retained v4.3.1 outcomes; this is a correctness improvement,
with no measured overall win-rate gain. The exact artifact won its practice
test in five turns. See `research/V4_3_2_REPORT.md`. V4.3.1 is archived in
`archive/v4_3_1` and remains available as a versioned ZIP.

## Previous single-notebook search and v4.3.1

[Open the previous private Kaggle notebook](https://www.kaggle.com/code/faaizhussain/redline-pokemon-team-search-v4-3-1).
Use CPU, enable Internet and Run All. Quick mode is the default; full mode screens
all 2,024 species trios before mutating survivor sets. Checkpoints support resume.
The local notebook is `notebooks/REDLINE_Team_Search.ipynb`.

V4.3.1 reduces repeated stat construction in chance branches. A paired local check
measured 1.10x throughput with identical actions and memory on 960 observations;
392 benchmark battles retained v4.3 results. This is a speed improvement, not a
proven win-rate increase. See `research/V4_3_1_REPORT.md`. V4.3 is archived in
`archive/v4_3`; the historical results below describe v4.3.

## What improved

V4.3 adds a cost when a voluntary switch is predicted to lose a reserve before
it acts. The cost scales with remaining HP, preserving weak-reserve sacrifice
plays. Forced replacements and the final summed-HP objective are unaffected.
It also fixes continuation forecasts that could escape a Choice lock when the
locked move was absent from the enemy's default set.

A saved loss demonstrates the change: Arcanine stays in and uses Play Rough
against Salamence, preserving a full-health Dragapult. The associated
side-reversed development pair changes from two losses to two wins.

The broader post-knockout forecast was slower and did not improve development
results, so it remains in research. The previous Close Combat team and Explosion
experiments remain experimental. See `research/V4_3_REPORT.md` for current
results, tradeoffs and reproduction details.

## Selected team

| Pokémon | Item / ability | Nature / EVs | Moves |
| --- | --- | --- | --- |
| Dragapult | Choice Band / Clear Body | Jolly, 252 Atk / 252 Spe / 4 SpD | Dragon Darts, Phantom Force, Flamethrower, U-turn |
| Snorlax | Leftovers / Thick Fat | Careful, 252 HP / 252 SpD / 4 Def | Body Slam, Earthquake, Crunch, Rest |
| Corviknight | Leftovers / Mirror Armor | Impish, 252 HP / 252 Def / 4 SpD | Brave Bird, Body Press, Roost, Iron Defense |

Configure this exact team in the practice portal. Uploading the Python file
does not configure the team. Rebuild after changing `team.json` so the agent's
own-team knowledge matches.

## Results and limits of the evidence

| Matched schedule | V4.3 | V4.2 |
| --- | ---: | ---: |
| Fresh adaptive opponent, 32 custom teams | 166/192 | 160/192 |
| Fresh mixed simple policies | 167/200 | 169/200 |
| Original six customized tactical teams | 59/60 | 59/60 |
| Fresh instance each turn, missing boosts | 31/40 | 31/40 |

V4.3 also tied archived v4.1 directly, 40-40. Its exact source completed 572
simulator games with legal actions and no worker exceptions. The improvement
is modest and varies by opponent mix: the fresh adaptive gain is +3.125 points
with a team-cluster 95% interval of -2.08 to +8.33, while fresh mixed play lost
two games. These results do not establish statistical or tournament-wide
superiority. V4.2 remains a fallback.

All 31 Python tests and two JavaScript checks pass. The authorized v4.3 portal
smoke test won in seven turns. The packaged source is byte-for-byte identical
to the tested candidate. Local timings depend on hardware and concurrent load;
selected runs had medians around 30-37 ms.

The full research pass includes 3,384 games across candidates and controls,
with repeated teams and reused schedules. That total must not be treated as
independent evidence or a tournament win probability. Earlier reports retain
their historical comparisons. If execution changes to create a fresh instance
every turn, v3 remains the better tested fallback on the old stateless suite.

## Interface and strategy

The standalone Python file defines `PokemonAgent.decide(self, observation)` and
requires only Python's standard library. It makes no network calls, filesystem
reads, subprocess calls or model downloads. It returns legal indexed moves,
switches and the team-preview ordering.

The policy enumerates legal moves/switches and possible enemy attacks, branching
on first-turn hit/miss events, flinches and three damage rolls. Root speed ties
branch in both orders. Two greedy continuation turns estimate consequences. The
score blends expected outcomes with a penalty for the worst modeled reply,
rewarding knockouts, HP preservation and useful boosts. This is an approximate
bounded search, not a full simulator or equilibrium solver.

The portal diagnostic found missing/empty boosts, stats and PP in the tested
observations, but preserved instance memory. The agent remembers estimated own
boosts and resets them on switching. Attempts are not confirmed outcomes: a
failed setup or missed stat-dropping attack can still mislead this estimate.

## Reproduce

From this directory, Python 3.10+ and Node 20+:

```powershell
npm.cmd ci --omit=optional
node tools/export_data.js
python tools/build_agent.py
python -m unittest discover -s tests -v
$env:SEED='61979'
$env:SPARSE='1'
$env:REPORT='research/reproduction-v4_2-mixed.json'
node tools/benchmark.js 200
python tools/package_submission.py
```

Use a fresh terminal for each benchmark configuration, or clear previous test
environment variables. `AGENT_FILE` selects an archived agent, `TEAM_FILE` its
team, `OPP_TEAM_FILE` a fixed opposing team, and `CUSTOM` a JSON list of opposing
teams. `OPPONENT` supports `v1`, `v2`, `v3`, `v4`, `v4_1`, `tactical`, `search`, `power`, `stab` and
`random`. `SPARSE=1` removes boosts; `STATELESS=1` discards agent memory.

For reproducible evaluation without inherited environment settings:

```powershell
npm.cmd test
python tools/verify_release.py
node tools/check_cap_scenario.js submission/agent.py research/v4_3-cap-scenario.json
python tools/run_eval.py --seed 44017 --games 192 --suite research/eval-holdout-teams.json --report research/my-holdout.json
python tools/compare_reports.py --candidate research/my-holdout.json --control research/v4_1-adaptive-holdout.json --out research/my-comparison.json
```

The independent `adaptive` opponent knows its own exact set and state. It uses
only public enemy species, types and rounded HP, with curated defaults for the
enemy's hidden set. It can switch, set up and recover, but remains a heuristic
baseline, not a proven strong tournament opponent. `--policy mixed` runs the
earlier power/STAB/tactical schedule; `--stateless` disables instance memory.
GitHub Actions runs release tests, opponent isolation checks and ZIP verification.

`tools/build_agent.py --team research/team-v4-arcanine.json --out research/test-build`
builds a separate candidate without overwriting the main submission.
`tools/package_submission.py --name MyTeam` creates `dist/MyTeam.zip`.
`tools/portal_test.py` performs a real practice upload, sharing the generated
agent and team with the organizers' service. Its `--probe` flag is an old
diagnostic, not part of the submission. No final entry has been submitted.

## Limits and competition rules

Unknown enemy sets use defaults and coverage hypotheses. Enemy switches,
hazards, many volatile effects, secondary effects, status durations and several
multi-turn moves remain approximate or unmodeled. Later continuation accuracy
and speed ties are approximate. The 100-turn HP objective is evaluated locally,
not with a complete future team model. No numerical service response-time limit
was found in the reviewed public rules; local timings are not a service SLA.

Reviewed 15 October 2026: Gen 9 singles, exactly three PokÃ©mon from the curated
24-species roster, up to four permitted moves with item/ability/nature/EV
customization. Maximum 100 turns, then summed remaining HP-percentage tiebreak.
One or two people per team; autonomous legal decisions, no manual intervention
during a match. Heuristics are permitted; ML is not mandatory. Submit a ZIP named
after the registered team containing PokÃ©mon `.txt` and algorithm `.py` files.

Registration closes **16 October 2026, 12:59 PM IST**. Phase 1 submissions close
**16 October 2026, 11:59 PM IST**. Offline round: **17 October 2026, noonâ€“5 PM
IST**, APJ Lecture Theatre, NSUT main campus, Dwarka. Check organizer updates for
any later restrictions or format changes.

Sources: [event listing](https://unstop.com/hackathons/redline-ares-netaji-subhas-university-of-technology-nsut-delhi-1766284),
[practice portal](https://redline-aresxshunya.netlify.app/),
[technical docs](https://redline-aresxshunya.netlify.app/docs),
[live options](https://redline-aresxshunya.netlify.app/api/pokemon-options).
Public starter files and options are saved under `research/`.

Battle mechanics data derive from PokÃ©mon Showdown 0.11.11. Its MIT license is
embedded in the agent and saved in `research/SHOWDOWN_LICENSE.txt`. Experimental
`enemy_sets` data in the generated file are not used as live inference by v4.3.
