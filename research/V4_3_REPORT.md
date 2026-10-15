# V4.3: reserve risk and persistent Choice locks

Recommended artifact: `dist/REDLINE_Search.zip`, also saved as
`dist/REDLINE_Search_v4_3.zip`. Team and lead ordering are unchanged. V4.2 is
preserved in `archive/v4_2` and `dist/REDLINE_Search_v4_2.zip`.

This is a small policy revision with a concrete forecast correction. It has
modest positive evidence against switching opponents, one regressed fresh
simple-policy schedule, and no demonstrated statistical or tournament-wide
dominance. The recommendation is a judgment in favor of avoiding costly
reserve losses, not a claim that every matchup improves.

## Included changes

### Price a reserve that faints on entry

Previously a voluntary switch that died to the incoming attack could score
well relative to staying in, despite losing a reserve without getting an
action. The existing HP/KO accounting does price some of that loss; it does
not fully represent the lost future team options.

V4.3 adds a cost of half the reserve's starting HP percentage only in forecast
branches where it faints on the immediate switch-in hit. Hit/miss and move
uncertainty retain their existing probabilities. A weak reserve remains a
possible sacrifice; this is not a hard ban on sacrifice plays. Forced
replacements do not receive this penalty. Turns 98-100 retain the summed-HP
objective without this additional cost.

A saved public-observation fixture shows the practical change: on turn 4,
Arcanine is at about 76%, enemy Salamence at 68%, and Dragapult at full HP.
V4.2 switches Dragapult in; v4.3 stays with Arcanine and chooses Play Rough.
The associated development pair (games 38/39) changes from two losses to two
wins in actual Showdown. The fixture includes the observation history, so its
estimated boosts and memory are reproduced rather than fabricated.

### Preserve nondefault Choice locks

An enemy coverage hypothesis can use a legal move absent from its curated
default moves. The old continuation filtered the default move list by the
Choice lock, then fell back to the full default list if nothing matched. That
incorrectly allowed the predicted enemy to change moves.

The continuation now retrieves the locked move directly from the static Dex.
An actual Showdown test uses Choice Band Metagross with Thunder Punch into
Protect. Both the real request and the corrected model stay locked to Thunder
Punch, including when the next modeled target is immune. Returning to a new
entry clears the forecast's lock state as before.

## Exact released-artifact evidence

The frozen candidate `research/c-final/agent.py` and `submission/agent.py` are
byte-for-byte identical. SHA256:
`f44eb69614d6b551e008c3023b8a0d7a1ca93c94b63bd5ed5ed2fefa16a81067`.

| Matched schedule | V4.3 | V4.2 reference |
| --- | ---: | ---: |
| Fresh adaptive opponent, 32 custom teams, seed 24683 | 166/192 | 160/192 |
| Fresh mixed power/STAB/tactical, seed 90677 | 167/200 | 169/200 |
| Original six customized tactical teams, seed 42817 | 59/60 | 59/60 |
| Stateless tactical, seed 64513 | 31/40 | 31/40 |

The fresh adaptive gain is +3.125 percentage points, with a whole-team-cluster
bootstrap 95% interval of -2.08 to +8.33 points. It contains eight improved and
two regressed games. The fresh mixed change is -1 point, interval -2.5 to 0,
with zero improvements and two regressions. Those regressions are STAB-policy
games against Dragonite / Ferrothorn / Snorlax and Gengar / Togekiss / Dragonite.
The intervals do not establish overall superiority. No tuning followed these
fresh confirmation results.

An additional direct comparison against archived v4.1 on its exact equipped
team tied 40-40. All 572 exact-artifact simulator games completed with legal
actions and no worker exceptions. These include repeated teams and reused
regression suites, not 572 independent trials.

The actual turn-cap counterexample still passes: Roost wins the HP tiebreak
that the archived v4.1 knockout loses. The case remains a legal alternate-team
fixture using Corviknight, not a full game with our selected three Pokémon.
V4.3 provenance is in `v4_3-cap-scenario.json`; the v4.2 evidence remains intact.

The authorized portal smoke test won in seven turns, battle
`sim-1792089334996`. Source and exact team hashes are recorded in
`v4_3-portal-result.tested.json`; result, replay and extracted log are preserved.
No invalid/error/fallback strings were found in the replay log. This does not
prove that the service never silently falls back. No final entry was submitted.

## Selection and rejected prototypes

This pass ran 3,384 simulator games across candidates and controls. Counts below
are candidate-selection evidence, not fresh confirmation of the released file.

- The Choice-lock-only candidate tied v4.2 at 73/96 development, 158/200 mixed,
  and 133/192 adaptive. The included change is supported by mechanics evidence,
  not a separately demonstrated win-rate gain.
- A flat 50-point immediate switch-faint cost scored 75/96 development versus
  73; 163/200 mixed versus 158; 137/192 adaptive versus 133; and 153/192 on a new
  intermediate schedule versus 155. It retained 59/60 custom and tied v4.1
  40/80 directly. The HP-scaled version matched these tested win counts, while
  retaining an explicit weak-reserve sacrifice fixture. Its coefficient was
  fixed before final confirmation, not swept over a parameter grid.
- A broader post-KO forecast averaged an additional exchange against all other
  curated species with equal prior mass. The first prototype scored 72/96
  versus 73 and incorrectly retriggered the incumbent's Intimidate on enemy
  entry. The corrected entry version scored 38/48 versus the control prefix's
  38/48, with p95 around 451 ms under load. Neither version is included. Equal
  species mass is an uncalibrated prior, not knowledge of the hidden enemy team.

New infrastructure saves the exact public agent observations/actions through
`tools/run_eval.py --traces DIR`. `tools/trace_diff.py` compares policies from
the same reference memory and observations. These diagnostics do not pretend
that a changed decision on a fixed reference trajectory proves a changed
battle outcome. Private enemy moves, items, stats and reserves are excluded.

## Validation and remaining work

All 31 release Python tests and both JavaScript tests pass. New tests cover the
saved loss, nondefault Choice locks, weak-reserve sacrifice and last-turn HP
behavior. The historical pre-cap equivalence test now explicitly tests frozen
v4.2 against v4.1; current pre-cap switches intentionally differ. Core, team,
ZIP and manifest agreement are verified. `tools/summarize_v4_3.py` verifies the
exact source hashes, selected battle counts and portal provenance.

Selected runs recorded medians around 30-37 ms and p95 around 86-110 ms under
concurrent local load. No extra search depth was added. Timing depends on
hardware and load, and does not establish a service guarantee.

The important unsolved work remains an evidence-based model of opposing
switches and hidden sets, and continuation after either side faints. A uniform
unknown-opponent forecast was not useful here. Stronger independent opponents
are still needed; the current adaptive policy is independent but not proven
tournament strength. The existing model also retains known approximations,
including the researched Explosion issue. V4.2 remains a usable fallback for
opponent mixes where this reserve-risk adjustment is unhelpful.
