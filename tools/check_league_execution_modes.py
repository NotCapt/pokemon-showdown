"""Matched deployment diagnostic: fresh agent instance on every request.

Uses the first four confirmation adaptive chunks for both builds. Those exact
stateful cohorts already exist; this adds 192 stateless games, without changing
the league's score, selection or confirmation rule.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess

import evaluate_diverse_league as league

ROOT=league.ROOT;OUT=ROOT/'research/diverse-league-v1';DEST=OUT/'execution-modes'
manifest=json.loads((OUT/'manifest.json').read_text());result=json.loads((OUT/'result.json').read_text())
DEST.mkdir(exist_ok=True)
identifiers=[result['incumbent']['id'],result['challenger']['id']]
jobs=[j for j in manifest['jobs']['confirmation'] if j['category']=='adaptive'][:4]
assert len(jobs)==4 and all(j['games']==24 for j in jobs)

def run(spec):
    identifier,job=spec;path=DEST/f'{identifier}-{job["key"]}.json';folder=OUT/'candidates'/identifier
    if path.exists():report=json.loads(path.read_text())
    else:
        env=dict(os.environ)
        for key in ('CUSTOM','MIRROR','STATELESS','SAVE_LOGS','TRACE_DIR','OPP_TEAM_FILE','OPP_AGENT_FILE','AGENT_FILE','TEAM_FILE','OPPONENT','SEED','SPARSE','REPORT'):
            env.pop(key,None)
        env.update(AGENT_FILE=str(folder/'agent.py'),TEAM_FILE=str(folder/'team.json'),OPPONENT='adaptive',
            SEED=str(job['seed']),SPARSE='1',STATELESS='1',REPORT=str(path),NO_LAST_LOSS='1',CUSTOM=str(OUT/job['teamFile']))
        with path.with_suffix('.log').open('w',encoding='utf-8') as log:
            subprocess.run(['node','tools/benchmark.js','24'],cwd=ROOT,env=env,check=True,
                           stdout=log,stderr=subprocess.STDOUT,timeout=900)
        report=json.loads(path.read_text())
    assert report['agentSha256']==manifest['candidateSha256'][identifier]==league.sha(folder/'agent.py')
    assert report['stateless'] and report['sparseBoosts'] and report['games']==len(report['results'])==24
    stateful=json.loads((OUT/'jobs'/f'confirmation-{identifier}-{job["key"]}.json').read_text())
    for x,y in zip(stateful['results'],report['results']):
        assert y['errors']==0
        for key in ('seed','side','opponentSets','baseline'):assert x[key]==y[key]
    return identifier,stateful,report

with ThreadPoolExecutor(max_workers=4) as pool:reports=list(pool.map(run,[(i,j) for i in identifiers for j in jobs]))
summary={}
for identifier in identifiers:
    rows=[(a,b) for i,a,b in reports if i==identifier]
    summary[identifier]=dict(sourceSha256=manifest['candidateSha256'][identifier],gamesPerMode=96,
        statefulWins=sum(a['wins'] for a,b in rows),statelessWins=sum(b['wins'] for a,b in rows),
        statelessDraws=sum(b['draws'] for a,b in rows),
        statelessTurnCapGames=sum(x['turns']>100 for a,b in rows for x in b['results']))
proof=dict(manifestSha256=league.sha(OUT/'manifest.json'),additionalGames=192,results=summary,
    purpose='Execution robustness diagnostic; reuses confirmation opposing-set cohorts to isolate persistence. Excluded from league scoring and independent strength claims.')
(DEST/'summary.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
