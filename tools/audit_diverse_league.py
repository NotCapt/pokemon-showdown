"""Audit the frozen league inputs, then the exact completed battle schedules."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

import evaluate_diverse_league as league
import team_search as search

p=argparse.ArgumentParser();p.add_argument('--out',default='research/diverse-league-v1')
p.add_argument('--preflight',action='store_true');args=p.parse_args()
ROOT=league.ROOT;OUT=(ROOT/args.out).resolve()
manifest=json.loads((OUT/'manifest.json').read_text())
sha=league.sha
if (OUT/'execution-adapter.json').exists():
    adapter=json.loads((OUT/'execution-adapter.json').read_text())
    assert adapter['manifestSha256']==sha(OUT/'manifest.json')
    assert adapter['evaluationScriptSha256']==manifest['inputSha256']['tools/evaluate_diverse_league.py']
    assert adapter['adapterSha256']==sha(OUT/'reference/writer-adapter.py')==sha(ROOT/'tools/run_diverse_league.py')
assert manifest['weights']==league.WEIGHTS=={'adaptive':.4,'tactical':.2,'league':.4}
assert len(manifest['candidates'])==25 and len(manifest['opponents'])==12
assert len({league.team_id(t) for t in manifest['opponents']})==12
assert {p['name'] for t in manifest['opponents'] for p in t}==set(search.OPTIONS['pokemon'])
core=(OUT/'reference/agent_core.py').read_text(encoding='utf-8')
assert sha(OUT/'reference/agent_core.py')==manifest['inputSha256']['agent_core.py']
assert sha(OUT/'reference/agent.py')==manifest['inputSha256']['submission/agent.py']
for path,digest in manifest['inputSha256'].items():
    if args.preflight or path not in ('agent_core.py','team.json','submission/agent.py','submission/team.txt'):
        assert sha(ROOT/path)==digest,'Input changed: '+path
teams={league.team_id(t):t for t in manifest['candidates']}
for identifier,team in teams.items():
    search.validate(team);folder=OUT/'candidates'/identifier
    assert json.loads((folder/'team.json').read_text())==team
    source=(folder/'agent.py').read_text(encoding='utf-8');assert source.endswith(core)
    own=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=='OWN' for t in n.targets))
    assert own=={''.join(c for c in p['name'].lower() if c.isalnum()):p for p in team}
    assert sha(folder/'agent.py')==manifest['candidateSha256'][identifier]
assert manifest['candidateSha256'][manifest['incumbentId']]==sha(OUT/'reference/agent.py')
for path,digest in manifest['suiteSha256'].items():assert sha(OUT/path)==digest
generated=set();counts={};roster={league.team_id(t):t for t in manifest['opponents']}
for phase,jobs in manifest['jobs'].items():
    assert len({j['key'] for j in jobs})==len(jobs)
    counts[phase]=sum(j['games'] for j in jobs)
    for j in jobs:
        data=json.loads((OUT/j['teamFile']).read_text())
        if j['category']=='league':
            rotation=int(j['key'][-1]);team=roster[j['opponentId']]
            assert data==team[rotation:]+team[:rotation]
        else:
            assert j['games']==24 and len(data)==12
            for t in data:
                search.validate(t);key=search.digest(t)
                assert key not in generated,'Reused generated set across phases or policies'
                generated.add(key)
assert counts=={'qualification':216,'validation':432,'confirmation':864}
assert sum(counts[p]*n for p,n in [('qualification',25),('validation',4),('confirmation',2)])==manifest['maxScheduledGames']==8856
preflight=dict(candidates=25,fixedRosters=12,coveredSpecies=24,distinctGeneratedOpponents=len(generated),
    gamesPerCandidate=counts,plannedGames=8856,incumbentScoreWeight=.4/12,
    frozenEngineSha256=manifest['inputSha256']['agent_core.py'],manifestSha256=sha(OUT/'manifest.json'))
if args.preflight:
    league.write(OUT/'preflight.json',preflight);print(json.dumps(preflight,indent=2));raise SystemExit

result=json.loads((OUT/'result.json').read_text())
assert result['status']=='complete' and result['manifestSha256']==sha(OUT/'manifest.json')
evidence={};total=0;report_count=0;rankings={}
for phase,n in [('qualification',25),('validation',4),('confirmation',2)]:
    ranked=json.loads((OUT/(phase+'-ranking.json')).read_text());assert len(ranked)==n
    assert ranked==sorted(ranked,key=league.ranking_key,reverse=True)
    rankings[phase]=ranked
    for record in ranked:
        identifier=record['id'];rows=[]
        for spec in manifest['jobs'][phase]:
            path=OUT/'jobs'/f'{phase}-{identifier}-{spec["key"]}.json'
            report=json.loads(path.read_text());stamp=json.loads(path.with_suffix('.stamp.json').read_text())
            assert stamp==dict(manifestSha256=sha(OUT/'manifest.json'),candidateSha256=manifest['candidateSha256'][identifier],phase=phase,specification=spec)
            assert report['agentSha256']==manifest['candidateSha256'][identifier] and report['team']==teams[identifier]
            assert report['games']==len(report['results'])==spec['games']
            assert report['opponentPolicySha256']==manifest['inputSha256']['tools/opponents.js']
            assert report['simulatorVersion']=='0.11.11' and report['sparseBoosts'] and not report['stateless']
            suite=json.loads((OUT/spec['teamFile']).read_text())
            for i,row in enumerate(report['results']):
                assert row['game']==i and row['errors']==0 and row['baseline']==spec['policy']
                assert row['seed']==[1,2,i//2+1,spec['seed']%65536] and row['side']==(2 if i%2 else 1)
                assert row['opponentSets']==(suite if spec['opponentId'] else suite[i//2])
            if spec['opponentId']:assert report['opponentAgentSha256']==manifest['candidateSha256'][spec['opponentId']]
            assert report['wins']==sum(r['winner']=='agent' for r in report['results'])
            assert report['draws']==sum(not r['winner'] for r in report['results'])
            assert report['losses']==sum(r['winner']=='baseline' for r in report['results'])
            rows.append((spec,report));total+=report['games'];report_count+=1
        assert league.aggregate(identifier,phase,rows,manifest)==record
        evidence[(phase,identifier)]=rows
expected=[manifest['incumbentId']]+[r['id'] for r in rankings['qualification'] if not r['incumbent']][:3]
assert result['validationCandidates']==expected
assert {r['id'] for r in rankings['validation']}==set(expected)
challenger=next(r for r in rankings['validation'] if not r['incumbent'])
assert {r['id'] for r in rankings['confirmation']}=={manifest['incumbentId'],challenger['id']}
assert result['challenger']==next(r for r in rankings['confirmation'] if not r['incumbent'])
assert result['incumbent']==next(r for r in rankings['confirmation'] if r['incumbent'])
comparison=league.compare(evidence[('confirmation',manifest['incumbentId'])],evidence[('confirmation',challenger['id'])])
assert comparison==result['comparison']
promote=(result['challenger']['score']>result['incumbent']['score'] and comparison['pairedInterval95'][0]>0
         and all(c['scoreGainPP']>=-5 for c in comparison['categories'].values()))
assert promote==result['promote']
assert result['selected']==(result['challenger'] if promote else result['incumbent'])
assert result['sourceSha256']==manifest['candidateSha256'][result['selected']['id']]
assert total==result['completedGames']==8856
assert report_count==1362
assert len([p for p in (OUT/'jobs').glob('*.json') if not p.name.endswith('.stamp.json')])==report_count
with zipfile.ZipFile(OUT/'selected_candidate.zip') as z:
    assert sorted(z.namelist())==['agent.py','team.txt']
    for name in z.namelist():assert z.read(name)==(OUT/'candidates'/result['selected']['id']/name).read_bytes()
audit=dict(**preflight,checkedGames=total,checkedReports=report_count,promote=promote,
    selectedSourceSha256=result['sourceSha256'],selectedZipSha256=sha(OUT/'selected_candidate.zip'),
    allSchedulesAndCompiledTeamsVerified=True)
league.write(OUT/'audit.json',audit);print(json.dumps(audit,indent=2))
