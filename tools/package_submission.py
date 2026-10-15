import hashlib
import json
import argparse
import ast
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--name',default='REDLINE_Search')
parser.add_argument('--source',default='submission',help='Directory containing the tested agent.py and team.txt')
parser.add_argument('--team',default='team.json',help='Exact configuration compiled into the tested agent')
args=parser.parse_args()
assert args.name and all(c.isalnum() or c in '_-' for c in args.name), 'Use a simple archive name.'
team=json.loads((root/args.team).read_text())
source=root/args.source
options=json.loads((root/'research/options.json').read_text())
assert len(team)==3 and len({p['name'] for p in team})==3
for p in team:
    r=options['pokemon'][p['name']]
    assert p['ability'] in r['abilities']
    assert p['item'] in options['items'] and p['nature'] in options['natures']
    assert p['evs'] in options['evPresets']
    assert 1<=len(p['moves'])<=4 and len(set(p['moves']))==len(p['moves'])
    assert all(m in r['legalMoves'] for m in p['moves'])
tree=ast.parse((source/'agent.py').read_text(encoding='utf-8'))
own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OWN' for t in n.targets))
assert own=={''.join(c for c in p['name'].lower() if c.isalnum()):p for p in team}, 'Agent own-team configuration does not match --team'
lines=[]
for p in team:
    lines += [p['name']+' @ '+p['item'],'Ability: '+p['ability'],'EVs: '+p['evs'].split('(')[-1].rstrip(')'),p['nature']+' Nature']+['- '+m for m in p['moves']]+['']
assert (source/'team.txt').read_text(encoding='utf-8')=='\n'.join(lines), 'team.txt does not match --team'
out=root/'dist';out.mkdir(exist_ok=True)
with zipfile.ZipFile(out/(args.name+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
    for name in ('agent.py','team.txt'):
        archive.write(source/name,name)
manifest={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ('agent.py','team.txt')}
(out/(args.name+'-manifest.json')).write_text(json.dumps(manifest,indent=2))
print('Team legality verified against downloaded portal options. ZIP contains agent.py and team.txt only.')
print(json.dumps(manifest,indent=2))
