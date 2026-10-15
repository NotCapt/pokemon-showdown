"""Verify release provenance and summarize measured outcomes without inflation."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
source=sha(root/'submission/agent.py')
control=sha(root/'archive/v4_3_2/agent.py')
team=json.loads((root/'team.json').read_text())
experiment_sources=0
for path in sorted((root/'research').glob('f-*.json')):
    report=json.loads(path.read_text())
    if not isinstance(report,dict) or not report.get('agentFile') or not report.get('agentSha256'):continue
    retained=root/report.get('retainedAgentFile',report['agentFile'])
    assert sha(retained)==report['agentSha256'],f'Experiment source mismatch: {path.name}'
    experiment_sources+=1
selected={}
for label,oldfile in [('confirm','f-control-confirm'),('confirm-mixed','f-control-confirm-mixed'),('stateless','f-control-stateless')]:
    a=json.loads((root/f'research/v4_4-{label}.json').read_text())
    b=json.loads((root/f'research/{oldfile}.json').read_text())
    assert a['agentSha256']==source and b['agentSha256']==control
    assert a['team']==b['team']==team
    for key in ('games','simulatorVersion','sparseBoosts','stateless','opponentPolicySha256'):assert a[key]==b[key]
    assert len(a['results'])==len(b['results'])==a['games']
    changed=0
    for x,y in zip(a['results'],b['results']):
        for key in ('seed','side','baseline','opponentSets'):assert x[key]==y[key]
        assert x['errors']==y['errors']==0
        changed+=x['winner']!=y['winner']
    selected[label]=dict(games=a['games'],wins=a['wins'],controlWins=b['wins'],changedOutcomes=changed,latencyMs=a['latencyMs'])

scenario=json.loads((root/'research/v4_4-hazard-scenario.json').read_text())
old,new=scenario['results']
assert (old['agentSha256'],new['agentSha256'])==(control,source)
assert old['actions'][0]['action']=='switch 3' and new['actions'][0]['action']=='move 2'
assert new['ownHP']>old['ownHP']
for case in (old,new):
    # No previously fainted member may become a living member of the fixture.
    dead=case['warmupObservations'][0]['my_active']['name']
    assert next(p for p in case['initialObservation']['my_team'] if p['name']==dead)['fainted']
cap=json.loads((root/'research/v4_4-cap-scenario.json').read_text())
assert cap['results'][1]['agentSha256']==source and cap['results'][1]['capWinner']=='agent'

portal=json.loads((root/'research/v4_4-portal-result.json').read_text())
proof=json.loads((root/'research/v4_4-portal-result.tested.json').read_text())
assert proof['agentSha256']==source and proof['teamSha256']==sha(root/'team.json') and not proof['probe']
assert portal['success'] and portal['winnerSlot']=='p1'
match=re.search(r'<script[^>]*class="battle-log-data"[^>]*>(.*?)</script>',portal['replayHtml'],re.S)
assert match
log=match.group(1)
assert not re.search(r'invalid|fallback|\|error\|',log,re.I)
(root/'research/v4_4-portal-battle.log').write_text(log,encoding='utf-8')
result=dict(agentSha256=source,controlSha256=control,experimentSourceReportsVerified=experiment_sources,
            selectedArtifactGames=sum(r['games'] for r in selected.values()),
            selected=selected,hazardScenario=dict(controlOwnHP=old['ownHP'],candidateOwnHP=new['ownHP'],
            hpPreserved=new['ownHP']-old['ownHP'],controlWinner=old['capWinner'],candidateWinner=new['capWinner'],
            caveat='Controlled losing position: better HP margin, not a loss-to-win conversion.'),
            portal=dict(battleId=portal['battleId'],turns=portal['turns'],winner=portal['winner']),
            caveat='Scoped hazard-model improvement; matched broad outcomes do not establish an overall win-rate gain. Kaggle search stays pinned to v4.3.2.')
(root/'research/v4_4-summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
