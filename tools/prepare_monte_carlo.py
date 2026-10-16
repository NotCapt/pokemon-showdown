"""Build separate Monte Carlo candidates without modifying the submission."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/monte-carlo-v1'
helper = (OUT / 'rollout_helpers.py').read_text(encoding='utf-8')
options = json.loads((ROOT / 'research/options.json').read_text())
priors = json.loads((ROOT / 'research/enemy_sets.json').read_text())
legal_priors = {}
for key, sets in priors.items():
    for config in sets:
        legal = options['pokemon'][config['name']]
        if (config['ability'] in legal['abilities'] and config['item'] in options['items']
                and config['nature'] in options['natures'] and config['evs'] in options['evPresets']
                and len(config['moves']) == len(set(config['moves'])) == 4
                and all(move in legal['legalMoves'] for move in config['moves'])):
            legal_priors.setdefault(key, []).append(config)
helper = 'MC_PRIORS = ' + repr(legal_priors) + '\n\n' + helper
bases = dict(control=ROOT / 'archive/v4_6', phased=ROOT / 'research/phantom-forecast-v1/candidates/phased')
hashes = {}
for label, base_label in [('control', 'control'), ('phased', 'phased'), ('mc', 'control'), ('phased_mc', 'phased')]:
    base = bases[base_label]
    core = (base / 'agent_core.py').read_text(encoding='utf-8')
    if label in ('mc', 'phased_mc'):
        assert core.count('class PokemonAgent:') == 1
        core = core.replace('class PokemonAgent:', helper + '\n\nclass PokemonAgent:')
        core = core.replace('        self.last_switch_turn=-100', '        self.mc_last=None\n        self.last_switch_turn=-100')
        before = '        command=max(scored,key=lambda v:v[0])[1]'
        assert core.count(before) == 1
        core = core.replace(before, '        command=monte_carlo_choice(self,scored,actions,a,b,weather,turn_no,o,switches)')
    ast.parse(core)
    folder = OUT / 'candidates' / label
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'agent_core.py'
    if (OUT / 'manifest.json').exists():
        assert path.read_text(encoding='utf-8') == core, 'Frozen source changed'
    else:
        path.write_text(core, encoding='utf-8')
    (folder / 'team.json').write_bytes((base / 'team.json').read_bytes())
    subprocess.run([sys.executable, 'tools/build_agent.py', '--core', str(path), '--team', str(folder / 'team.json'), '--out', str(folder)], cwd=ROOT, check=True)
    hashes[label] = hashlib.sha256((folder / 'agent.py').read_bytes()).hexdigest()
for label, base in bases.items():
    assert (OUT / 'candidates' / label / 'agent.py').read_bytes() == (base / 'agent.py').read_bytes()
print(json.dumps(hashes, indent=2))
