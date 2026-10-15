# v4.3.1: faster simulation and Kaggle team search

The recommended ZIP uses the same team and decision policy as v4.3. The change
builds a switch-in Pokemon once per action, then clones its mutable state for
each chance branch. Move accuracy is also computed outside the chance loop.

`research/d-fast-equivalence.json` records identical actions **and internal
memory** on 960 public observations from 96 games. Alternating execution order
gave 19.800 seconds for v4.3 and 17.983 seconds for v4.3.1: 1.101x throughput
(9.2% less elapsed time). This is one local timing run, not a universal speedup.

The exact generated candidate retained 166/192 wins on the adaptive schedule
and 167/200 on mixed policies. These are reused schedules and establish no new
win-rate advantage. Source SHA256:
`eb72fe28329b3bb377ccefcb908a3778f003b51c0ecd4adc88365d368d362037`.
The previous v4.3 portal test applies to the previous artifact; v4.3.1 has been
tested locally, not uploaded to the practice portal in this pass.

All 33 Python tests and 2 JavaScript checks passed. The new search smoke run
completed 78 battles, tested the frozen v4.3 opponent, exported a legal
two-file ZIP with matching compiled team knowledge, and resumed entirely from
cache without additional battles. Smoke results are not team-quality evidence.

## Kaggle

`notebooks/REDLINE_Team_Search.ipynb` embeds a checksummed minimal source bundle.
It installs the pinned Showdown dependency and an official Node runtime when
needed. CPU only, Internet enabled. It never submits to the competition.

Quick mode starts with 48 teams; full mode starts with all 2,024 species trios
plus the exact incumbent. Full mode does not enumerate all sets or all orders.
Subsequent mutation explores species, moves, items, abilities, natures, EVs and
order. Aggressive early elimination is a compute tradeoff and can miss strong
teams. The three-policy league is not representative of every opponent.

Development, validation and confirmation use separate seeds and generated
opponent teams. Only one challenger selected on validation reaches confirmation.
The frozen incumbent opponent necessarily uses the same team in every phase.
Rankings use 70% mean policy score plus 30% worst policy score, with draws
counting half. Export selection is exploratory, not a significance test.

Completed jobs are cached with source/configuration/suite fingerprints. Changing
search inputs requires a fresh output directory. Time and battle limits pause
work; rerunning identical inputs resumes. The checkpoint ZIP can be attached as
a Kaggle dataset to continue in a later session. Increase limits as necessary.

Run locally: `python tools/team_search.py --profile quick --out runs/search`.
For all trios use `--profile full`. Start with `--profile smoke` to check setup.
Results remain separate from the recommended submission pending review.
