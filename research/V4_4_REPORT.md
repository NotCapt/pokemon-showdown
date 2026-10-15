# v4.4: observing entry damage without field telemetry

The recommended archive is dist/REDLINE_Search.zip, also versioned as
dist/REDLINE_Search_v4_4.zip. The selected three Pokemon, moves, items, EVs,
natures and ordering are unchanged. V4.3.2 is archived for comparison and for
the currently running distributed Kaggle campaign.

Selected agent SHA256:
`480295eec4620074c6665f4aab1ea8ea9773ee42a01f6797d930c5a017fed923`.

## Included behavior

The portal does not provide field hazards. The agent now remembers the HP of
a chosen replacement after its active Pokemon faints, then compares that HP
with the next observation of the entrant. It enumerates eight possible field
states: Stealth Rock present/absent and zero to three Spikes layers. Integer
damage flooring and a one-HP observation tolerance are included.

Only damage compatible with every retained state is charged to future entries.
A Flying entrant can establish Rock damage but cannot establish the number of
Spikes layers. A neutral entrant may not distinguish Rock from one Spikes layer.
Boots, Magic Guard, Flying and Levitate exemptions are respected. A lethal
observed entry supplies a lower bound, not an exact damage amount. Missing HP,
stale or mismatched species observations are ignored. An incompatible new
observation replaces the old hypothesis rather than retaining contradicted
field information. Living pivot replacements are not used for inference:
another attack may still target the entrant before the next observation.

Forecasts subtract entry damage before Intimidate and the opposing attack. A
Pokemon that faints on entry cannot activate Intimidate or attack. A voluntary
switch still spends the turn, including opposing Leftovers healing; a forced
entry does not spend a turn. Unknown fields retain the previous zero-entry-cost
assumption until there is usable evidence.

## Evidence

tools/hazard_oracle.js generated 384 actual-engine fixtures: 24 allowed species,
two Rock states, four Spikes levels and Boots present/absent. The candidate's
predictions match every fixture. These compare direct entry damage, not full
battle play. Magic Guard and Levitate also receive separate Python checks.

The controlled actual-engine scenario in v4_4-hazard-scenario.json uses the
equipped team, a real Choice lock and a consistent sparse public history:
Dragapult has fainted; Dragonite's earlier forced entry establishes Rock damage.
At turn 100, Dragonite is at 96/323 HP, locked into Earthquake against a Flying
Corviknight. Arcanine has 92/384 HP and would die to Rock damage on entry.
Corviknight uses Roost. V4.3.2 switches Arcanine in, loses it, then pays another
entry cost bringing Dragonite back. V4.4 stays in. Actual final own summed HP
improves from 4.95 to 53.68 points. Both versions lose this deliberately adverse
position; it is an HP-preservation fixture, not a loss-to-win conversion.

An earlier synthetic test was discarded because its history resurrected a
previously fainted member. Its apparent win conversion is not release evidence.
The replacement verifies fainted-member consistency and real move legality.

| Exact released artifact schedule | v4.4 | v4.3.2 |
| --- | ---: | ---: |
| Adaptive, 32 custom teams, seed 49937 | 146/192 | 146/192 |
| Mixed policies, seed 40259 | 150/200 | 150/200 |
| Fresh agent each request, tactical, seed 83729 | 30/40 | 30/40 |

All 432 paired outcomes matched and had no illegal actions or worker exceptions.
These ordinary policies rarely exercise hazard-setting play. Unchanged results
are a regression check; they do not prove that the new hazard inference improves
an overall tournament win rate. Selected median times were about 16-18 ms and
p95 about 48-49 ms on this machine; timings vary with load.

All 52 Python tests and both existing JavaScript tests pass. The actual-engine
turn-cap scenario still selects Roost and wins its original HP tiebreak. The
exact released artifact won the authorized practice test in six turns, battle
sim-1792095027235. Source/team hashes and replay are retained; the extracted
log contains no invalid-action, error or fallback markers. This is only a smoke
test against the sample opponent. No final competition entry was submitted.

tools/summarize_v4_4.py checks source hashes, the exact compiled team, paired
opponent schedules, zero errors, scenario consistency and portal provenance.
tools/verify_release.py checks the packaged bytes and manifest.

To reproduce the focused checks, run `npm test`, `node tools/hazard_oracle.js`,
`python tools/check_hazard_oracle.py`, `node tools/check_hazard_scenario.js`,
`python tools/summarize_v4_4.py` and `python tools/verify_release.py`.
The retained f-hazards prototype and its reports precede the final pivot and
residual-turn guards. tools/prepare_f_hazards.py reproduces the released model;
running it replaces the prototype core rather than reproducing those older
prototype reports.

## Research candidates left out

Independent damage rolls in each first-turn exchange tied the control at
83/96 on development and used roughly three times the decision time. It stays
experimental. This does not establish that shared rolls are accurate, only
that this broader tree did not justify its cost on this development schedule.

A priority-preserving opponent shortlist also tied 83/96. Adding a low-weight
alternative attacking build tied again. A subsequent fixed 20% alternative-set
mixture scored 87/96 and recovered two side-reversed Lapras matchups, but did
not retain the improvement consistently:

| Priority mixture schedule | Candidate | Control |
| --- | ---: | ---: |
| Development custom | 87/96 | 83/96 |
| Separate validation custom | 170/192 | 172/192 |
| Validation mixed | 173/200 | 169/200 |
| Final confirmation custom | 142/192 | 146/192 |
| Final confirmation mixed | 147/200 | 150/200 |

The mixture is not included. The confirmation schedules were not used to tune
its prior afterward. A refactor matched its actions and memory on 859 public
observations, but equivalence does not establish strength. The prototype,
reports and research-only tests remain available.

Changing only the lead to Dragapult scored 80/96; leading Arcanine scored
82/96, versus the existing Dragonite lead's 83/96 on the matched development
suite. Both reordered teams were compiled into their exact agent; neither is
promoted. These tests do not exhaust all possible team configurations.

## Kaggle and limits

The three running screen notebooks and final comparison stay on the original
v4.3.2 bundle hash:
`a6ac61f80989e32d6d2319476718c4019a5af66d3c25564a375aa695a41652af`.
The notebook builder now explicitly reads the frozen v4.3.2 core/team and the
verifier rejects accidental campaign source changes. A versioned source bundle
is saved as dist/REDLINE_Kaggle_Project_v4_3_2.zip. The final campaign winner must
be recompiled and compared with v4.4 before replacing the selected team.

Hazards first placed or removed between clean observations can remain unknown
or stale. The agent does not infer them from voluntary entries, because incoming
attacks and residual damage can be indistinguishable. Hidden own item changes,
unusual max-HP configurations and some volatile effects remain approximate.
The agent also retains its existing limitations around opposing switches,
hidden sets and continuation after knockouts. V4.3.2 remains a fallback.
