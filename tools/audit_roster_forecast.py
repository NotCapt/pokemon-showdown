"""Recompute every schedule, score and gate before considering a policy release."""
import ast
import json
from pathlib import Path
import subprocess
import sys

import evaluate_roster_forecast as run

ROOT,OUT=run.ROOT,run.OUT
load=run.load
m=load(OUT/'manifest.json');run.verify(m)
assert m['primaryGames']==4752 and m['generatedOpponents']==504
source_hashes={label:run.sha(OUT/'candidates'/label/'agent.py') for label in m['candidates']}
assert source_hashes==m['candidateSha256']
for label in m['candidates']:
    folder=OUT/'candidates'/label
    tree=ast.parse((folder/'agent.py').read_text(encoding='utf-8'))
    own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='OWN' for t in n.targets))
    team=load(folder/'team.json');run.team_search.validate(team)
    assert list(own.values())==team
    assert (folder/'agent.py').read_text(encoding='utf-8').endswith((folder/'agent_core.py').read_text(encoding='utf-8'))
evidence={};games=reports=0
for phase,labels in [('development',run.LABELS),('validation',('control','recovery','combined')),('confirmation',('control','recovery','combined'))]:
    recomputed=[]
    for label in labels:
        rows=[]
        for spec in m['jobs'][phase]:
            path=OUT/'jobs'/f'{phase}-{label}-{spec["key"]}.json'
            signature=dict(manifestSha256=run.sha(OUT/'manifest.json'),candidateSha256=source_hashes[label],phase=phase,specification=spec)
            assert load(path.with_suffix('.stamp.json'))==signature
            r=load(path);assert r['agentSha256']==source_hashes[label]
            assert r['team']==load(OUT/'candidates'/label/'team.json')
            assert r['games']==len(r['results'])==spec['games'] and r['simulatorVersion']=='0.11.11'
            assert r['sparseBoosts'] and not r['stateless']
            assert r['opponentPolicySha256']==m['inputSha256']['tools/opponents.js']
            suite=load(OUT/spec['teamFile'])
            if spec['opponentId']:
                assert r['opponentAgentSha256']==run.sha(OUT/'opponents'/spec['opponentId']/'agent.py')
            for i,row in enumerate(r['results']):
                assert row['game']==i and row['errors']==0 and row['baseline']==spec['policy']
                assert row['seed']==[1,2,i//2+1,spec['seed']%65536] and row['side']==(2 if i%2 else 1)
                assert row['opponentSets']==(suite if spec['opponentId'] else suite[i//2])
            assert r['wins']==sum(x['winner']=='agent' for x in r['results'])
            assert r['draws']==sum(not x['winner'] for x in r['results'])
            assert r['losses']==sum(x['winner']=='baseline' for x in r['results'])
            games+=r['games'];reports+=1;rows.append((spec,r))
        evidence[phase,label]=rows;recomputed.append(run.aggregate(label,rows))
    recomputed.sort(key=lambda r:(r['score'],r['hpMargin'],{'recovery':3,'combined':2,'roster':1,'control':0}[r['id']]),reverse=True)
    assert recomputed==load(OUT/(phase+'-ranking.json'))
assert games==4752 and reports==492
result=load(OUT/'result.json');assert result['manifestSha256']==run.sha(OUT/'manifest.json')
comparisons={phase:{a+'-vs-'+b:run.scoring.compare(evidence[phase,b],evidence[phase,a]) for a,b in
             [('recovery','control'),('combined','control'),('combined','recovery')]} for phase in ('validation','confirmation')}
assert comparisons==result['comparisons']
strength=all(comparisons['confirmation'][key]['weightedGainPP']>0 and comparisons['confirmation'][key]['pairedInterval95'][0]>0
             for key in ('combined-vs-control','combined-vs-recovery')) and all(r['scoreGainPP']>=-5 for phase in comparisons.values()
             for key in ('combined-vs-control','combined-vs-recovery') for r in phase[key]['categories'].values())
c=comparisons['confirmation']['recovery-vs-control']
correctness=c['weightedGainPP']>=0 and c['pairedInterval95'][0]>-3 and all(r['scoreGainPP']>=-2 for phase in comparisons.values()
             for r in phase['recovery-vs-control']['categories'].values())
assert result['promoteStrength']==strength and result['promoteCorrectness']==correctness
assert result['selected']==('combined' if strength else 'recovery' if correctness else 'control')
properties={}
for label in ('control','recovery','roster','combined'):
    command=[sys.executable,'tools/check_recovery_forecast.py','--agent',str(OUT/'candidates'/label/'agent.py')]
    if label in ('recovery','combined'):command.append('--require-fixed')
    check=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True)
    properties[label]=json.loads(check.stdout)
audit=dict(manifestSha256=result['manifestSha256'],checkedGames=games,checkedReports=reports,
           allSourcesSchedulesAndScoresVerified=True,sourceSha256=source_hashes,recoveryProperties=properties,
           promoteStrength=strength,promoteCorrectness=correctness,selected=result['selected'])
run.write(OUT/'audit.json',audit)
print(json.dumps(audit,indent=2))
