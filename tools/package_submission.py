import hashlib
import json
import argparse
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--name',default='REDLINE_Search')
args=parser.parse_args()
assert args.name and all(c.isalnum() or c in '_-' for c in args.name), 'Use a simple archive name.'
team=json.loads((root/'team.json').read_text())
options=json.loads((root/'research/options.json').read_text())
assert len(team)==3 and len({p['name'] for p in team})==3
for p in team:
    r=options['pokemon'][p['name']]
    assert p['ability'] in r['abilities']
    assert p['item'] in options['items'] and p['nature'] in options['natures']
    assert p['evs'] in options['evPresets']
    assert 1<=len(p['moves'])<=4 and len(set(p['moves']))==len(p['moves'])
    assert all(m in r['legalMoves'] for m in p['moves'])
out=root/'dist';out.mkdir(exist_ok=True)
with zipfile.ZipFile(out/(args.name+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
    for name in ('agent.py','team.txt'):
        archive.write(root/'submission'/name,name)
manifest={name:hashlib.sha256((root/'submission'/name).read_bytes()).hexdigest() for name in ('agent.py','team.txt')}
(out/(args.name+'-manifest.json')).write_text(json.dumps(manifest,indent=2))
print('Team legality verified against downloaded portal options. ZIP contains agent.py and team.txt only.')
print(json.dumps(manifest,indent=2))
