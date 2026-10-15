# V2 candidate — verified fixes, not yet a proven stronger tournament policy

Historical report: v3 has since replaced the recommended main ZIP. See
`research/V3_REPORT.md` for current release results. Statements below describe
the state at the v2 evaluation.

The original release is preserved in `archive/v1/`, including its ZIP. The main
`dist/REDLINE_Search.zip` remains v1; the new candidate is separately packaged as
`dist/REDLINE_Search_v2_candidate.zip`. `submission/agent.py` and `agent_core.py`
now contain v2. Do not assume the main ZIP matches those development files.

## What was established on the real portal

The controlled `tools/portal_contract.py` agent encoded field-presence checks as
legal move choices, with Corviknight remaining active throughout the relevant
turns. Its replay showed:

- Turn 2: `bool(my_active.boosts)` false.
- Turn 3, after successful Iron Defense: positive Defense boost unavailable.
- Turn 4: `self.calls > 2` true, demonstrating instance memory in this run.
- Turn 5: no `pp` key in the tested valid move entries.
- Turn 6: own stats absent/empty.
- Turn 7: own condition present.
- Turn 8: opponent boosts absent/empty.
- Turn 9: own name present.

This is one observed service execution, not a permanent API guarantee. The script
and response are preserved as `tools/portal_contract.py` and
`research/contract-result.json`. The service's static validator also requires the
literal argument name `observation`: a semantically equivalent `decide(self,o)`
was rejected. No diagnostic code is embedded in the production candidate.

## Changes

- Remember estimated own boosts between turns, resetting on switching. Prefer
  supplied nonempty boost telemetry when available. Track setup attempts to stop
  repeated setup even when a move fails. Retain conservative limits for a fresh
  agent created mid-battle.
- Use the actual available moves in search continuations instead of assuming the
  species' default moves. Honor single-move choice locks.
- Enumerate independent first-turn hit/miss outcomes, weighted by accuracy,
  across three damage rolls. A miss no longer acts like a weaker guaranteed hit.
  Later greedy continuation turns still approximate accuracy by expected damage.
- Prioritize plausible knockouts and priority when choosing rollout attacks.
- Model multihit damage as multiple damage calculations, reduce only the first
  hit for Multiscale, and avoid treating Focus Sash as protection from an entire
  lethal multihit attack.
- Add a frozen v1 opponent and a fixed tactical baseline, custom-team fixtures,
  selectable agent paths, and record the agent hash at benchmark startup.

## Evidence

Fourteen unittest tests pass, including 100 randomized legality states. New
regressions cover misses, multihit/Sash, multihit/Multiscale and memory reset.

| Comparison | V2 | V1 | Interpretation |
| --- | ---: | ---: | --- |
| Same-team head-to-head, 60 games, hidden boosts | 30 wins | 30 wins | No demonstrated head-to-head advantage |
| Six custom opponent teams, fixed tactical baseline, 60 paired games each | 52 wins | 54 wins | V2 did not improve this suite |

Reports: `v2-final-mirror.json`, `v2-custom.json`, `v1-custom.json`. Custom fixture
sets include sand offense, setup sweepers, Choice Scarf and Choice Specs sets,
Focus Sash, Weakness Policy and defensive builds. The tactical opponent remains
simple: these are stronger coverage tests, not a top-tier external opponent.
Its hidden-state assumptions remain imperfect, including default-set estimates.

An earlier default-team tactical run scored 58/60, but its tactical baseline used
the evolving model. It is not directly comparable to older v1 reports and is not
used to claim improvement. Historical experimental reports may also have hashes
captured after a concurrent build; only the explicit comparisons above are used.

The final candidate completed a real portal battle in six turns and won. Replay
showed Iron Defense once, followed by Body Press on the next turn. An earlier
candidate lost an eleven-turn practice battle after a Draco Meteor miss. These
are compatibility tests, not reliable live win-rate estimates.

## Remaining limits and next work

Boost memory is an estimate of attempted moves: without move-result telemetry it
cannot reliably identify flinches, misses, Taunt, failed setup or stat resets.
Do not confuse remembered actions with confirmed outcomes. Own offensive drops
can consequently be overestimated after a miss. Root speed ties, secondary
effects, full coherent enemy-set beliefs, opponent switching, hazards and many
volatile effects still need a more complete state model.

The candidate fixes reproducible mechanics and integration defects but is slower
and has not earned promotion over v1. Keep both packages. The next promotion gate
should be a fresh, diverse opponent suite and independent strong opponents, with
paired seeds and no reuse of validation results to tune the policy.
