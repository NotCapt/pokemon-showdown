"""Authorized practice diagnostic: encode booleans using legal move choices.
No exception payloads, environment reads in the uploaded agent, or invalid actions.
"""
import json
import urllib.request
from pathlib import Path
import uuid
root=Path(__file__).resolve().parents[1]
source='''
class PokemonAgent:
    def __init__(self): self.calls=0
    def decide(self, observation):
        o=observation
        self.calls+=1
        if o.get('team_preview'): return 'team 123'
        if o.get('force_switch'):
            s=o.get('valid_switches',[])
            return 'switch '+str(s[0]['index']) if s else 'pass'
        t=o.get('turn',1)
        a=o.get('my_active') or {}
        moves=o.get('valid_moves') or []
        checks=[bool(a.get('boosts')),a.get('boosts',{}).get('def',0)>0,
                self.calls>2,any('pp' in m for m in moves),
                bool(a.get('stats')),bool(a.get('condition')),
                bool(o.get('foe',{}).get('boosts')),bool(a.get('name'))]
        # Turn 1 establishes Iron Defense; subsequent moves encode one bit.
        idx=2 if t==1 else (1 if checks[(t-2)%len(checks)] else 3)
        valid=[m['index'] for m in moves if not m.get('disabled')]
        return 'move '+str(idx if idx in valid else valid[0])
'''
options=json.loads((root/'research/options.json').read_text())['pokemon']
def default(n):
 p=options[n]
 return dict(name=n,item=p['defaultItem'],ability=p['defaultAbility'],nature=p['defaultNature'],evs=p['defaultEvs'],moves=p['defaultMoves'])
team=json.loads((root/'team.json').read_text()); team=[team[2],team[0],team[1]]
# Controlled physical opponent keeps the diagnostic subject alive.
opponent=[default(n) for n in ['Metagross','Snorlax','Ferrothorn']]
fields={'p1Name':'Contract Test','p2Name':'Control','p1_custom_team':json.dumps(team),'p2_custom_team':json.dumps(opponent),'p2Sample':'q_learning_agent.py'}
boundary='---'+uuid.uuid4().hex
body=b''.join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k,v in fields.items())
body+=f'--{boundary}\r\nContent-Disposition: form-data; name="p1_file"; filename="contract.py"\r\nContent-Type: text/x-python\r\n\r\n{source}\r\n--{boundary}--\r\n'.encode()
req=urllib.request.Request('https://redline-aresxshunya.netlify.app/api/simulate-ml',data=body,headers={'Content-Type':'multipart/form-data; boundary='+boundary})
try:
 with urllib.request.urlopen(req,timeout=120) as response: result=json.load(response)
except urllib.error.HTTPError as exc:
 result=json.loads(exc.read())
(root/'research/contract-result.json').write_text(json.dumps(result),encoding='utf-8')
html=result.get('replayHtml','');start=html.find('|t:|');log=html[start:html.find('</script>',start)]
print('\n'.join(x for x in log.splitlines() if x.startswith(('|turn|','|move|p1','|-boost|p1','|switch|p1'))))
print({k:v for k,v in result.items() if k!='replayHtml'})
