# Original v4.6 submission audit

The original v4.6 package passes the current published submission contract.
This is a compatibility finding, not a claim that its approximate battle model
is free of errors or that it will win the tournament.

- Agent SHA256: `07b1e968db139b43ebf4dcf49900719977096ac42434d217f1f8534984183ac5`.
- ZIP SHA256: `c15f9c6ce60c6de0eb13ef2df05755d52ad109afcc54f4fa1b189012e69b864f`.
- Artifact: `dist/REDLINE_Search_v4_6.zip`.

## Current rules and package

Reviewed the [official docs](https://redline-aresxshunya.netlify.app/docs),
the current downloaded starter guide and the
[event submission requirements](https://unstop.com/hackathons/redline-ares-netaji-subhas-university-of-technology-nsut-delhi-1766284).
The live `/api/pokemon-options` data matches the previously archived options.

| Requirement | Finding |
| --- | --- |
| Exactly three permitted Pokémon | Dragapult / Snorlax / Corviknight; passed |
| Legal moves, ability, item, nature and EV preset | All three complete sets checked against current portal options |
| Python 3 class and decision method | `PokemonAgent.decide(self, observation)`; passed |
| Self-contained execution | Only `math` and `re`; no external model files, repository imports, file or network operations |
| Valid actions with original indices | Passed 288 varied isolated cases plus targeted contract fixtures |
| No blocking network calls or infinite loops | No such operations found; search depth and enemy candidate count are bounded |
| ZIP submission | Exactly `agent.py` and `team.txt` at archive root; bytes and hashes match |
| Team text describes the code's configured team | Verified by Showdown text parser and embedded OWN extraction |
| ZIP named after registered team | User will rename the release ZIP before submission |
| Turn limit | Existing model caps continuation at turn 100; local benchmark uses summed remaining HP percentages |

The exact ZIP agent imported successfully under `python -I -S` in an empty
temporary directory and returned legal actions in all 288 isolated cases.
The checked inputs and static data remained unchanged. The full suite passed
63 Python tests and both JavaScript checks. The public docs state no numeric
per-decision CPU or memory limit, so no undocumented limit is claimed.

The same exact source/team already won its authorized practice compatibility
test in eight turns, battle `sim-1792103224232`. Its recorded upload hashes
match this release. That prior sample-baseline game is not a strength estimate
and no new upload was performed for this audit.

## Confirmed forecasting defects

Official pinned Showdown 0.11.11 fixtures confirm these model discrepancies:

1. The original forecast does not remove Flying typing for the remainder of a
   turn after a successful Roost. This can incorrectly predict Ground immunity
   for a faster Roosting Corviknight.
2. A modeled Rest allows an attack one turn too early. Real Rest prevents
   attacks for the next two turns.
3. The original model creates sleep even for a full-HP Rest, which actually
   fails without inducing sleep.

These defects affect action evaluation, not the legality of the returned move
or the validity of the ZIP. Isolated recovery and combined-forecast candidates
correct the checked properties; their fresh battle study is under
`research/roster-forecast-v1`. Both completed the audit but failed their
predeclared release gates, so neither replaces the recommended release.

Unknown remaining sleep duration, two-turn attacks, pivot transitions, hidden
enemy sets/bench and several status effects remain approximations. Therefore
the audit does not certify an exact Pokémon simulator or a bug-free strategy.

The initial 4,752-game study retained original v4.6: recovery-only scored
740/864 confirmation wins versus 744/864 for control, and the merged roster
forecast scored 729/864. Neither passed its fixed release gate. See
`research/roster-forecast-v1/REPORT.md`. A separate, frozen follow-up adds an
explicit Phantom Force charge/invulnerability/strike sequence to the recovery
fixes; the original model instead averages its damage across turns. That
follow-up scored 741/864, compared with control's 744/864, and also failed its
predeclared release gates. Its paired weighted gain was -0.139 points with a
descriptive 95% interval of [-2.22, +2.36]. The original v4.6 remains the
recommended submission; see `research/phantom-forecast-v1/REPORT.md`.

One historical exact-action test is pinned to the archived v4.5 engine on its
original team: correcting Rest legitimately changes that old ranking. Recovery
mechanics themselves are checked against the official simulator, rather than
requiring the corrected model to reproduce the old mistaken forecast.

Re-run the compatibility check with
`python tools/audit_submission_readiness.py`. The full machine-readable proof
and observed timing values are in `audit.json`; the current starter and options
snapshots remain local beside this report.
