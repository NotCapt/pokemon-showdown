"""One practice simulation via the same public form endpoint used by the UI."""
import json
from pathlib import Path
import urllib.request
import uuid
import sys
root=Path(__file__).resolve().parents[1]
boundary='----Redline'+uuid.uuid4().hex
fields={'p1Name':'REDLINE Search','p2Name':'Sample Baseline','p1_custom_team':(root/'team.json').read_text(),
        'p2_custom_team':json.dumps([dict(name=n,ability=p['defaultAbility'],item=p['defaultItem'],nature=p['defaultNature'],evs=p['defaultEvs'],moves=p['defaultMoves']) for n,p in json.loads((root/'research/options.json').read_text())['pokemon'].items() if n in ['Garchomp','Metagross','Volcarona']]),'p2Sample':'q_learning_agent.py'}
parts=[]
for name,value in fields.items():
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
source=(root/'submission/agent.py').read_bytes()
if '--probe' in sys.argv:
    source+=b'\nimport json\n_OriginalAgent=PokemonAgent\nclass PokemonAgent(_OriginalAgent):\n def decide(self, observation):\n  if observation.get("turn",0)>=4:\n   return "OBSERVATION_PROBE: "+json.dumps(observation)\n  return super().decide(observation)\n'
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="p1_file"; filename="agent.py"\r\nContent-Type: text/x-python\r\n\r\n'.encode()+source+b'\r\n')
parts.append(f'--{boundary}--\r\n'.encode())
request=urllib.request.Request('https://redline-aresxshunya.netlify.app/api/simulate-ml',data=b''.join(parts),headers={'Content-Type':'multipart/form-data; boundary='+boundary})
try:
    with urllib.request.urlopen(request,timeout=120) as res: body=res.read()
except urllib.error.HTTPError as exc: body=exc.read()
(root/('research/portal-probe.json' if '--probe' in sys.argv else 'research/portal-result.json')).write_bytes(body)
result=json.loads(body)
print(json.dumps({k:v for k,v in result.items() if k!='replayHtml'},indent=2))
