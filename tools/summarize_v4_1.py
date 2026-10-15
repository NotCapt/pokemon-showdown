"""Verify release provenance and matched-control benchmark schedules."""
import hashlib
import json
from pathlib import Path
import random
import re

ROOT=Path(__file__).resolve().parents[1]
digest=hashlib.sha256((ROOT/'submission/agent.py').read_bytes()).hexdigest()
old_digest=hashlib.sha256((ROOT/'archive/v4/agent.py').read_bytes()).hexdigest()
reports={}
for label,new,old in [
    ('development','v5-memory-mixed.json','v4-control-mixed-v5.json'),
    ('holdout','v5-memory-holdout.json','v4-control-holdout-v5.json'),
    ('custom','v5-memory-custom.json','v4-arcanine-final-custom.json'),
    ('stateless','v5-memory-stateless.json','v4-arcanine-stateless.json')]:
    a,b=[json.loads((ROOT/'research'/name).read_text()) for name in (new,old)]
    assert a['agentSha256']==digest and b['agentSha256']==old_digest
    assert a['team']==b['team']==json.loads((ROOT/'team.json').read_text())
    assert len(a['results'])==len(b['results'])
    deltas=[]
    for x,y in zip(a['results'],b['results']):
        assert all(x[k]==y[k] for k in ('seed','side','opponentSets','baseline'))
        assert x['errors']==y['errors']==0
        deltas.append(int(x['winner']=='agent')-int(y['winner']=='agent'))
    pairs=[sum(deltas[i:i+2])/2 for i in range(0,len(deltas),2)]
    rng=random.Random(8741)
    boot=sorted(sum(rng.choice(pairs) for _ in pairs)/len(pairs) for _ in range(5000))
    reports[label]=dict(games=a['games'],releaseWins=a['wins'],v4Wins=b['wins'],
                        gainPercentagePoints=100*sum(deltas)/len(deltas),
                        pairedBootstrap95GainPP=[100*boot[125],100*boot[4874]],
                        improvedGames=deltas.count(1),regressedGames=deltas.count(-1),
                        latencyMs=a['latencyMs'])
result=dict(agentSha256=digest,controlSha256=old_digest,
            method='5000 bootstrap replicates of side-reversed two-game pairs; seed 8741. Mixed policies are simple baselines. Not tournament win probabilities.',
            reports=reports)
(ROOT/'research/v4_1-summary.json').write_text(json.dumps(result,indent=2))
portal=json.loads((ROOT/'research/portal-result.json').read_text())
(ROOT/'research/v4_1-portal-result.json').write_text(json.dumps(portal,indent=2))
html=portal['replayHtml']
(ROOT/'research/v4_1-portal-replay.html').write_text(html,encoding='utf-8')
match=re.search(r'<script[^>]*class="battle-log-data"[^>]*>(.*?)</script>',html,re.S)
if match: (ROOT/'research/v4_1-portal-battle.log').write_text(match.group(1),encoding='utf-8')
(ROOT/'research/v4_1-portal-tested.json').write_text(json.dumps(dict(agentSha256=digest,team=json.loads((ROOT/'team.json').read_text()),battleId=portal['battleId']),indent=2))
print(json.dumps(result,indent=2))
