"""Verify and extract the published study without overwriting existing files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/monte-carlo-v1'
destination = OUT / 'reproducer-check'
assert not destination.exists(), 'Choose a fresh directory; never overwrite research'
source = ROOT / 'dist/REDLINE_Monte_Carlo_Project_v1.zip'
sha = lambda data: hashlib.sha256(data).hexdigest()
record = json.loads(source.with_suffix('.json').read_text())
assert sha(source.read_bytes()) == record['sha256']
private_hashes = {sha(p.read_bytes()) for folder in ('teammate', 'teammate_2')
                  for p in (ROOT / folder).rglob('*.py')}
with zipfile.ZipFile(source) as archive:
    names = archive.namelist()
    assert len(names) == len(set(names)) == record['files']
    contents = json.loads(archive.read('MONTE_CARLO_CONTENTS.json'))['files']
    assert set(contents) | {'MONTE_CARLO_CONTENTS.json'} == set(names)
    for name in names:
        path = (destination / name).resolve()
        path.relative_to(destination.resolve())
        assert not any(part.startswith('teammate') for part in Path(name).parts)
        assert not any(name.startswith('research/' + folder + '/') for folder in
                       ('hybrid-comparison', 'teammate-comparison', 'teammate2-comparison'))
        data = archive.read(name)
        if name in contents:
            assert sha(data) == contents[name], name
        if name.endswith('.py'):
            assert sha(data) not in private_hashes, 'Original private code: ' + name
    destination.mkdir()
    archive.extractall(destination)

# npm resolves the installed, pinned runtime from the parent workspace here.
# A separate machine should first install package-lock.json with npm ci.
commands = [[sys.executable, 'tools/audit_monte_carlo.py'],
            [sys.executable, 'tools/verify_release.py'],
            ['npm.cmd' if sys.platform == 'win32' else 'npm', 'test']]
for index, command in enumerate(commands):
    with (destination / ('verification-' + str(index) + '.log')).open('w', encoding='utf-8') as log:
        subprocess.run(command, cwd=destination, stdout=log, stderr=subprocess.STDOUT, check=True)
    print('Passed:', ' '.join(command), flush=True)
assert (destination / 'research/monte-carlo-v1/audit.json').read_bytes() == (OUT / 'audit.json').read_bytes()
evidence = dict(zipSha256=record['sha256'], files=record['files'], allContentsHashesPassed=True,
                noOriginalPrivateTeammateSources=True, extractedAuditPassed=True,
                extractedReleaseMatches=True, extractedTestsPassed=True,
                extractedDirectory=destination.relative_to(ROOT).as_posix(),
                runtime='Python 3.10; Node 24; installed parent Showdown 0.11.11; npm ci needed on a fresh machine')
(OUT / 'reproducer-check.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
print(json.dumps(evidence, indent=2))
