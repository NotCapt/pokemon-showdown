# REDLINE Search — v4.1

The recommended release is `dist/REDLINE_Search.zip` (v4.1). Rename the ZIP to
your registered team name before submission. It contains exactly `agent.py` and
`team.txt`. The same release is also available as `dist/REDLINE_Search_v4_1.zip`.

`submission/agent.py`, `submission/team.txt`, `agent_core.py` and `team.json` all
describe this release. Prior versions are preserved in `archive/v1` and
`archive/v2`, `archive/v3` and `archive/v4`. V3 and v4 remain available as versioned ZIPs.

## What improved

V4.1 tracks opposing Intimidate entries when the portal omits boosts, avoids
counting the same entry again, and respects explicit boost observations.
It also models Protean's once-per-switch type change in continuation search,
using observed types to recognize an already transformed Greninja.

The same team and bounded search remain in use. More exact damage arithmetic
and a sixteen-roll search were investigated but did not improve the tested
battle results enough to include. See `research/V4_1_REPORT.md`.

V4 replaces Corviknight with **Assault Vest Arcanine**, combining special bulk,
Intimidate, Fire resistance and strong physical coverage. Choice Band Dragonite
and Choice Specs Dragapult retain their previous configurations.

V4 retains the previous search and additionally branches on first-turn flinches,
so a flinch cancels the entire reply, including healing, setup and recoil. It
models Intimidate immunities and Mirror Armor reflection, and remembers expected
entry effects when the portal omits boost telemetry. Enemy-belief and switch
prediction experiments were tested but were not selected for this release.

## Selected team

| Pokémon | Item / ability | Nature / EVs | Moves |
| --- | --- | --- | --- |
| Dragonite | Choice Band / Multiscale | Adamant, 252 Atk / 252 Spe / 4 SpD | Extreme Speed, Earthquake, Ice Spinner, Fire Punch |
| Dragapult | Choice Specs / Infiltrator | Timid, 252 SpA / 252 Spe / 4 SpD | Shadow Ball, Draco Meteor, Flamethrower, Thunderbolt |
| Arcanine | Assault Vest / Intimidate | Adamant, 252 HP / 252 Atk / 4 SpD | Flare Blitz, Extreme Speed, Crunch, Play Rough |

Configure this exact team in the practice portal. Uploading the Python file
does not configure Pokémon, moves or items. This release is tuned to this team.
After changing `team.json`, rebuild the agent so its own-team knowledge matches.

## Results

| Matched test | V4.1 wins | V4 wins |
| --- | ---: | ---: |
| Mixed simple policies, development seed | 125/160 | 123/160 |
| Mixed simple policies, fresh holdout seed | 151/200 | 145/200 |
| Six customized teams, tactical policy | 59/60 | 59/60 |
| Fresh agent each decision, missing boosts | 31/40 | 31/40 |

All 460 v4.1 games completed with legal actions. Twenty-three release tests passed.
Local median decision time was approximately 8–18 ms; p95 was 34–57 ms across
these runs. The latest actual portal smoke test won in six turns. Local timing
depends on hardware and concurrent load.

The holdout gain is modest: +3 percentage points, with a paired bootstrap 95%
interval of 0 to +7 points. Development includes one regressed game. These
simple opponents do not establish performance against strong independent bots.

V3 scored 56/60 on the same custom suite but 38/40 on the same stateless schedule.
V4 is preferred for the tested portal, which preserved agent instances. If the
organizers change execution to create a fresh instance every turn, v3 is the
better tested fallback. V4 is not uniformly better across all conditions.

This is evidence of improvement over our saved submissions, not a tournament
win probability. The saved agents share our modeling assumptions, and the
tactical policy is simpler than a strong independent competitor. See
`research/V4_1_REPORT.md` for current evidence and `research/V4_REPORT.md` for
historical v4 benchmarks against the saved agents.

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
$env:REPORT='research/reproduction-v4_1-mixed.json'
node tools/benchmark.js 200
python tools/package_submission.py
```

Use a fresh terminal for each benchmark configuration, or clear previous test
environment variables. `AGENT_FILE` selects an archived agent, `TEAM_FILE` its
team, `OPP_TEAM_FILE` a fixed opposing team, and `CUSTOM` a JSON list of opposing
teams. `OPPONENT` supports `v1`, `v2`, `v3`, `v4`, `tactical`, `search`, `power`, `stab` and
`random`. `SPARSE=1` removes boosts; `STATELESS=1` discards agent memory.

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

Reviewed 15 October 2026: Gen 9 singles, exactly three Pokémon from the curated
24-species roster, up to four permitted moves with item/ability/nature/EV
customization. Maximum 100 turns, then summed remaining HP-percentage tiebreak.
One or two people per team; autonomous legal decisions, no manual intervention
during a match. Heuristics are permitted; ML is not mandatory. Submit a ZIP named
after the registered team containing Pokémon `.txt` and algorithm `.py` files.

Registration closes **16 October 2026, 12:59 PM IST**. Phase 1 submissions close
**16 October 2026, 11:59 PM IST**. Offline round: **17 October 2026, noon–5 PM
IST**, APJ Lecture Theatre, NSUT main campus, Dwarka. Check organizer updates for
any later restrictions or format changes.

Sources: [event listing](https://unstop.com/hackathons/redline-ares-netaji-subhas-university-of-technology-nsut-delhi-1766284),
[practice portal](https://redline-aresxshunya.netlify.app/),
[technical docs](https://redline-aresxshunya.netlify.app/docs),
[live options](https://redline-aresxshunya.netlify.app/api/pokemon-options).
Public starter files and options are saved under `research/`.

Battle mechanics data derive from Pokémon Showdown 0.11.11. Its MIT license is
embedded in the agent and saved in `research/SHOWDOWN_LICENSE.txt`. Experimental
`enemy_sets` data in the generated file are not used as live inference by v4.1.
