# Direct-counter replay diagnosis

Two diagnostic replays reproduced the first side-reversed seed pair of the
preceding 188–4 matchup exactly, including the four-turn outcomes and final HP.
The roles were reversed to capture the incumbent's decisions. These are repeat
observations of existing games; they add no independent strength evidence and
are excluded from the 8,856-game diverse league.

In this pair:

1. Dragonite chose Ice Spinner. The faster opposing Dragapult used Dragon
   Darts, with the second hit finishing Dragonite after Multiscale reduced the
   first hit. Dragonite never attacked.
2. The incumbent's Dragapult used Sucker Punch, leaving the opposing Dragapult
   at 15/317 HP. Dragon Darts then knocked out the incumbent's Dragapult.
3. Arcanine entered and used Crunch. The opponent switched to Tyranitar,
   resisted Crunch and recovered some HP with Leftovers.
4. Arcanine used Play Rough, but Tyranitar survived and knocked it out with
   Stone Edge. Corviknight was never needed in this pair.

The forecast already estimates the default Dragapult's Dragon Darts as lethal
to full-HP Dragonite (about 124% at its middle damage quantile). The retained
policy nevertheless chooses Ice Spinner after combining several possible
opposing moves. That identifies opponent action weighting and long-term
replacement value as possible investigation targets. It does not establish
that switching would win, or explain every one of the 188 losses.

`tools/diagnose_kaggle_decision.py` captures the existing policy's scores without
modifying them. Dragon Darts has 2/8.6 (23.26%) of its expected-move weight;
Phantom Force, Flamethrower and U-turn each receive the same weight, with Draco
Meteor receiving 0.6/8.6. Ice Spinner's combined internal score is +34.73, versus
-13.37 for switching to Arcanine. These are model utility units. The forecast
also approximates two-turn moves, so the values should not be interpreted as
accurate opponent probabilities or guaranteed battle outcomes.

As a post-hoc counterfactual, `tools/counterfactual_opening.py` forced the legal
Arcanine switch on turn 1 and then returned to the original policy. Both games
still lost, in 12 turns rather than four; the opponent retained 143.25 summed
HP points. This does not prove the matchup unwinnable. It shows that this one
opening change did not solve the observed pair. These two additional diagnostic
games are also excluded from league scores and independent strength claims.

Reproduce with `python tools/replay_kaggle_matchup.py`. Exact source hashes,
observations, actions and battle logs are under `diagnostics/direct-counter/`.
No decision-engine change was made during the diverse league.
