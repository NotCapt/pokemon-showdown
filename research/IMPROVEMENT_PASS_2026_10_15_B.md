# Second improvement pass: fresh loss analysis and coverage experiments

The recommended submission remains v4.2, `dist/REDLINE_Search.zip`. No v4.3
release was promoted. Research identifiers `v4_3-*` and `v5-*` below are
experiment names, not release versions. No portal upload or final entry was
made in this pass.

## What was built

- Generated 24 development teams (seed 102173) and 32 separate validation teams
  (seed 727309), using the curated legal options. They are synthetic teams,
  not optimized tournament opponents. The independent adaptive opponent is
  unchanged and is not established as stronger than competing submissions.
- Saved all 96 development replays and added `tools/analyze_losses.py`.
  It records deaths, preceding attacks and resisted attacks, with an explicit
  warning that a preceding move does not prove the cause of a faint.
- Added `--logs` to the clean evaluation runner.
- Extended the packager with `--source` / `--team`, and checks that the compiled
  own-team configuration and team text match. This allows experimental ZIPs
  without replacing the recommended submission.

The baseline lost 23/96 development battles. Lapras and Excadrill appeared
frequently in the death diagnostics. Replays also show costly switches into
attacks and Choice locks exploited by opposing switches. Hidden items, stats
and sets in saved simulator reports are only offline diagnostics; they are
never passed to the agent.

## Team experiments

All candidates retain the same search core as v4.2. Each generated agent embeds
its exact own-team configuration. Team order stays Dragonite / Dragapult /
Arcanine.

| Development, adaptive opponent, 96 games | Wins |
| --- | ---: |
| V4.2 control | 73 |
| HP investment instead of Speed on Dragonite | 74 |
| Close Combat instead of Crunch on Arcanine | 81 |
| Close Combat and Wild Charge instead of Crunch and Play Rough | 77 |
| Close Combat instead of Play Rough | 81 |

The first Close Combat candidate gained eight games with no regressions in
development, across three opposing team configurations. Its broader results:

| Matched schedule | Close Combat instead of Crunch | V4.2 |
| --- | ---: | ---: |
| Fresh 32-team adaptive validation, 192 games | 133 | 133 |
| Previously used 24-team adaptive schedule, 192 games | 154 | 151 |
| Previously used mixed simple policies, 200 games | 165 | 151 |
| Fresh mixed simple policies, seed 27449, 200 games | 162 | 158 |
| Original six tactical teams, 60 games | 58 | 59 |

The fresh mixed gain is +2 percentage points, with a team-cluster bootstrap
95% interval of -2 to +6 points. It includes six improved and two regressed
games. Fresh adaptive validation includes three improvements and three
regressions. The older mixed gain is +7 points, interval +2.5 to +12, but this
schedule has been reused for candidate evaluation.

Directly against archived v4.1 on its exact equipped team, the Close Combat
instead-of-Crunch candidate won 35/80; replacing Play Rough won 34/80. These
small samples do not establish statistical inferiority, but they do not
demonstrate an advantage over our saved policy. Ordinary v4.2/v4.1 differences
are only at the turn cap; the retained mechanics candidate below tied v4.1
40/80 on the same schedule. The custom-suite regression was one extra loss
against Dragonite / Dragapult / Metagross, not a complete matchup collapse.

The coverage variant is preserved as
`dist/REDLINE_Search_coverage_experimental.zip`, containing only agent.py and
team.txt. It is **not** the recommended competition artifact. Its source SHA256
is `eb18fa72c8284070025fba9242a46da21b3d68511a0144abc10923befa862ef1`.

## Explosion mechanics experiment

The approximate model failed to faint an Explosion user, including when the
target was immune or protected. The experimental correction handles execution,
immunity, Protect and an explicit miss, while sleep, freeze and flinch can
prevent the move from executing.

Three actual Showdown tests confirm self-KO on legal Metagross matchups against
Snorlax, Dragapult and Protect Blastoise. Three additional Python tests cover
execution gates and misses. Run:

```
python research/test_explosion.py
node --test research/explosion.test.js
```

| Mechanics candidate schedule | Candidate | V4.2 |
| --- | ---: | ---: |
| Adaptive development /96 | 73 | 73 |
| Fresh adaptive validation /192 | 133 | 133 |
| Fresh mixed /200 | 156 | 158 |
| Original tactical /60 | 59 | 59 |
| Stateless tactical /40 | 31 | 31 |
| Direct archived v4.1 /80 | 40 | — |

This correction is retained in research, not the release. It demonstrates a
real mechanics error, but does not improve tested battle performance. A likely
explanation to investigate is that the model rewards the predicted opposing
faint without modeling the opposing replacement. That explanation is an
inference, not a demonstrated cause of the two regressed games.

## Verification and next direction

`tools/summarize_improvement_b.py` checks every new battle report against its
saved source hash, game count and illegal-action field. There were 2,544 games
in this pass, with no illegal actions or worker exceptions. These games include
controls, repeated teams, candidate selection and reused schedules; their total
must not be interpreted as 2,544 independent trials or pooled into a single
win-rate estimate. The release still passes 27 Python tests and the JavaScript
opponent isolation test, and ZIP/core/team/manifest agreement checks.

The next policy work should target switching and the value of the battle after
a predicted knockout, especially Choice locks and opposing replacements.
Correcting individual mechanics or adding coverage without that context can
improve simple matchups while hurting others. New candidates need fresh
independent opponents as well as these regression suites. No tournament-level
strength claim follows from the current baselines.
