"""Verify release/control provenance, normal-game equivalence and portal proof."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
digest=hashlib.sha256((root/'submission/agent.py').read_bytes()).hexdigest()
old=hashlib.sha256((root/'archive/v4_1/agent.py').read_bytes()).hexdigest()
summaries={}
for label,new,control in [
    ('mixed','v4_2-cap-mixed.json','v5-memory-holdout.json'),
    ('adaptive','v4_2-cap-adaptive.json','v4_1-adaptive-holdout.json'),
    ('custom','v4_2-cap-custom.json','v5-memory-custom.json'),
    ('stateless','v4_2-cap-stateless.json','v5-memory-stateless.json')]:
    a,b=[json.loads((root/'research'/name).read_text()) for name in (new,control)]
    assert a['agentSha256']==digest and b['agentSha256']==old
    assert a['team']==b['team']==json.loads((root/'team.json').read_text())
    assert a['games']==b['games']==len(a['results'])==len(b['results'])
    for x,y in zip(a['results'],b['results']):
        assert all(x[k]==y[k] for k in ('game','seed','side','opponentSets','baseline','winner','turns'))
        assert x['errors']==y['errors']==0 and x['turns']<98
    summaries[label]=dict(games=a['games'],releaseWins=a['wins'],v4_1Wins=b['wins'],latencyMs=a['latencyMs'],identicalGameOutcomes=True)
case=json.loads((root/'research/cap-scenario.json').read_text())
assert case['results'][0]['agentSha256']==old and case['results'][1]['agentSha256']==digest
assert case['results'][0]['capWinner']=='enemy' and case['results'][1]['capWinner']=='agent'
result=dict(agentSha256=digest,controlSha256=old,games=sum(r['games'] for r in summaries.values()),reports=summaries,capScenario=case)
(root/'research/v4_2-summary.json').write_text(json.dumps(result,indent=2))
portal=json.loads((root/'research/portal-result.json').read_text())
assert portal['success'] and portal['winnerSlot']=='p1'
(root/'research/v4_2-portal-result.json').write_text(json.dumps(portal,indent=2))
(root/'research/v4_2-portal-replay.html').write_text(portal['replayHtml'],encoding='utf-8')
match=re.search(r'<script[^>]*class="battle-log-data"[^>]*>(.*?)</script>',portal['replayHtml'],re.S)
assert match
log=match.group(1)
assert not re.search(r'invalid|fallback|\|error\|',log,re.I)
(root/'research/v4_2-portal-battle.log').write_text(log,encoding='utf-8')
(root/'research/v4_2-portal-tested.json').write_text(json.dumps(dict(agentSha256=digest,team=json.loads((root/'team.json').read_text()),battleId=portal['battleId']),indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='capScenario'},indent=2))
