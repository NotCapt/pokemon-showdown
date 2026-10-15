# Published league evidence

`REPORT.md` describes the completed study; `manifest.json` records its original
inputs, candidates, schedules, weights and promotion rule. The rankings, result,
audit, release and verification records provide the aggregate evidence for v4.6.
`portal-summary.json` records the separate authorized practice compatibility check.

Full battle reports, traces, replay HTML, compiled candidates and scratch output
remain in the local workspace. They are not all included in this Git directory.
The 192 extra execution-mode games are summarized in `execution-modes/summary.json`
and do not affect the 8,856-game league score.

For reproduction, extract `dist/REDLINE_Diverse_League_Project_v1.zip` from the
repository root into a separate Windows directory and follow its `REPRODUCE.md`.
The bundle preserves the original v4.5 control, all 25 compiled candidates and
the frozen schedules. Its manifest lists the exact file and bundle hashes.
It contains no cached battle outcomes, so reproduction runs the games again.

The root working tree now contains v4.6 and is deliberately rejected as a changed
historical campaign input. No competition entry was submitted.
