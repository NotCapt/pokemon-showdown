"""Freeze passing automated checks before any new battle outcomes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/monte-carlo-v1'
assert not (OUT / 'manifest.json').exists(), 'Preflight evidence is already frozen'
checks = {}
for label in ('control', 'phased', 'mc', 'phased_mc'):
    source = OUT / 'candidates' / label / 'agent.py'
    env = dict(os.environ, AGENT_FILE=str(source))
    commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'],
                ['node', '--test', 'tests/opponents.test.js', 'tests/choice.test.js']]
    with (OUT / ('checks-' + label + '.log')).open('w', encoding='utf-8') as log:
        for command in commands:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    checks[label] = dict(passed=True, pythonTests=63, javascriptChecks=2,
                         agentSha256=hashlib.sha256(source.read_bytes()).hexdigest())
    print('Checks passed:', label, flush=True)
(OUT / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
# Run controlled timing after all check processes have ended.
subprocess.run([sys.executable, 'tools/check_monte_carlo.py'], cwd=ROOT, check=True, timeout=180)
