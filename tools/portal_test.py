"""One practice simulation via the same public form endpoint used by the UI."""
import json
from pathlib import Path
import urllib.request
import uuid
import argparse
import hashlib
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--probe',action='store_true')
parser.add_argument('--out',help='Result path relative to the repository')
parser.add_argument('--source',default='submission',help='Directory containing the exact agent.py to test')
parser.add_argument('--team',default='team.json',help='Exact JSON team compiled into that agent')
args=parser.parse_args()
source_dir=root/args.source
team_path=root/args.team
boundary='----Redline'+uuid.uuid4().hex
fields={'p1Name':'REDLINE Search','p2Name':'Sample Baseline','p1_custom_team':team_path.read_text(),
        'p2_custom_team':json.dumps([dict(name=n,ability=p['defaultAbility'],item=p['defaultItem'],nature=p['defaultNature'],evs=p['defaultEvs'],moves=p['defaultMoves']) for n,p in json.loads((root/'research/options.json').read_text())['pokemon'].items() if n in ['Garchomp','Metagross','Volcarona']]),'p2Sample':'q_learning_agent.py'}
parts=[]
for name,value in fields.items():
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
source=(source_dir/'agent.py').read_bytes()
if args.probe:
    source+=b'\nimport json\n_OriginalAgent=PokemonAgent\nclass PokemonAgent(_OriginalAgent):\n def decide(self, observation):\n  if observation.get("turn",0)>=4:\n   return "OBSERVATION_PROBE: "+json.dumps(observation)\n  return super().decide(observation)\n'
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="p1_file"; filename="agent.py"\r\nContent-Type: text/x-python\r\n\r\n'.encode()+source+b'\r\n')
parts.append(f'--{boundary}--\r\n'.encode())
request=urllib.request.Request('https://redline-aresxshunya.netlify.app/api/simulate-ml',data=b''.join(parts),headers={'Content-Type':'multipart/form-data; boundary='+boundary})
try:
    with urllib.request.urlopen(request,timeout=120) as res: body=res.read()
except urllib.error.HTTPError as exc: body=exc.read()
out=root/(args.out or ('research/portal-probe.json' if args.probe else 'research/portal-result.json'))
out.write_bytes(body)
out.with_suffix('.tested.json').write_text(json.dumps(dict(agentSha256=hashlib.sha256(source).hexdigest(),
    teamSha256=hashlib.sha256(team_path.read_bytes()).hexdigest(),probe=args.probe),indent=2))
result=json.loads(body)
print(json.dumps({k:v for k,v in result.items() if k!='replayHtml'},indent=2))
