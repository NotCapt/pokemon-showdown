"""Publish our frozen Monte Carlo experiment, excluding private teammate code."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/monte-carlo-v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((OUT/'manifest.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
assert audit['allSourcesSchedulesScoresAndGatesVerified']
paths=set(m['inputSha256'])
for name,digest in m['inputSha256'].items():assert sha((ROOT/name).read_bytes())==digest,name
# Track-only collection excludes original, untracked teammate submissions.
paths.update(subprocess.check_output(['git','ls-files','--','tools','tests','archive'],cwd=ROOT,text=True).splitlines())
paths.update('tools/'+name for name in ('prepare_monte_carlo.py','check_monte_carlo.py','preflight_monte_carlo.py',
             'evaluate_monte_carlo.py','audit_monte_carlo.py','summarize_monte_carlo.py',
             'check_monte_carlo_standalone.py','package_monte_carlo_project.py','check_monte_carlo_package.py'))
paths.update(p.relative_to(ROOT).as_posix() for p in OUT.glob('*.json') if p.name not in ('progress.json','portal-result.json','portal-result.tested.json'))
paths.update(p.relative_to(ROOT).as_posix() for p in OUT.glob('*.md'))
paths.update(p.relative_to(ROOT).as_posix() for p in (OUT/'jobs').glob('*.json'))
paths.update(('README.md','package.json','package-lock.json','.gitattributes','agent_core.py','team.json',
              'submission/agent.py','submission/team.txt','dist/REDLINE_Search.zip','dist/REDLINE_Search_v4_6.zip',
              'dist/REDLINE_Search-manifest.json','research/c-switch-fixture.json','research/f-hazard-fixture.json',
              'research/readiness-v4_6/options-fetch.txt'))
if (OUT/'release.json').exists():
    paths.add('tools/promote_monte_carlo.py')
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'archive/v4_7').glob('*') if p.is_file())
    paths.update(('dist/REDLINE_Search_v4_7.zip','dist/REDLINE_Search_v4_7-manifest.json'))
for name in paths:
    p=(ROOT/name).resolve();p.relative_to(ROOT)
    assert not any(part.startswith('teammate') for part in p.relative_to(ROOT).parts),name
    assert not name.startswith('research/hybrid-comparison/'),name
    assert p.is_file(),name
payload={name:(ROOT/name).read_bytes() for name in sorted(paths)}
payload['MONTE_CARLO_REPRODUCE.md']=b'''# Frozen Monte Carlo rollout experiment

This research package is not the competition submission. Read
research/monte-carlo-v1/REPORT.md for the result and limitations.
Extract into a separate directory. Python 3.10+, Node 20+:

    npm ci
    python tools/audit_monte_carlo.py
    python tools/verify_release.py
    npm test

The audit recomputes 6,048 stored results, their schedules, hashes, ranks,
paired intervals, challenger selection and promotion gates. Frozen model
sources, legal team files and all battle result records are included.
No private original teammate submissions are included. Runtime preflight
evidence predates the battle campaign; do not overwrite frozen inputs.

To rerun the scheduled battles, remove only extracted jobs/ records first:

    python tools/evaluate_monte_carlo.py --run --workers 6

Selection and all model inputs remain frozen; no field tuning is performed.
Scores concern the local test field, not guaranteed tournament performance.
'''
contents=dict(files={name:sha(data) for name,data in payload.items()},scheduledGames=6048,recommended=audit['recommended'])
payload['MONTE_CARLO_CONTENTS.json']=(json.dumps(contents,indent=2)+'\n').encode()
destination=ROOT/'dist/REDLINE_Monte_Carlo_Project_v1.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,data in sorted(payload.items()):
        info=zipfile.ZipInfo(name,(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,data)
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    for name,digest in contents['files'].items():assert sha(archive.read(name))==digest
record=dict(zip=destination.relative_to(ROOT).as_posix(),sha256=sha(destination.read_bytes()),files=len(payload),bytes=destination.stat().st_size,
            scheduledGames=6048,recommended=audit['recommended'],originalPrivateTeammateSourcesIncluded=False)
destination.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
