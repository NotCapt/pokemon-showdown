"""Audit selected teams, actual-engine schedules and exact exported bytes."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile
import team_search as search

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/kaggle-v4_5-evaluation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OUT/'manifest.json').read_text())
result=json.loads((OUT/'result.json').read_text())
# Audits remain reproducible after a later release changes the root team.
search.INCUMBENT=manifest['teams'][0]
assert result['status']=='complete' and result['manifestSha256']==sha(OUT/'manifest.json')
assert sha(OUT/'reference/agent.py')==manifest['inputSha256']['submission/agent.py']
assert sha(OUT/'reference/engine-core.py')==manifest['inputSha256']['agent_core.py']
assert sha(OUT/'reference/team.json')==manifest['inputSha256']['team.json']
teams={}
for path in (OUT/'candidates').glob('*/team.json'):
    team=json.loads(path.read_text());folder=path.parent
    tree=ast.parse((folder/'agent.py').read_text(encoding='utf-8'))
    own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id',None)=='OWN')
    assert own=={''.join(c for c in p['name'].lower() if c.isalnum()):p for p in team}
    assert (folder/'agent.py').read_text(encoding='utf-8').endswith((OUT/'reference/engine-core.py').read_text(encoding='utf-8'))
    teams[folder.name]=team
    search.validate(team)
assert len(teams)==len(manifest['teams'])==19
assert {search.digest(t)[:20] for t in manifest['teams']}==set(teams)
reports={};total=0
for path in (OUT/'jobs').glob('*.json'):
    if path.name.endswith('.stamp.json'):continue
    report=json.loads(path.read_text());stamp=json.loads(path.with_suffix('.stamp.json').read_text())
    phase,identifier,policy=path.stem.split('-')
    assert policy in ('adaptive','tactical','frozen')
    source=OUT/'candidates'/identifier/'agent.py'
    assert report['agentSha256']==stamp['agentSha256']==sha(source)
    assert stamp['manifestSha256']==sha(OUT/'manifest.json')
    assert stamp['suiteSha256']==sha(OUT/(phase+'-teams.json'))
    assert report['team']==teams[identifier]
    assert len(report['results'])==report['games']==stamp['games']
    assert report['opponentPolicySha256']==manifest['inputSha256']['tools/opponents.js']
    assert report['simulatorVersion']=='0.11.11' and report['sparseBoosts'] and not report['stateless']
    suite=json.loads((OUT/(phase+'-teams.json')).read_text())
    for i,row in enumerate(report['results']):
        assert row['game']==i and row['errors']==0 and row['baseline']==policy
        assert row['side']==(2 if i%2 else 1)
        assert row['seed']==[1,2,i//2+1,stamp['seed']%65536]
        expected=json.loads((OUT/'reference/team.json').read_text()) if policy=='frozen' else suite[(i//2)%len(suite)]
        assert row['opponentSets']==expected
    if policy=='frozen':assert report['opponentAgentSha256']==sha(OUT/'reference/agent.py')
    assert report['wins']==sum(r['winner']=='agent' for r in report['results'])
    assert report['draws']==sum(not r['winner'] for r in report['results'])
    assert report['losses']==sum(r['winner']=='baseline' for r in report['results'])
    assert report['wins']+report['draws']+report['losses']==report['games']
    reports[(phase,identifier,policy)]=report;total+=report['games']
assert total==result['completedGames']==5040
assert len(reports)==75
rankings={}
for phase,games,count in [('qualification',48,19),('validation',96,4),('confirmation',192,2)]:
    ranked=json.loads((OUT/(phase+'-ranking.json')).read_text())
    assert len(ranked)==count
    for record in ranked:
        rows=[reports[(phase,record['id'],p)] for p in search.POLICIES]
        assert all(r['games']==games for r in rows)
        rates=[(r['wins']+.5*r['draws'])/r['games'] for r in rows]
        assert record['rates']==dict(zip(search.POLICIES,rates))
        assert record['score']==.7*sum(rates)/3+.3*min(rates)
        assert record['wins']==sum(r['wins'] for r in rows)
        assert record['games']==sum(r['games'] for r in rows)
        assert record['team']==teams[record['id']]
    assert sorted(ranked,key=search.ranking_key,reverse=True)==ranked
    rankings[phase]=ranked
incumbent_id=search.digest(manifest['teams'][0])[:20]
expected_finalists=[incumbent_id]+[r['id'] for r in rankings['qualification'] if not r['incumbent']][:3]
assert result['qualificationFinalists']==expected_finalists
assert {r['id'] for r in rankings['validation']}==set(expected_finalists)
chosen_id=next(r['id'] for r in rankings['validation'] if not r['incumbent'])
assert result['challenger']['id']==chosen_id
comparison=search.compare_confirmation(
    [reports[('confirmation',incumbent_id,p)] for p in search.POLICIES],
    [reports[('confirmation',chosen_id,p)] for p in search.POLICIES])
assert comparison==result['comparison']
selected=result['selected'];source=OUT/'candidates'/selected['id']
assert selected['team']==teams[selected['id']]
assert sha(source/'agent.py')==result['sourceSha256']
with zipfile.ZipFile(OUT/'selected_candidate.zip') as z:
    assert sorted(z.namelist())==['agent.py','team.txt']
    for name in z.namelist():assert z.read(name)==(source/name).read_bytes()
assert result['promote']==(result['challenger']['score']>result['incumbent']['score'] and
    result['comparison']['pairedScoreInterval95'][0]>0 and
    all(p['scoreGainPP']>=-5 for p in result['comparison']['policies'].values()))
audit=dict(checkedGames=total,checkedReports=len(reports),candidateCount=len(teams),selectedSourceSha256=result['sourceSha256'],
    selectedZipSha256=sha(OUT/'selected_candidate.zip'),screeningBattles=77700,allSchedulesAndCompiledTeamsVerified=True)
(OUT/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
lines=['# Kaggle finalists evaluated with v4.5','',
    'All three original screens completed: 77,700 battles, 2,024 default species trios, six finalists per shard. Their source bundle and complete, disjoint coverage were verified before import.',
    '', 'The 18 nominated teams and the v4.5 incumbent were recompiled with the exact same frozen v4.5 engine. These are new battles; old screening scores were not reused.',
    '', 'Qualification used 48 games per policy for all 19 builds; three challengers and incumbent reached validation at 96 per policy. One challenger selected on validation met the incumbent on independent confirmation at 192 per policy. Policies were adaptive, tactical and the exact frozen v4.5 incumbent. Qualification, validation and confirmation use distinct generated team suites and seeds.',
    '', '| Confirmation policy | Incumbent wins | Challenger wins | Games each |', '| --- | ---: | ---: | ---: |']
for policy,row in result['comparison']['policies'].items():lines.append(f"| {policy} | {row['controlWins']} | {row['challengerWins']} | {row['games']} |")
c=result['comparison'];lo,hi=c['pairedScoreInterval95']
lines+=['',f"Mean score gain: {c['meanScoreGainPP']:+.2f} percentage points; descriptive paired 95% interval [{lo:+.2f}, {hi:+.2f}]. Improved games: {c['improvedGames']}; regressed games: {c['regressedGames']}.",
    '',f"Promotion criterion passed: **{result['promote']}**. The rule was fixed before qualification: higher confirmation composite score, positive lower paired interval, and no per-policy regression exceeding five percentage points. A failed rule retains the incumbent.",
    '', '## Selected team','']
for p in selected['team']:
    lines.append(f"- {p['name']}: {p['item']}, {p['ability']}, {p['nature']}; {p['evs']}; moves: {', '.join(p['moves'])}.")
lines+=['',f"Selected source SHA256: `{result['sourceSha256']}`.",f"Selected ZIP SHA256: `{audit['selectedZipSha256']}`.",
    '',f"Audit: {total:,} new engine battles, {len(reports)} complete reports, zero illegal actions or worker exceptions. Every compiled OWN config, opponent set, seed, player side and exported ZIP byte was verified.",
    '', 'The parallel Kaggle final retains its original v4.3.2 engine and separate incumbent. Its outcome is a different experiment and cannot be used as a latest-engine result. Selection here is conditional on a small experimental policy league, not a tournament win probability or proof of an exhaustive set search. Hidden sets, opponent switching and volatile effects remain approximate.',
    '', 'Reproduce with tools/evaluate_kaggle_finalists.py --run, then tools/audit_kaggle_evaluation.py. Source changes require a new evaluation directory.']
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(audit,indent=2))
