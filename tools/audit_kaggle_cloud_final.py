"""Read-only audit of the frozen cloud final; never execute downloaded code."""
import ast
import hashlib
import json
import math
from pathlib import Path
import zipfile
import team_search as search

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/kaggle-results-v4_3_2/final'
sha=lambda b:hashlib.sha256(b).hexdigest()
result=json.loads((OUT/'result.json').read_text())
record=json.loads((ROOT/'research/kaggle-parallel-notebooks.json').read_text())
assert result['status']=='complete'
bundle_path=ROOT/'dist/REDLINE_Kaggle_Project_v4_3_2.zip'
assert sha(bundle_path.read_bytes())==record['bundleSha256']
with zipfile.ZipFile(bundle_path) as bundle:
    assert result['provenance']['hashes']=={p:sha(bundle.read(p)) for p in result['provenance']['hashes']}
    core=bundle.read('agent_core.py').decode('utf-8').replace('\r\n','\n')
    incumbent=json.loads(bundle.read('team.json'))
    frozen_team=json.loads(bundle.read('archive/v4_3/team.json'))
    frozen_sha=sha(bundle.read('archive/v4_3/agent.py'))
assert result['provenance']['config']['screeningSha256']==sorted(
    sha((OUT.parent/f'redline-screen-{i}.zip').read_bytes()) for i in (1,2,3))
assert result['provenance']['config']==dict(profile='full',seed=43179,mode='finalize',shard_index=0,shard_count=3,
    screeningSha256=result['provenance']['config']['screeningSha256'])
reports={};teams={};sources={};total=0
with zipfile.ZipFile(OUT/'redline-final-checkpoint.zip') as z:
    assert json.loads(z.read('result.json'))==result
    assert json.loads(z.read('manifest.json'))==result['provenance']
    for name in z.namelist():
        if not name.startswith('candidates/') or not name.endswith('/team.json'):continue
        prefix=name.rsplit('/',1)[0];identifier=prefix.split('/')[-1]
        team=json.loads(z.read(name));search.validate(team)
        assert search.digest(team)[:20]==identifier
        source=z.read(prefix+'/agent.py');text=source.decode('utf-8').replace('\r\n','\n')
        assert text.endswith(core)
        own=next(ast.literal_eval(n.value) for n in ast.parse(text).body
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OWN' for t in n.targets))
        assert own=={''.join(c for c in p['name'].lower() if c.isalnum()):p for p in team}
        teams[identifier]=team;sources[identifier]=sha(source)
    expected_games={'development':48,'validation':96,'confirmation':192}
    for name in z.namelist():
        if not name.startswith('jobs/') or not name.endswith('.json'):continue
        report=json.loads(z.read(name));team=report['team'];identifier=search.digest(team)[:20]
        assert report['agentSha256']==sources[identifier] and team==teams[identifier]
        games=report['games'];assert len(report['results'])==games
        phase=next(p for p,g in expected_games.items() if g==games)
        policy=report['results'][0]['baseline'];assert policy in search.POLICIES
        seed=43179+{'development':505,'validation':10000,'confirmation':20000}[phase]
        suite_bytes=z.read(phase+'.json');suite=json.loads(suite_bytes)
        key=search.digest([team,phase,games,policy,seed,search.digest(result['provenance']),sha(suite_bytes)])
        assert name==f'jobs/{key}.json'
        assert report['simulatorVersion']=='0.11.11' and report['sparseBoosts'] and not report['stateless']
        assert report['opponentPolicySha256']==result['provenance']['hashes']['tools/opponents.js']
        for i,row in enumerate(report['results']):
            assert row['game']==i and row['errors']==0 and row['baseline']==policy
            assert row['seed']==[1,2,i//2+1,seed%65536] and row['side']==(2 if i%2 else 1)
            assert row['opponentSets']==(frozen_team if policy=='frozen' else suite[i//2%len(suite)])
        if policy=='frozen':assert report['opponentAgentSha256']==frozen_sha
        assert report['wins']==sum(r['winner']=='agent' for r in report['results'])
        assert report['draws']==sum(not r['winner'] for r in report['results'])
        reports[(phase,identifier,policy)]=report;total+=games
    assert len(teams)==19 and len(reports)==75 and total==result['completedGames']==5040
    selected=result['selected'];identifier=selected['id']
    with zipfile.ZipFile(OUT/'best_candidate.zip') as export:
        assert sorted(export.namelist())==['agent.py','team.txt']
        for name in export.namelist():assert export.read(name)==z.read(f'candidates/{identifier}/{name}')
        assert sha(export.read('agent.py'))==sources[identifier]
    assert (OUT/'best_candidate.zip').read_bytes()==z.read('best_candidate.zip')
    rankings={}
    for phase,round_id,count in [('development',5,19),('validation',0,4),('confirmation',0,2)]:
        ranked=json.loads(z.read(f'{phase}-{round_id}-ranking.json'));assert len(ranked)==count
        for row in ranked:
            rs=[reports[(phase,row['id'],p)] for p in search.POLICIES]
            rates=[(r['wins']+.5*r['draws'])/r['games'] for r in rs]
            assert row['rates']==dict(zip(search.POLICIES,rates))
            assert row['score']==.7*sum(rates)/3+.3*min(rates)
        assert ranked==sorted(ranked,key=search.ranking_key,reverse=True)
        rankings[phase]=ranked
    chosen=next(r for r in rankings['validation'] if not r['incumbent'])
    assert chosen['id']==next(r['id'] for r in result['confirmation'] if not r['incumbent'])
    assert result['selected']==rankings['confirmation'][0]
search.INCUMBENT=incumbent
control_id=search.digest(incumbent)[:20]
recomputed=search.compare_confirmation([reports[('confirmation',control_id,p)] for p in search.POLICIES],
    [reports[('confirmation',chosen['id'],p)] for p in search.POLICIES])
# Python 3.12+ uses improved floating-point summation; tolerate only rounding
# in the mean, while requiring every count, policy score and interval exactly.
mean=recomputed.pop('meanScoreGainPP')
recorded_comparison=dict(result['comparison']);recorded_mean=recorded_comparison.pop('meanScoreGainPP')
assert math.isclose(mean,recorded_mean,rel_tol=0,abs_tol=1e-12)
assert recomputed==recorded_comparison
audit=dict(engineVersion='v4.3.2',checkedGames=total,checkedReports=len(reports),candidateCount=len(teams),
    sourceBundleSha256=record['bundleSha256'],selectedSourceSha256=sources[selected['id']],
    selectedZipSha256=sha((OUT/'best_candidate.zip').read_bytes()),
    resultSha256=sha((OUT/'result.json').read_bytes()),checkpointSha256=sha((OUT/'redline-final-checkpoint.zip').read_bytes()),
    allSchedulesAndCompiledTeamsVerified=True,downloadedCodeExecuted=False)
(OUT/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit,indent=2))
