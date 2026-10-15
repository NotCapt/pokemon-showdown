# REDLINE Search — v4.3.2

GitHub: [NotCapt/pokemon-showdown](https://github.com/NotCapt/pokemon-showdown).

The recommended release is `dist/REDLINE_Search.zip` (v4.3.2), also available as
`dist/REDLINE_Search_v4_3_2.zip`. Rename the ZIP to your registered team name
before submission. It contains exactly `agent.py` and `team.txt`.

`submission/agent.py`, `submission/team.txt`, `agent_core.py` and `team.json`
all describe this release. V4.2 is preserved in `archive/v4_2` and its versioned
ZIP; earlier releases and experiments remain available.

## Parallel Kaggle search and v4.3.2

Three private CPU notebooks screen disjoint portions of all 2,024 species trios:
[screen 1](https://www.kaggle.com/code/faaizhussain/redline-pokemon-screen-1-v4-3-2),
[screen 2](https://www.kaggle.com/code/faaizhussain/redline-pokemon-screen-2-v4-3-2),
[screen 3](https://www.kaggle.com/code/faaizhussain/redline-pokemon-screen-3-v4-3-2).
The [final comparison](https://www.kaggle.com/code/faaizhussain/redline-pokemon-final-comparison-v4-3-2)
combines completed screen outputs and evaluates finalists together. Each screen
uses a six-hour checkpoint limit and 30,000-game budget. The first screening
round uses eight games per policy; remaining HP breaks tied scores. See
`research/PARALLEL_SEARCH.md` for running, resuming and merging results.

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
| Dragonite | Choice Band / Multiscale | Adamant, 252 Atk / 252 Spe / 4 SpD | Extreme Speed, Earthquake, Ice Spinner, Fire Punch |
| Dragapult | Choice Specs / Infiltrator | Timid, 252 SpA / 252 Spe / 4 SpD | Shadow Ball, Draco Meteor, Flamethrower, Thunderbolt |
| Arcanine | Assault Vest / Intimidate | Adamant, 252 HP / 252 Atk / 4 SpD | Flare Blitz, Extreme Speed, Crunch, Play Rough |

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
