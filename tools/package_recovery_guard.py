"""Publish own frozen experiment inputs/results, preserving the aborted trial."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/robust-rollout-v4';OLD=ROOT/'research/robust-rollout-v1';MIDDLE=ROOT/'research/robust-rollout-v2';PRIOR=ROOT/'research/robust-rollout-v3'
load=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
r=load(OUT/'result.json');assert r['allSourcesSchedulesAndOutcomesAudited'] and r['checkedGames'] in (792,2760)
paths=set()
for folder in (OLD,MIDDLE,PRIOR,OUT):
    manifest=load(folder/'manifest.json')
    for name,digest in manifest['inputSha256'].items():
        assert sha((ROOT/name).read_bytes())==digest,name
        paths.add(name)
    paths.update(p.relative_to(ROOT).as_posix() for p in folder.glob('*.json') if p.name not in ('progress.json','portal-result.json','portal-result.tested.json','package-verification.json'))
    paths.update(p.relative_to(ROOT).as_posix() for p in folder.glob('*.md'))
    paths.update(p.relative_to(ROOT).as_posix() for p in (folder/'jobs').glob('*.json'))
    paths.update(p.relative_to(ROOT).as_posix() for p in folder.glob('checks-*.log'))
paths.update(p.relative_to(ROOT).as_posix() for p in (OLD/'diagnostics').rglob('*') if p.is_file() and p.suffix in ('.json','.log'))
# The diagnostic replay tool needs these selected historical schedules/results.
historical=ROOT/'research/v4_7-matchups-v1';plan=load(historical/'plan.json')
paths.add('research/v4_7-matchups-v1/plan.json')
for case in load(OLD/'diagnostics/summary.json')['cases']:
    spec=next(s for s in plan['jobs'] if s['name']==case['name'])
    paths.add('research/v4_7-matchups-v1/jobs/'+spec['name']+'.json')
    paths.add(spec['teamFile'])
    if 'custom' in spec:paths.add(spec['custom'])
    if 'opponentTeam' in spec:paths.add(spec['opponentTeam'])
paths.update(subprocess.check_output(['git','ls-files','--','tools','tests','archive'],cwd=ROOT,text=True).splitlines())
paths.update('tools/'+name for name in ('trace_matchup.js','trace_worker.py','diagnose_robust_rollout.py',
             'prepare_robust_rollout.py','check_robust_rollout.py','evaluate_robust_rollout.py',
             'prepare_robust_rollout_v2.py','check_robust_rollout_v2.py','evaluate_robust_rollout_v2.py',
             'prepare_margin_rollout.py','check_margin_rollout.py','evaluate_margin_rollout.py','prepare_recovery_guard.py','check_recovery_guard.py','evaluate_recovery_guard.py','summarize_recovery_guard.py','package_recovery_guard.py','verify_recovery_guard_archive.py','audit_robust_history.py'))
paths.update(('README.md','package.json','package-lock.json','.gitattributes','team.json','agent_core.py',
              'submission/agent.py','submission/team.txt','dist/REDLINE_Search.zip','dist/REDLINE_Search-manifest.json',
              'dist/REDLINE_Search_v4_7.zip','dist/REDLINE_Search_v4_7-manifest.json',
              'research/c-switch-fixture.json','research/f-hazard-fixture.json','research/readiness-v4_6/options-fetch.txt',
              'research/roster-forecast-v1/recovery-oracle.json','research/monte-carlo-v1/candidates/phased_mc/agent_core.py'))
if (OUT/'release.json').exists():
    paths.add('tools/promote_recovery_guard.py')
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'archive/v4_8').glob('*') if p.is_file())
    paths.update(('dist/REDLINE_Search_v4_8.zip','dist/REDLINE_Search_v4_8-manifest.json'))
private={sha(p.read_bytes()) for folder in ('teammate','teammate_2') for p in (ROOT/folder).rglob('*.py')}
paths={name.replace('\\','/') for name in paths}
payload={}
for name in sorted(paths):
    path=(ROOT/name).resolve();path.relative_to(ROOT)
    assert not any(part.startswith('teammate') for part in Path(name).parts),name
    assert not any(name.startswith('research/'+folder+'/') for folder in ('hybrid-comparison','teammate-comparison','teammate2-comparison')),name
    data=path.read_bytes()
    if name.endswith('.py'):assert sha(data) not in private,name
    payload[name]=data
payload['ROBUST_ROLLOUT_REPRODUCE.md']=b'''# Selective recovery-override study v4

This research archive is not the competition entry. Extract into a new folder.
Windows, Python 3.10+, Node 20+; install the pinned simulator with npm ci.
Frozen input manifests retain some Windows-native paths. Their original
audit tools should be run on Windows; ZIP member names use standard slashes.

    python tools/evaluate_recovery_guard.py --audit
    python tools/audit_robust_history.py
    python tools/verify_release.py
    npm test

Read research/robust-rollout-v4/REPORT.md and PROTOCOL.md. The main audit
recomputes the source/schedule checks, validation eligibility and selected
candidate, paired comparisons and gates. It handles either the predeclared
792-game validation-futility stop or the full 2,760-game study. Sources and
rules remain frozen; no post-hoc tuning or source substitution.

The original 376 v1 games, 792 v2 games and 1,000 retained v3 games are included
for transparency. These earlier attempts failed or stopped and are excluded
from v4 strength estimates. Historical replay diagnostics are development
information only. The separate history audit verifies their retained records.
No original private teammate submissions are included.
'''
contents={name:sha(data) for name,data in payload.items()}
payload['ROBUST_ROLLOUT_CONTENTS.json']=(json.dumps(contents,indent=2)+'\n').encode()
destination=ROOT/'dist/REDLINE_Recovery_Guard_Project_v4.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,data in sorted(payload.items()):
        info=zipfile.ZipInfo(name,(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,data)
with zipfile.ZipFile(destination) as archive:
    assert len(archive.namelist())==len(set(archive.namelist()))==len(payload)
    assert archive.testzip() is None
    for name,digest in contents.items():assert sha(archive.read(name))==digest
record=dict(zip=destination.relative_to(ROOT).as_posix(),sha256=sha(destination.read_bytes()),bytes=destination.stat().st_size,
            files=len(payload),auditedFreshGames=r['checkedGames'],abortedGamesPreservedButExcluded=376,futileValidationGamesPreservedButExcluded=792,otherRetainedV3GamesExcluded=1000,originalPrivateTeammateSourcesIncluded=False)
destination.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
