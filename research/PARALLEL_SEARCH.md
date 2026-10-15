# Three-way search and common final comparison

The private Kaggle screen notebooks use the same checksummed v4.3.2 source
bundle and seed 43179. Each is CPU-only with Internet enabled, two battle
processes, a six-hour time limit and a 30,000-game budget. The final comparison
has a 10,000-game budget and is saved without execution. No notebook submits a
competition entry or overwrites the recommended agent.

## Workflow

1. Screens 1, 2 and 3 run independently. Their default species-trio partitions
   contain 675, 675 and 674 entries. The current configured team is repeated as
   a control. All default trios appear exactly once across the partitions.
2. Each screen evaluates 8, then 12, then 48 games **per opponent policy** in
   successive rounds, eliminating weaker teams between rounds. It then mutates
   survivor moves, items, abilities, EVs, natures, species and lead order and
   evaluates those candidates for 24 games per policy. Scores combine mean
   and worst-policy performance; tied scores use remaining HP margin.
3. Completed screens export six non-incumbent finalists in compact files named
   redline-screen-1.zip, redline-screen-2.zip and redline-screen-3.zip. These
   contain screening.json only. The default builds are one legal build/order
   per species trio, not an exhaustive search through all possible sets.
4. The final notebook has the three screen notebooks configured as inputs.
   After their output versions complete, use Save & Run All on the final
   notebook. If Kaggle has pinned an older input version, refresh each input
   to the completed version. Alternatively attach the three compact ZIPs as
   a dataset and set SCREENING_ZIPS to their paths. Input discovery ignores
   checkpoint ZIPs and collapses identical root/results copies.
5. The final notebook validates all three campaigns, source hashes, partition
   identities and complete trio coverage. It rejects missing, duplicate,
   stale or mismatched results. It compiles every finalist for its exact team
   and evaluates them on a common 48-game-per-policy qualification schedule.
   The top three plus incumbent reach 96-game-per-policy validation. One
   challenger selected there meets the incumbent on a separate 192-game-per-
   policy confirmation schedule. Adaptive and tactical opponents use distinct
   generated team suites for development, validation and confirmation. The
   frozen opponent is always the exact archived v4.3 team and source.
6. Download best_candidate.zip, result.json and the final checkpoint for
   review. The candidate ZIP contains agent.py and team.txt only. The result
   includes per-policy scores and a paired bootstrap comparison. These are
   exploratory league results, not proof of tournament superiority.

## Budgets and resume

The broader eight-game first round increases work compared with the original
single-notebook estimate. A full screen schedules at most about 26,000 battles;
the common final schedules at most 5,040. Real counts depend on duplicate
mutations and the incumbent's ranking. Speed and match length vary; the earlier
43-second smoke timing does not guarantee the full campaign's completion time.
Parallel speedup applies primarily to screening, while final comparison follows
the completed screens. No GPU acceleration is used by this simulator.

If a budget is reached, the notebook saves completed jobs in a checkpoint.
Attach redline-screen-N-checkpoint.zip as a dataset in the next session and set
RESUME_ZIP to its path. Keep PROFILE, SEED and SHARD_INDEX unchanged. Increase
MAX_GAMES if the cumulative battle limit was reached; MAX_HOURS is per invocation.
An incomplete screen produces no compact finalists file. Final comparison waits
until all three are complete. Work already cached is reused; a partially run
individual battle job may need to be repeated.

For a fast setup test, use PROFILE="smoke" consistently in all four notebooks.
Never merge smoke outputs into a full search. Run only one execution per shard
unless resuming a completed/paused version. Identical simultaneous copies repeat
work. The seed is shared across shards so candidate schedules are comparable.

## Local verification

The exact v4.3.2 three-screen smoke workflow completed 42 + 54 + 36 screening
battles and 102 final-comparison battles: 234 total. The final export's compiled
OWN configuration matched its selected team and the ZIP had exactly two files.
Resuming final comparison used cached jobs and stayed at 102 battles. Tests cover
complete/disjoint partition coverage, illegal sets, duplicate and mismatched
imports, HP tie-breaking and matched outcome comparisons. Notebook verification
also simulates duplicate Kaggle input copies and checkpoint files.

tools/build_parallel_notebooks.py regenerates all notebooks;
tools/verify_parallel.py checks embedded source and input discovery.
