# Interpreting the follow-up

The direct matchups favor v4.7 strongly, including all team orders. These are
familiar releases using the same fixed three-Pokémon team, with new simulator
seeds. They do not estimate performance against an unknown tournament field.
The earlier Monte Carlo selection league already contained familiar opponents.

In the new random-build field, the two releases are essentially tied: v4.7
741/768, v4.6 742/768. The descriptive paired interval for the score gain is
[-1.69, +1.43] percentage points. This follow-up does not establish a general
win-rate gain from v4.7. Both models nearly saturate the random-action and
tactical categories; adaptive play exposes more losses. In coherent adaptive
games v4.7 scores 115/128 versus 117/128; in uniform adaptive games it scores
122/128 versus 124/128. These small individual regressions are exploratory
observations, not proof of a broad decrease in strength.

Native self-play is a symmetry diagnostic. Each exact, side-swapped seed pair
must sum to one scored point; both versions pass. Identical team-order cells
on the v4.7 order grid also split 2–2. Off-diagonal cells use different orders
and fresh seeds, so the full 75–69 result can differ from 50%. Each cell has
only four games and should not determine a new preferred lead order.

Both releases receive identical recorded simulator seeds, sides and opposing
configurations. The random-action baseline has a continuous pseudorandom stream
within each job. Different battle lengths can therefore cause later action
streams to diverge between releases; the comparisons do not force identical
future opponent actions. Tactical/adaptive responses also change with the
position. Whole-build clustered intervals remain descriptive local diagnostics.
Uniformly sampled legal sets can have weak item/move/EV synergy, so their high
win rates should not stand in for results against well-built enemy teams.

Of v4.7's 16 native direct losses, 13 reach the turn-101 HP adjudication. Only
28/256 native direct games reach that point overall. Endgame HP management and
the fresh adaptive regressions are useful next debugging targets. These counts
do not establish the cause of a loss. No agent source, team, release gate or
submission artifact was changed during this follow-up, and no additional
practice upload or final entry submission was performed.
