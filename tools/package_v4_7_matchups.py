"""Package the exact frozen matchup inputs and results for reproduction."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/v4_7-matchups-v1'
sha = lambda data: hashlib.sha256(data).hexdigest()
plan = json.loads((OUT / 'plan.json').read_text())
result = json.loads((OUT / 'result.json').read_text())
assert result['completedGames'] == plan['plannedGames'] == 2336
assert result['allSourcesSchedulesAndActionsAudited']
assert result['planSha256'] == sha((OUT / 'plan.json').read_bytes())
assert result['auditorSha256'] == sha((ROOT / 'tools/test_v4_7_matchups.py').read_bytes())
paths = set(plan['inputSha256'])
for name, digest in plan['inputSha256'].items():
    assert sha((ROOT / name).read_bytes()) == digest, name
paths.update(('package.json', 'team.json', '.gitattributes', 'research/SHOWDOWN_LICENSE.txt',
              'tools/package_v4_7_matchups.py'))
paths.update(p.relative_to(ROOT).as_posix() for p in OUT.glob('*.json') if p.name != 'progress.json')
paths.update(p.relative_to(ROOT).as_posix() for p in OUT.glob('*.md'))
paths.update(p.relative_to(ROOT).as_posix() for p in (OUT / 'jobs').glob('*.json'))
payload = {}
for name in sorted(paths):
    path = (ROOT / name).resolve()
    path.relative_to(ROOT)
    assert not any(part.startswith('teammate') for part in Path(name).parts), name
    payload[name] = path.read_bytes()
payload['MATCHUP_REPRODUCE.md'] = b'''# Frozen v4.7 follow-up tests

Extract into a separate directory; Python 3.10+, Node 20+:

    npm ci
    python tools/test_v4_7_matchups.py --audit

Read research/v4_7-matchups-v1/REPORT.md and PROTOCOL.md for the results,
methods and limitations. All 2,336 raw game records and their job stamps
are included. Audit checks exact source hashes, teams, seeds, side pairing,
opponent sets, legal execution and native self-play symmetry, then recomputes
the counts, matrices and paired descriptive intervals.

    python tools/test_v4_7_matchups.py --run --workers 6

resumes missing jobs using the frozen plan. To rerun every battle, remove only
the extracted research/v4_7-matchups-v1/jobs directory first. Do not overwrite
the original campaign or tune candidates on these results.
No private original teammate submissions or competition upload is included.
'''
contents = {name: sha(data) for name, data in payload.items()}
payload['MATCHUP_CONTENTS.json'] = (json.dumps(contents, indent=2) + '\n').encode()
destination = ROOT / 'dist/REDLINE_v4_7_Matchup_Tests_v1.zip'
with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(payload.items()):
        info = zipfile.ZipInfo(name, (2026, 10, 17, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, data)
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    for name, digest in contents.items():
        assert sha(archive.read(name)) == digest
record = dict(zip=destination.relative_to(ROOT).as_posix(), sha256=sha(destination.read_bytes()),
              files=len(payload), bytes=destination.stat().st_size, games=2336,
              planSha256=result['planSha256'], sourceSha256=plan['sourceSha256'],
              originalPrivateTeammateSourcesIncluded=False)
destination.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
