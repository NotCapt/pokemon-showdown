"""Summarize the two completed, audited campaigns without changing the release."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
latest=ROOT/'research/kaggle-v4_5-evaluation'
cloud=ROOT/'research/kaggle-results-v4_3_2/final'
local_result=json.loads((latest/'result.json').read_text())
cloud_result=json.loads((cloud/'result.json').read_text())
local_audit=json.loads((latest/'audit.json').read_text())
cloud_audit=json.loads((cloud/'audit.json').read_text())
assert all(r['allSchedulesAndCompiledTeamsVerified'] for r in (local_audit,cloud_audit))
assert not local_result['promote']
release_sha=hashlib.sha256((ROOT/'submission/agent.py').read_bytes()).hexdigest()
assert release_sha==local_result['sourceSha256']=='0afe57fe578ffdbd74fa848deae46524f3de4d66065bd152f061c9e684e45c69'
names=lambda row:'/'.join(p['name'] for p in row['team'])
lines=['# Completed Kaggle campaign: keep v4.5 as recommended','',
    'All three screens completed and passed matching-source and complete-coverage checks: 77,700 battles covering all 2,024 default species trios, followed by survivor mutations. This is one default build/order per trio, not exhaustive enumeration of legal teams.',
    '', 'Both final comparisons completed 5,040 battles. Total campaign work: **87,780 battles**. That total includes selection rounds, repeated opponents and seed pairs; it is not an independent statistical sample.',
    '', '## Latest-engine result','',
    'The 18 screen finalists and the incumbent were compiled with the same frozen v4.5 engine. Qualification used 48 games per policy, validation 96, and independent confirmation 192. Only one challenger was chosen on validation, before confirmation. All phases used new suites and seeds.',
    '',f"Challenger: **{names(local_result['challenger'])}**.",
    '', '| Confirmation opponent | Current v4.5 | Challenger | Change |',
    '| --- | ---: | ---: | ---: |']
for policy,row in local_result['comparison']['policies'].items():
    label={'adaptive':'Adaptive, varied hidden sets','tactical':'Tactical, varied hidden sets','frozen':'Fixed v4.5 agent and team'}[policy]
    lines.append(f"| {label} | {row['controlWins']}/{row['games']} | {row['challengerWins']}/{row['games']} | {row['scoreGainPP']:+.2f} pp |")
c=local_result['comparison'];lo,hi=c['pairedScoreInterval95']
lines+=['',f"Overall: challenger {local_result['challenger']['wins']}/576 versus control {local_result['incumbent']['wins']}/576; mean score gain {c['meanScoreGainPP']:+.2f} percentage points, descriptive paired 95% interval [{lo:+.2f}, {hi:+.2f}]. Most of that gain comes from the fixed v4.5 matchup. On the two varied-opponent policies combined, the challenger won 338/384 (88.02%) versus control 345/384 (89.84%)."]
lines+=['', '**Promotion rejected by the rule fixed before testing.** Although the aggregate score and interval passed, the adaptive result fell 5.73 points, exceeding the allowed five-point regression. The recommended submission remains unchanged at v4.5; no v4.6 release is justified by this campaign.',
    '', 'The alternate build is preserved in `dist/REDLINE_Kaggle_Challenger_v4_5.zip`. Its exact source passed all 52 Python checks and its exported team matched the embedded configuration. It is an experimental option; it has not received a new portal practice test.',
    '', '## Frozen cloud result','',
    f"The original private Kaggle final completed as version 5. Its selected team was **{names(cloud_result['selected'])}**. It used the frozen v4.3.2 engine and the archived v4.3 fixed opponent, so these results are separate from the latest-engine campaign.",
    '', '| Frozen cloud confirmation opponent | Old incumbent | Cloud challenger |', '| --- | ---: | ---: |']
for policy,row in cloud_result['comparison']['policies'].items():
    lines.append(f"| {policy} | {row['controlWins']}/{row['games']} | {row['challengerWins']}/{row['games']} |")
c=cloud_result['comparison'];lo,hi=c['pairedScoreInterval95']
lines+=['',f"Mean score gain over the old control: {c['meanScoreGainPP']:+.2f} points, descriptive paired 95% interval [{lo:+.2f}, {hi:+.2f}]. Recompiled with v4.5, this same team scored only 106/144 in qualification and did not reach latest-engine validation. The cloud ZIP must therefore remain a historical experimental artifact.",
    '', '## Evidence and artifacts','',
    '- `research/kaggle-results-v4_3_2/`: verified compact screen exports and downloaded cloud final result, ZIP, full checkpoint and audit.',
    '- `research/kaggle-v4_5-evaluation/`: frozen manifest/reference source, all 19 exact candidate builds, three suites, 75 battle reports, rankings, result and audit.',
    '- `tools/audit_kaggle_cloud_final.py`: verified cloud provenance, compiled teams and source hashes, all 5,040 schedules, zero reported action errors, selection and paired bootstrap. Downloaded Python was parsed but never executed.',
    '- `tools/audit_kaggle_evaluation.py`: verified all 5,040 latest-engine schedules, compiled teams, rankings, promotion gate and exported bytes.',
    '- Kaggle final version 4 ran no battles because the input links were not mounted. Version 5 included the three checksummed compact ZIPs directly and completed.',
    '', '## Next direction','',
    'Build a stronger opponent league from diverse frozen finalist teams and policies. Fix its weights and new holdout schedules before tuning; the single fixed-incumbent matchup currently dominates the apparent gain. Inspect the challenger\'s adaptive regressions to guide switching and hidden-set inference, then evaluate any changes on untouched schedules. Two-turn attacks, pivot transitions, sleep and status forecasts remain approximate and deserve targeted simulator comparisons.',
    '', 'Use `dist/REDLINE_Search.zip` for the current recommended release. Its source SHA256 remains `'+release_sha+'`. The alternate candidate source SHA256 is `77d4c22dee29157e910063d84b37ca62fa40e8c5f9d1261cb5ed337005935c08`. No competition entry was submitted.']
(ROOT/'research/KAGGLE_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Wrote research/KAGGLE_RESULTS.md. Recommended v4.5 release unchanged.')
