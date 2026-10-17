"""Prepare two public-history prototypes; do not alter the recommended release."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/robust-rollout-v1'
assert not (OUT / 'manifest.json').exists(), 'Do not rebuild frozen trial inputs'
options = json.loads((ROOT / 'research/options.json').read_text())
data = json.loads((ROOT / 'research/battle_data.json').read_text())
ident = lambda s: ''.join(c for c in s.lower() if c.isalnum())
pp = json.loads(subprocess.check_output(['node', '-e', "const {Dex}=require('pokemon-showdown');const d=require('./research/battle_data.json');process.stdout.write(JSON.stringify(Object.fromEntries(Object.keys(d.moves).map(k=>[k,Math.floor(Dex.moves.get(k).pp*8/5)]))))"], cwd=ROOT, text=True))
defaults, generic = {}, {}
for name, allowed in options['pokemon'].items():
    key = ident(name)
    base = dict(name=name, ability=allowed['defaultAbility'], item=allowed['defaultItem'],
                nature=allowed['defaultNature'] if allowed['defaultNature'] in options['natures'] else 'Impish',
                evs=next(x for x in options['evPresets'] if x.split(' (')[0] == allowed['defaultEvs'].split(' (')[0]),
                moves=allowed['defaultMoves'])
    defaults[key] = base
    generic[key] = []
    for physical, bulky in ((True, False), (False, False), (True, True), (False, True)):
        category = 'Physical' if physical else 'Special'
        attacks = [data['moves'][ident(m)] for m in allowed['legalMoves'] if data['moves'][ident(m)]['category'] == category]
        ranked = sorted(attacks, key=lambda m: (m['base_power'] or 65)*(1.5 if m['type'] in allowed['types'] else 1), reverse=True)
        moves, types = [], set()
        for m in ranked:
            if m['type'] not in types:
                moves.append(m['name']); types.add(m['type'])
            if len(moves) == 4:
                break
        for m in ranked + [data['moves'][ident(x)] for x in allowed['legalMoves']]:
            if len(moves) < 4 and m['name'] not in moves:
                moves.append(m['name'])
        prefix = ('Bulky Attacker' if physical else 'Bulky Special') if bulky else ('Physical Sweeper' if physical else 'Special Sweeper')
        generic[key].append(dict(base, nature=('Adamant' if physical else 'Modest') if bulky else ('Jolly' if physical else 'Timid'),
                                  evs=next(x for x in options['evPresets'] if x.startswith(prefix)),
                                  item='Leftovers' if bulky else 'Life Orb', moves=moves))
for configs in [list(defaults.values())] + list(generic.values()):
    for config in configs:
        legal = options['pokemon'][config['name']]
        assert config['nature'] in options['natures'] and config['evs'] in options['evPresets']
        assert config['item'] in options['items'] and config['ability'] in legal['abilities']
        assert len(set(config['moves'])) == len(config['moves']) == 4
        assert all(m in legal['legalMoves'] for m in config['moves'])
base = (ROOT / 'research/monte-carlo-v1/candidates/phased_mc/agent_core.py').read_text(encoding='utf-8')
assert base.count('        self.mc_last=None') == 1
base = base.replace('        self.mc_last=None', '        self.public_state={}\n        self.mc_last=None')
hook = "        weather=ident(o.get('weather') or '')"
assert base.count(hook) == 1
base = base.replace(hook, '        observe_public(self,a,b,o,turn_no)\n' + hook)
hook = "                m['index']=raw['index']"
assert base.count(hook) == 1
base = base.replace(hook, hook + "\n                if mid=='struggle': m.update(type='???',category='Physical',base_power=50,accuracy=True)")
assert base.count('        return command') == 1
base = base.replace('        return command', '        remember_action(self,command,a,actions,turn_no)\n        return command')
helper = (OUT / 'robust_helpers.py').read_text()
for label in ('guarded', 'aware'):
    folder = OUT / 'candidates' / label
    folder.mkdir(parents=True, exist_ok=True)
    config = '\nPP_MAX = ' + repr(pp) + '\nMC_DEFAULTS = ' + repr(defaults) + '\nMC_GENERIC = ' + repr(generic) + '\nSWITCH_AWARE = ' + repr(label == 'aware') + '\n'
    core = base + config + helper
    ast.parse(core)
    (folder / 'agent_core.py').write_text(core, encoding='utf-8')
    (folder / 'team.json').write_bytes((ROOT / 'archive/v4_7/team.json').read_bytes())
    subprocess.run([sys.executable, 'tools/build_agent.py', '--core', str(folder/'agent_core.py'),
                    '--team', str(folder/'team.json'), '--out', str(folder)], cwd=ROOT, check=True)
    print(label, hashlib.sha256((folder/'agent.py').read_bytes()).hexdigest())
