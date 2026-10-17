"""Verify the preserved interrupted/futile trials without a promotion claim."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof={}
for version,expected in [('v1',376),('v2',792),('v3',1000)]:
    folder=ROOT/'research'/('robust-rollout-'+version);m=load(folder/'manifest.json');groups={};games=reports=0
    for name,digest in m['inputSha256'].items():assert sha(ROOT/name)==digest,name
    report_names={p.stem for p in (folder/'jobs').glob('*.json') if not p.name.endswith('.stamp.json')}
    stamp_names={p.name.removesuffix('.stamp.json') for p in (folder/'jobs').glob('*.stamp.json')}
    assert report_names==stamp_names,'Unmatched finalized result or provenance stamp: '+version
    for path in (folder/'jobs').glob('*.stamp.json'):
        stamp=load(path);name=path.name.removesuffix('.stamp.json');r=load(path.with_name(name+'.json'))
        phase=stamp['phase'];spec=stamp['specification']
        label=next(s for s in m['candidateSha256'] if name.startswith(phase+'-'+s+'-'))
        assert spec in m['jobs'][phase] and name==phase+'-'+label+'-'+spec['key']
        assert stamp==dict(manifestSha256=sha(folder/'manifest.json'),candidateSha256=m['candidateSha256'][label],phase=phase,specification=spec)
        assert r['agentSha256']==m['candidateSha256'][label] and r['games']==len(r['results'])==spec['games']
        assert r['team']==load(folder/'candidates'/label/'team.json')
        assert r['simulatorVersion']=='0.11.11' and r['sparseBoosts'] and not r['stateless']
        assert r['opponentPolicySha256']==m['inputSha256']['tools/opponents.js']
        suite=load(folder/spec['teamFile'])
        if spec['opponentId']:assert r['opponentAgentSha256']==sha(folder/'opponents'/spec['opponentId']/'agent.py')
        for i,row in enumerate(r['results']):
            assert row['game']==i and row['baseline']==spec['policy']
            assert row['errors']==0 and row['seed']==[1,2,i//2+1,spec['seed']] and row['side']==(2 if i%2 else 1)
            assert row['opponentSets']==(suite if spec['opponentId'] else suite[i//2])
        assert r['wins']==sum(x['winner']=='agent' for x in r['results'])
        assert r['losses']==sum(x['winner']=='baseline' for x in r['results'])
        assert r['draws']==sum(not x['winner'] for x in r['results'])
        groups.setdefault((phase,label,spec['category']),[]).extend(r['results']);games+=r['games'];reports+=1
    assert games==expected
    record=dict(completedReports=reports,completedGames=games,allRetainedSourcesSchedulesAndOutcomesVerified=True,excludedFromV4StrengthEstimates=True)
    if version in ('v2','v3'):
        means={key:sum(1 if x['winner']=='agent' else .5 if not x['winner'] else 0 for x in rows)/len(rows) for key,rows in groups.items()}
        labels=('guarded','aware') if version=='v2' else ('margin','cycle')
        failures={s:{c:100*(means['validation',s,c]-means['validation','control',c]) for c in ('adaptive','strong','league')
                     if 100*(means['validation',s,c]-means['validation','control',c])<(-5 if c=='league' else -2)} for s in labels}
        assert all(failures.values()) and failures==load(folder/'futility.json')['failedCompletedCategoryGainsPP']
        record['failedCategoryGuardsVerified']=failures
    else:assert load(folder/'aborted.json')['status']=='aborted'
    proof[version]=record
destination=ROOT/'research/robust-rollout-v4/history-audit.json'
destination.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
