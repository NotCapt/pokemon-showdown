"""Validate completed Kaggle shards, then test their teams with frozen v4.5.

This is a separate campaign. Original v4.3.2 hashes are verified on import;
screening outcomes are never relabeled as v4.5 results.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

import team_search as search

ROOT=Path(__file__).resolve().parents[1]
IMPORTED=ROOT/'research/kaggle-results-v4_3_2'
OUT=ROOT/'research/kaggle-v4_5-evaluation'
SEED=352673
POLICIES=('adaptive','tactical','frozen')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2),encoding='utf-8');temporary.replace(path)

def imported_teams():
    recorded=json.loads((ROOT/'research/kaggle-parallel-notebooks.json').read_text())
    bundle=ROOT/'dist/REDLINE_Kaggle_Project_v4_3_2.zip'
    assert sha(bundle)==recorded['bundleSha256']
    paths=['agent_core.py','team.json','tools/team_search.py','tools/build_agent.py','tools/benchmark.js','tools/worker.py',
        'tools/opponents.js','tools/make_eval_teams.py','package-lock.json','research/options.json','research/battle_data.json',
        'research/enemy_sets.json','research/SHOWDOWN_LICENSE.txt','archive/v4_3/agent.py','archive/v4_3/team.json','archive/v1/agent.py']
    with zipfile.ZipFile(bundle) as z:hashes={p:hashlib.sha256(z.read(p)).hexdigest() for p in paths}
    campaign=dict(methodVersion=2,profile='full',seed=43179,hashes=hashes)
    screens=[IMPORTED/f'redline-screen-{i}.zip' for i in (1,2,3)]
    teams=search.read_screenings([str(p) for p in screens],campaign,search.population('full',43179),3)
    return teams,{str(p.relative_to(ROOT)):sha(p) for p in screens}

def prepare():
    teams,screen_hashes=imported_teams()
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=['agent_core.py','team.json','submission/agent.py','submission/team.txt','tools/build_agent.py','tools/benchmark.js',
        'tools/worker.py','tools/opponents.js','tools/make_eval_teams.py','tools/team_search.py','package-lock.json',
        'research/options.json','research/battle_data.json','research/enemy_sets.json','research/SHOWDOWN_LICENSE.txt','archive/v1/agent.py']
    manifest=dict(methodVersion=1,engineVersion='v4.5',seed=SEED,teams=teams,inputSha256={p:sha(ROOT/p) for p in inputs},
        importedZipSha256=screen_hashes,policies=list(POLICIES),qualificationGamesPerPolicy=48,validationGamesPerPolicy=96,
        confirmationGamesPerPolicy=192,maxScheduledGames=5040,
        promotionRule='One challenger selected on validation. Require confirmation composite score above incumbent, positive lower paired 95% score interval, and no policy score regression exceeding five percentage points. Otherwise retain v4.5.',
        caveat='New engine campaign with new qualification, validation and confirmation suites. No team or policy tuning after scores are observed.')
    path=OUT/'manifest.json'
    if path.exists():assert json.loads(path.read_text())==manifest,'Inputs changed; use a new evaluation directory'
    else:write(path,manifest)
    reference=OUT/'reference';reference.mkdir(exist_ok=True)
    for original,name in [('agent_core.py','engine-core.py'),('submission/agent.py','agent.py'),('submission/team.txt','team.txt'),('team.json','team.json')]:
        dest=reference/name
        if dest.exists():assert dest.read_bytes()==(ROOT/original).read_bytes()
        else:shutil.copyfile(ROOT/original,dest)
    for label,offset in [('qualification',0),('validation',10000),('confirmation',20000)]:
        suite=OUT/(label+'-teams.json')
        if not suite.exists():subprocess.run([sys.executable,'tools/make_eval_teams.py','--seed',str(SEED+offset+17713),'--count','192','--out',str(suite)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    for team in teams:
        folder=OUT/'candidates'/search.digest(team)[:20];folder.mkdir(parents=True,exist_ok=True)
        write(folder/'team.json',team)
        if not (folder/'agent.py').exists():subprocess.run([sys.executable,'tools/build_agent.py','--core',str(reference/'engine-core.py'),'--team',str(folder/'team.json'),'--out',str(folder)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    control=OUT/'candidates'/search.digest(teams[0])[:20]/'agent.py'
    assert sha(control)==sha(reference/'agent.py'),'Incumbent must retain exact released source bytes'
    return manifest

def run(workers):
    manifest=prepare();teams=manifest['teams'];incumbent=teams[0]
    completed=sum(json.loads(p.read_text())['games'] for p in (OUT/'jobs').glob('*.json') if not p.name.endswith('.stamp.json')) if (OUT/'jobs').exists() else 0
    evidence={}
    def job(spec):
        team,phase,games,policy=spec;folder=OUT/'candidates'/search.digest(team)[:20]
        seed=SEED+{'qualification':0,'validation':10000,'confirmation':20000}[phase]
        destination=OUT/'jobs'/f'{phase}-{search.digest(team)[:20]}-{policy}.json';destination.parent.mkdir(exist_ok=True)
        signature=dict(agentSha256=sha(folder/'agent.py'),manifestSha256=sha(OUT/'manifest.json'),suiteSha256=sha(OUT/(phase+'-teams.json')),
            seed=seed,games=games,policy=policy,frozenAgentSha256=sha(OUT/'reference/agent.py'))
        stamp=destination.with_suffix('.stamp.json')
        if destination.exists():
            assert stamp.exists() and json.loads(stamp.read_text())==signature
            result=json.loads(destination.read_text())
            assert result['agentSha256']==signature['agentSha256'] and result['team']==team and result['games']==games
            assert len(result['results'])==games and all(row['errors']==0 for row in result['results'])
            return result,False
        env=dict(os.environ)
        for key in ('CUSTOM','MIRROR','STATELESS','SAVE_LOGS','TRACE_DIR','OPP_TEAM_FILE','OPP_AGENT_FILE','AGENT_FILE','TEAM_FILE','OPPONENT','SEED','SPARSE','REPORT'):env.pop(key,None)
        temporary=destination.with_suffix('.pending')
        env.update(AGENT_FILE=str(folder/'agent.py'),TEAM_FILE=str(folder/'team.json'),OPPONENT=policy,SEED=str(seed),SPARSE='1',REPORT=str(temporary),NO_LAST_LOSS='1')
        if policy=='frozen':env.update(OPP_AGENT_FILE=str(OUT/'reference/agent.py'),OPP_TEAM_FILE=str(OUT/'reference/team.json'))
        else:env['CUSTOM']=str(OUT/(phase+'-teams.json'))
        with destination.with_suffix('.log').open('w',encoding='utf-8') as log:
            subprocess.run(['node','tools/benchmark.js',str(games)],cwd=ROOT,env=env,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        result=json.loads(temporary.read_text());assert result['agentSha256']==signature['agentSha256'] and result['team']==team and result['games']==games
        assert len(result['results'])==games and all(row['errors']==0 for row in result['results'])
        if policy=='frozen':assert result['opponentAgentSha256']==signature['frozenAgentSha256']
        temporary.replace(destination);write(stamp,signature)
        return result,True
    def evaluate(selected,phase,games):
        nonlocal completed
        ranked=[]
        for index,team in enumerate(selected):
            with ThreadPoolExecutor(max_workers=workers) as pool:results=list(pool.map(job,[(team,phase,games,p) for p in POLICIES]))
            reports=[r for r,_ in results];completed+=sum(r['games'] for r,new in results if new)
            evidence[(phase,search.digest(team))]=reports
            rates=[(r['wins']+.5*r['draws'])/r['games'] for r in reports]
            record=dict(id=search.digest(team)[:20],team=team,score=.7*sum(rates)/3+.3*min(rates),rates=dict(zip(POLICIES,rates)),
                wins=sum(r['wins'] for r in reports),games=sum(r['games'] for r in reports),incumbent=team==incumbent,
                hpMargin=sum(row['finalHP']['agent']-row['finalHP']['opponent'] for r in reports for row in r['results'])/sum(r['games'] for r in reports))
            ranked.append(record);write(OUT/'progress.json',dict(phase=phase,completedCandidates=index+1,totalCandidates=len(selected),completedGames=completed))
            print(json.dumps(dict(phase=phase,candidate=index+1,total=len(selected),names=[p['name'] for p in team],wins=record['wins'],games=record['games'],score=record['score'],completedGames=completed)),flush=True)
        ranked.sort(key=search.ranking_key,reverse=True);write(OUT/(phase+'-ranking.json'),ranked);return ranked
    qualification=evaluate(teams,'qualification',48)
    finalists=[incumbent]+[r['team'] for r in qualification if not r['incumbent']][:3]
    validation=evaluate(finalists,'validation',96)
    challenger=next(r['team'] for r in validation if not r['incumbent'])
    confirmation=evaluate([incumbent,challenger],'confirmation',192)
    comparison=search.compare_confirmation(evidence[('confirmation',search.digest(incumbent))],evidence[('confirmation',search.digest(challenger))])
    control_row=next(r for r in confirmation if r['incumbent']);candidate_row=next(r for r in confirmation if not r['incumbent'])
    promote=(candidate_row['score']>control_row['score'] and comparison['pairedScoreInterval95'][0]>0
        and all(p['scoreGainPP']>=-5 for p in comparison['policies'].values()))
    selected=candidate_row if promote else control_row
    folder=OUT/'candidates'/selected['id']
    with zipfile.ZipFile(OUT/'selected_candidate.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ('agent.py','team.txt'):z.write(folder/name,name)
    result=dict(status='complete',engineVersion='v4.5',selected=selected,challenger=candidate_row,incumbent=control_row,
        promote=promote,comparison=comparison,completedGames=completed,sourceSha256=sha(folder/'agent.py'),manifestSha256=sha(OUT/'manifest.json'),
        qualificationFinalists=[search.digest(t)[:20] for t in finalists],
        caveat='Screening outputs used only to nominate teams. All reported scores are new v4.5 battles. Do not reinterpret the v4.3.2 cloud final as a latest-policy result. Promotion rule was fixed before qualification.')
    write(OUT/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='selected'},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--workers',type=int,default=3);args=p.parse_args()
    if args.run:run(args.workers)
    else:
        m=prepare();print(json.dumps(dict(candidates=len(m['teams']),plannedGames=m['maxScheduledGames'],promotionRule=m['promotionRule'])))
