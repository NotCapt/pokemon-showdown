"""Preserve our two completed studies, excluding private teammate submissions."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = ('roster-forecast-v1', 'phantom-forecast-v1')
sha = lambda data: hashlib.sha256(data).hexdigest()
paths = set()
for campaign in CAMPAIGNS:
    folder = ROOT / 'research' / campaign
    manifest = json.loads((folder / 'manifest.json').read_text())
    for name, digest in manifest['inputSha256'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
        paths.add(name)
    audit = json.loads((folder / 'audit.json').read_text())
    assert audit['allSourcesSchedulesAndScoresVerified']
    assert not audit['promoteStrength'] and not audit['promoteCorrectness']
    paths.update(p.relative_to(ROOT).as_posix() for p in folder.glob('*.json')
                 if p.name != 'progress.json' and
                 (p.name != 'checks.json' or campaign == 'phantom-forecast-v1'))
    paths.update(p.relative_to(ROOT).as_posix() for p in folder.glob('*.md'))
    paths.update(p.relative_to(ROOT).as_posix() for p in (folder / 'jobs').glob('*.json'))

# These have already been published; do not collect untracked private folders.
tracked = subprocess.check_output(
    ['git', 'ls-files', '--', 'tools', 'tests', 'archive'], cwd=ROOT, text=True).splitlines()
paths.update(tracked)
paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'archive/v4_6').glob('*') if p.is_file())
paths.update('tools/' + name for name in (
    'audit_submission_readiness.py', 'check_recovery_forecast.py', 'recovery_oracle.js',
    'prepare_roster_forecast.py', 'evaluate_roster_forecast.py',
    'audit_roster_forecast.py', 'summarize_roster_forecast.py',
    'prepare_phased_forecast.py', 'check_phased_forecast.py', 'phantom_oracle.js',
    'evaluate_phased_forecast.py', 'audit_phased_forecast.py',
    'summarize_phased_forecast.py', 'package_forecast_project.py'))
paths.update((
    'README.md', 'package.json', 'package-lock.json', '.gitattributes',
    'agent_core.py', 'team.json', 'submission/agent.py', 'submission/team.txt',
    'dist/REDLINE_Search.zip', 'dist/REDLINE_Search_v4_6.zip',
    'dist/REDLINE_Search-manifest.json', 'tests/test_contract.py',
    'research/c-switch-fixture.json', 'research/f-hazard-fixture.json',
    'research/readiness-v4_6/REPORT.md', 'research/readiness-v4_6/audit.json',
    'research/readiness-v4_6/sources.json', 'research/readiness-v4_6/options-fetch.txt'))

for name in paths:
    path = (ROOT / name).resolve()
    path.relative_to(ROOT)
    assert not any(part.startswith('teammate') for part in path.relative_to(ROOT).parts), name
    assert not name.startswith(('research/hybrid-comparison/', 'teammate/', 'teammate_2/')), name
    assert path.is_file(), name

readme = '''# Frozen forecast experiments and original v4.6 audit

This is a research reproducer, not the competition submission ZIP.
The recommended submission remains dist/REDLINE_Search_v4_6.zip.
The new recovery, roster and temporal policies failed their release gates.

Extract into a separate directory. Use Python 3.10+ and Node 18+:

    npm ci
    python tools/audit_roster_forecast.py
    python tools/audit_phased_forecast.py
    python tools/audit_submission_readiness.py
    python tools/verify_release.py
    npm test

All 6,048 scheduled battle records, stamps, frozen inputs and aggregate results
are included. Shared control/recovery records are counted only once. The audit
commands recompute schedules, scores, paired intervals and promotion decisions;
they do not run new battles. The readiness audit uses the official options
snapshot checked on 16 October 2026, not a fresh future legality guarantee.

To rerun battles, remove job records only within this extracted project, then:

    python tools/evaluate_roster_forecast.py --run --workers 6
    python tools/evaluate_phased_forecast.py

Immutable manifests reject modified inputs. Original private teammate
submissions and downloaded organizer guides are excluded.
'''
payload = {name: (ROOT / name).read_bytes() for name in sorted(paths)}
payload['FORECAST_REPRODUCE.md'] = readme.encode()
manifest = dict(files={name: sha(data) for name, data in payload.items()},
                scheduledGames=6048, recommended='dist/REDLINE_Search_v4_6.zip',
                allExperimentalPromotionGatesPassed=False)
payload['FORECAST_CONTENTS.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
destination = ROOT / 'dist/REDLINE_Forecast_Audit_Project_v1.zip'
with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(payload.items()):
        info = zipfile.ZipInfo(name, (2026, 10, 16, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, data)
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    for name, digest in manifest['files'].items():
        assert sha(archive.read(name)) == digest
record = dict(zip=destination.relative_to(ROOT).as_posix(), sha256=sha(destination.read_bytes()),
              files=len(payload), bytes=destination.stat().st_size, scheduledGames=6048,
              privateOriginalSubmissionsIncluded=False)
destination.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
