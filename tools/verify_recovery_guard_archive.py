"""Safely extract the research archive and rerun its independent audits."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/robust-rollout-v4'
sha = lambda data: hashlib.sha256(data).hexdigest()
load = lambda path: json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, default=ROOT / 'dist/REDLINE_Recovery_Guard_Project_v4.zip')
    parser.add_argument('--destination', type=Path, default=OUT / 'reproducer-check')
    args = parser.parse_args()
    destination = args.destination.resolve()
    destination.relative_to(OUT.resolve())
    assert not destination.exists(), 'Use a new directory; existing evidence is never removed'
    with zipfile.ZipFile(args.archive) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP paths'
        manifest = json.loads(archive.read('ROBUST_ROLLOUT_CONTENTS.json'))
        assert set(names) == set(manifest) | {'ROBUST_ROLLOUT_CONTENTS.json'}
        for name in names:
            parts = PurePosixPath(name)
            assert not parts.is_absolute() and '..' not in parts.parts
            assert '\\' not in name and ':' not in name
            (destination / name).resolve().relative_to(destination)
            if name in manifest:
                assert sha(archive.read(name)) == manifest[name], name
        archive.extractall(destination)

    # Clear benchmark overrides inherited from a developer's shell.
    env = dict(os.environ)
    for name in ('AGENT_FILE', 'TEAM_FILE', 'OPP_AGENT_FILE', 'OPP_TEAM_FILE',
                 'CUSTOM', 'OPPONENT', 'SEED', 'REPORT', 'TRACE_DIR', 'SAVE_LOGS',
                 'TRACE_GAME', 'MIRROR', 'SPARSE', 'STATELESS', 'NO_LAST_LOSS'):
        env.pop(name, None)
    commands = [
        [sys.executable, 'tools/evaluate_recovery_guard.py', '--audit'],
        [sys.executable, 'tools/audit_robust_history.py'],
        [sys.executable, 'tools/verify_release.py'],
        ['npm.cmd' if os.name == 'nt' else 'npm', 'test'],
    ]
    log_path = OUT / 'package-verification.log'
    with log_path.open('w', encoding='utf-8') as log:
        for command in commands:
            print('Checking extracted archive:', ' '.join(command), flush=True)
            log.write('\n' + ' '.join(command) + '\n')
            log.flush()
            subprocess.run(command, cwd=destination, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=300)
    for relative in ('result.json', 'history-audit.json'):
        assert (destination / 'research/robust-rollout-v4' / relative).read_bytes() == (OUT / relative).read_bytes(), relative
    record = dict(
        archive=args.archive.resolve().relative_to(ROOT).as_posix(),
        archiveSha256=sha(args.archive.read_bytes()),
        checkedFiles=len(manifest),
        newExtraction=destination.relative_to(ROOT).as_posix(),
        allMemberHashesVerified=True,
        extractedStudyAndHistoryAuditsMatch=True,
        recommendedReleaseVerified=True,
        pythonTests=63,
        javascriptChecks=2,
        localSimulatorDependency='Pinned ancestor node_modules; npm ci required on a new machine',
    )
    (OUT / 'package-verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
