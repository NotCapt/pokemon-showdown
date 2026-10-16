"""Audit the follow-up and its shared, already audited reference cohorts."""
import json
from pathlib import Path

import evaluate_roster_forecast as e

ROOT=e.ROOT;OUT=ROOT/'research/phantom-forecast-v1';REF=ROOT/'research/roster-forecast-v1'
m=e.load(OUT/'manifest.json');r=e.load(OUT/'result.json');e.verify(m)
assert e.load(REF/'audit.json')['allSourcesSchedulesAndScoresVerified']
assert e.sha(REF/'manifest.json')==m['referenceManifestSha256']
assert e.sha(OUT/'manifest.json')==r['manifestSha256']
execution=e.load(OUT/'execution.json')
for key,path in [('evaluatorSha256',ROOT/'tools/evaluate_phased_forecast.py'),('checksSha256',OUT/'checks.json'),
                 ('mechanicsSha256',OUT/'mechanics.json'),('oracleSha256',OUT/'oracle.json')]:assert execution[key]==e.sha(path)
assert e.load(OUT/'checks.json')['passed'] and e.load(OUT/'checks.json')['agentSha256']==m['candidateSha256']['phased']
comparisons={};games=reports=0
for phase in ('validation','confirmation'):
    records=[]
    for spec in m['jobs'][phase]:
        path=OUT/'jobs'/f'{phase}-phased-{spec["key"]}.json'
        assert e.load(path.with_suffix('.stamp.json'))==dict(manifestSha256=r['manifestSha256'],candidateSha256=r['sourceSha256'],phase=phase,specification=spec)
        x=e.load(path)
        assert x['agentSha256']==r['sourceSha256'] and x['games']==len(x['results'])==spec['games']
        assert x['team']==e.load(OUT/'candidates/phased/team.json')
        assert x['sparseBoosts'] and not x['stateless'] and x['simulatorVersion']=='0.11.11'
        assert x['opponentPolicySha256']==m['inputSha256']['tools/opponents.js']
        suite=e.load(OUT/spec['teamFile'])
        if spec['opponentId']:assert x['opponentAgentSha256']==e.sha(OUT/'opponents'/spec['opponentId']/'agent.py')
        for i,row in enumerate(x['results']):
            assert row['errors']==0 and row['game']==i and row['baseline']==spec['policy']
            assert row['seed']==[1,2,i//2+1,spec['seed']%65536] and row['side']==(2 if i%2 else 1)
            assert row['opponentSets']==(suite if spec['opponentId'] else suite[i//2])
        assert x['wins']==sum(row['winner']=='agent' for row in x['results'])
        assert x['draws']==sum(not row['winner'] for row in x['results'])
        records.append((spec,x));games+=x['games'];reports+=1
    assert e.aggregate('phased',records)==e.load(OUT/(phase+'-score.json'))
    comparisons[phase]={label:e.scoring.compare([(j,e.load(REF/'jobs'/f'{phase}-{label}-{j["key"]}.json')) for j in m['jobs'][phase]],records) for label in ('control','recovery')}
assert comparisons==r['comparisons'] and games==1296 and reports==108
strength=all(row['weightedGainPP']>0 and row['pairedInterval95'][0]>0 and all(s['scoreGainPP']>=-5 for s in row['categories'].values()) for row in comparisons['confirmation'].values())
c=comparisons['confirmation']['control']
correctness=c['weightedGainPP']>=0 and c['pairedInterval95'][0]>-3 and all(row['scoreGainPP']>=-2 for phase in comparisons.values() for row in phase['control']['categories'].values())
assert r['promoteStrength']==strength and r['promoteCorrectness']==correctness
audit=dict(checkedNewGames=games,checkedNewReports=reports,sharedReferenceAuditSha256=e.sha(REF/'audit.json'),
           sourceSha256=r['sourceSha256'],allSourcesSchedulesAndScoresVerified=True,
           promoteStrength=strength,promoteCorrectness=correctness,referenceGamesNotRecounted=True)
e.write(OUT/'audit.json',audit);print(json.dumps(audit,indent=2))
