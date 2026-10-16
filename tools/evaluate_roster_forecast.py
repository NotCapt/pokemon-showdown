"""Frozen policy ablations with predeclared correctness and strength gates."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import evaluate_diverse_league as scoring
import team_search

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/roster-forecast-v1'
LABELS=('control','recovery','roster','combined')
BASE=1400003
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    for attempt in range(20):
        try:temporary.replace(path);return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.05)


def verify(manifest):
    for path,digest in manifest['inputSha256'].items():assert sha(ROOT/path)==digest,'Changed frozen input: '+path


def prepare():
    if (OUT/'manifest.json').exists():
        manifest=load(OUT/'manifest.json');verify(manifest);return manifest
    assert (OUT/'checks-final.json').exists(),'Complete automated checks before freezing'
    assert all(r['passed'] for r in load(OUT/'checks-final.json').values())
    assert all(r['agentSha256']==sha(OUT/'candidates'/label/'agent.py') for label,r in load(OUT/'checks-final.json').items())
    previous=load(ROOT/'research/diverse-league-v1/manifest.json')
    for i,team in enumerate(previous['opponents']):
        folder=OUT/'opponents'/f'{i:02d}';folder.mkdir(parents=True,exist_ok=True)
        write(folder/'team.json',team)
        subprocess.run([sys.executable,'tools/build_agent.py','--core','archive/v4_5/agent_core.py',
                        '--team',str(folder/'team.json'),'--out',str(folder)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        for lead in range(3):write(folder/f'lead-{lead}.json',team[lead:]+team[:lead])
    jobs={};generated=set()
    old_sets=set()
    for directory in [ROOT/'research/diverse-league-v1/suites',ROOT/'research/teammate2-comparison']:
        for file in directory.glob('*.json'):
            if directory.name=='teammate2-comparison' and not file.name.startswith('teams-'):continue
            for team in load(file):
                if isinstance(team,list):old_sets.add(team_search.digest(team))
    for phase,(offset,adaptive,tactical,pairs) in dict(development=(0,4,2,1),validation=(10000,8,4,2),confirmation=(20000,16,8,4)).items():
        specs=[]
        for c,(category,chunks) in enumerate([('adaptive',adaptive),('tactical',tactical)]):
            for chunk in range(chunks):
                file=OUT/'suites'/f'{phase}-{category}-{chunk:02d}.json';file.parent.mkdir(parents=True,exist_ok=True)
                subprocess.run([sys.executable,'tools/make_eval_teams.py','--seed',str(BASE+offset+1000*(c+1)+37*chunk),
                                '--count','12','--out',str(file)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
                for team in load(file):
                    key=team_search.digest(team);assert key not in generated and key not in old_sets;generated.add(key)
                specs.append(dict(key=f'{category}-{chunk:02d}',category=category,policy=category,games=24,
                                  seed=BASE+offset+6000+997*c+113*chunk,teamFile=file.relative_to(OUT).as_posix(),opponentId=None))
        for i in range(12):
            for lead in range(3):
                specs.append(dict(key=f'league-{i:02d}-{lead}',category='league',policy='frozen',games=2*pairs,
                                  seed=BASE+offset+8000+131*i,teamFile=f'opponents/{i:02d}/lead-{lead}.json',opponentId=f'{i:02d}'))
        jobs[phase]=specs
    inputs=['tools/evaluate_roster_forecast.py','tools/prepare_roster_forecast.py','tools/evaluate_diverse_league.py',
            'tools/benchmark.js','tools/worker.py','tools/opponents.js','tools/build_agent.py','tools/make_eval_teams.py',
            'tools/team_search.py','package-lock.json','archive/v1/agent.py','archive/v4_5/agent_core.py',
            'research/options.json','research/battle_data.json','research/enemy_sets.json',
            'research/roster-forecast-v1/checks-final.json','research/roster-forecast-v1/recovery-oracle.json',
            'tools/recovery_oracle.js','tools/check_recovery_forecast.py']
    inputs += [p.relative_to(ROOT).as_posix() for pattern in ('candidates/*/*.py','candidates/*/team.json',
               'candidates/*/team.txt','opponents/*/*.py','opponents/*/*.json','suites/*.json') for p in OUT.glob(pattern)]
    for label in LABELS:
        folder=OUT/'candidates'/label
        assert load(folder/'team.json')==load(ROOT/'team.json')
        team_search.validate(load(folder/'team.json'))
    manifest=dict(weights=scoring.WEIGHTS,candidates=list(LABELS),control='control',jobs=jobs,
                  candidateSha256={label:sha(OUT/'candidates'/label/'agent.py') for label in LABELS},
                  inputSha256={p:sha(ROOT/p) for p in inputs},generatedOpponents=len(generated),
                  primaryGames=4752,
                  rule='Development tests all four ablations. Validation and confirmation always compare control, recovery and combined. Roster without recovery fixes is explanatory only. No candidate selection, tuning or replacement after results.',
                  strengthPromotion='Combined must beat both control and recovery on confirmation mean with lower paired 95% intervals above zero. No validation/confirmation category may regress more than 5 pp against either reference.',
                  correctnessPromotion='Recovery-only candidate may be released as a scoped correctness fix if all simulator properties/checks pass, confirmation mean is not lower, lower paired interval is above -3 pp, and no validation/confirmation category regression exceeds 2 pp. Do not claim a demonstrated strength gain.',
                  bootstrap='4000 paired stratified bootstrap replicates, seed 384901. Whole opposing-set and base-roster clusters as in the earlier diverse-league method.',
                  caveat='Same fixed v4.6 team; this tests policy changes. Generated sets and seeds are new and disjoint from the preceding two campaigns. Twelve frozen roster identities remain known. No neural weights are trained.')
    assert len(generated)==504
    assert sum(sum(j['games'] for j in jobs[p])*n for p,n in [('development',4),('validation',3),('confirmation',3)])==4752
    write(OUT/'manifest.json',manifest);return manifest


def run_one(label,phase,spec,manifest):
    folder=OUT/'candidates'/label;path=OUT/'jobs'/f'{phase}-{label}-{spec["key"]}.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    signature=dict(manifestSha256=sha(OUT/'manifest.json'),candidateSha256=manifest['candidateSha256'][label],phase=phase,specification=spec)
    if path.exists() and path.with_suffix('.stamp.json').exists():
        assert load(path.with_suffix('.stamp.json'))==signature
        result=load(path)
    else:
        env=dict(os.environ)
        for key in ('CUSTOM','MIRROR','STATELESS','SAVE_LOGS','TRACE_DIR','OPP_TEAM_FILE','OPP_AGENT_FILE','AGENT_FILE','TEAM_FILE','OPPONENT','SEED','SPARSE','REPORT'):env.pop(key,None)
        pending=path.with_suffix('.pending')
        env.update(AGENT_FILE=str(folder/'agent.py'),TEAM_FILE=str(folder/'team.json'),OPPONENT=spec['policy'],SEED=str(spec['seed']),SPARSE='1',REPORT=str(pending),NO_LAST_LOSS='1')
        if spec['opponentId']:
            env.update(OPP_AGENT_FILE=str(OUT/'opponents'/spec['opponentId']/'agent.py'),OPP_TEAM_FILE=str(OUT/spec['teamFile']))
        else:env['CUSTOM']=str(OUT/spec['teamFile'])
        with path.with_suffix('.log').open('w',encoding='utf-8') as log:
            subprocess.run(['node','tools/benchmark.js',str(spec['games'])],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
        result=load(pending);pending.replace(path);write(path.with_suffix('.stamp.json'),signature)
    assert result['games']==len(result['results'])==spec['games']
    assert result['agentSha256']==manifest['candidateSha256'][label]
    assert all(r['errors']==0 for r in result['results'])
    return spec,result


def aggregate(label,reports):
    rates={c:sum(r['wins']+.5*r['draws'] for j,r in reports if j['category']==c)/sum(r['games'] for j,r in reports if j['category']==c) for c in scoring.WEIGHTS}
    rows=[x for _,r in reports for x in r['results']]
    return dict(id=label,score=sum(scoring.WEIGHTS[c]*rates[c] for c in rates),rates=rates,games=len(rows),
                wins=sum(r['winner']=='agent' for r in rows),draws=sum(not r['winner'] for r in rows),
                hpMargin=sum(r['finalHP']['agent']-r['finalHP']['opponent'] for r in rows)/len(rows))


def run(workers):
    manifest=prepare();done=0;evidence={}
    def phase(labels,name):
        nonlocal done
        verify(manifest);ranked=[]
        for label in labels:
            results={}
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures=[pool.submit(run_one,label,name,j,manifest) for j in manifest['jobs'][name]]
                for f in as_completed(futures):
                    j,r=f.result();results[j['key']]=(j,r);done+=r['games']
                    write(OUT/'progress.json',dict(phase=name,candidate=label,completedGames=done,plannedGames=4752))
            reports=[results[j['key']] for j in manifest['jobs'][name]]
            evidence[name,label]=reports;record=aggregate(label,reports);ranked.append(record)
            print(json.dumps(dict(phase=name,completedGames=done,**record)),flush=True)
        ranked.sort(key=lambda r:(r['score'],r['hpMargin'],{'recovery':3,'combined':2,'roster':1,'control':0}[r['id']]),reverse=True)
        write(OUT/(name+'-ranking.json'),ranked);return ranked
    phase(LABELS,'development')
    phase(['control','recovery','combined'],'validation');phase(['control','recovery','combined'],'confirmation')
    comparisons={name:{a+'-vs-'+b:scoring.compare(evidence[name,b],evidence[name,a]) for a,b in
                      [('recovery','control'),('combined','control'),('combined','recovery')]}
                 for name in ('validation','confirmation')}
    strength=all(comparisons['confirmation'][key]['weightedGainPP']>0 and comparisons['confirmation'][key]['pairedInterval95'][0]>0
                 for key in ('combined-vs-control','combined-vs-recovery')) and all(r['scoreGainPP']>=-5 for phase in comparisons.values()
                 for key in ('combined-vs-control','combined-vs-recovery') for r in phase[key]['categories'].values())
    confirmation=comparisons['confirmation']['recovery-vs-control']
    correctness=confirmation['weightedGainPP']>=0 and confirmation['pairedInterval95'][0]>-3 and all(
                r['scoreGainPP']>=-2 for phase in comparisons.values() for r in phase['recovery-vs-control']['categories'].values())
    assert done==4752
    write(OUT/'result.json',dict(status='complete',completedGames=done,comparisons=comparisons,
                               promoteStrength=strength,promoteCorrectness=correctness,selected='combined' if strength else 'recovery' if correctness else 'control',
                               manifestSha256=sha(OUT/'manifest.json'),caveat=manifest['caveat']))
    print(json.dumps(load(OUT/'result.json'),indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--workers',type=int,default=6);args=p.parse_args()
    if args.run:run(args.workers)
    else:
        m=prepare();print(json.dumps(dict(candidates=m['candidates'],games=m['primaryGames'],generatedOpponents=m['generatedOpponents'],manifestSha256=sha(OUT/'manifest.json'))))
