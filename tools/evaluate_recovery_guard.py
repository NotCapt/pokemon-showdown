"""Frozen stronger-opponent study; validation selection precedes confirmation."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shutil
import subprocess
import sys

import evaluate_roster_forecast as engine
import test_v4_7_matchups as prior

ROOT=engine.ROOT;OUT=ROOT/'research/robust-rollout-v4';LABELS=('control','recovery_guard','recovery_cycle')
engine.OUT=OUT
engine.scoring.WEIGHTS={'adaptive':.45,'strong':.35,'league':.20}
sha,load,write=engine.sha,engine.load,engine.write


def prepare():
    if (OUT/'manifest.json').exists():
        m=load(OUT/'manifest.json');engine.verify(m);return m
    checks=load(OUT/'checks.json')
    assert all(checks['checks'][s]['passed'] for s in ('recovery_guard','recovery_cycle'))
    for label in ('recovery_guard','recovery_cycle'):
        assert sha(OUT/'candidates'/label/'agent.py')==checks['sourceSha256'][label]
    shutil.copytree(ROOT/'archive/v4_7',OUT/'candidates/control',dirs_exist_ok=True)
    prior.OUT=OUT  # Exclude this study when resuming a partially prepared plan.
    old_tags,old_teams,old_reports=prior.previous_records()
    previous=load(ROOT/'research/v4_7-matchups-v1/plan.json')
    old_tags.update(previous['actualSeedTags'])
    for path in (ROOT/'research/v4_7-matchups-v1/suites').glob('*-all.json'):
        old_teams.update(engine.team_search.digest(t) for t in load(path))
    for i in range(12):
        shutil.copytree(ROOT/'research/monte-carlo-v1/opponents'/f'{i:02d}',OUT/'opponents'/f'league-{i:02d}',dirs_exist_ok=True)
    for version in ('v4_6','v4_7'):
        shutil.copytree(ROOT/'archive'/version,OUT/'opponents'/('direct-'+version),dirs_exist_ok=True)
    tags=set(old_tags);fresh=set();jobs={};serial=0
    def seed():
        value=next(x for x in range(62001,65000) if x not in tags);tags.add(value);return value
    for phase,chunks,strong_count,pairs,offset in [('validation',4,24,1,0),('confirmation',8,48,2,10000)]:
        specs=[]
        for category,count,salt in [('adaptive',chunks*12,91),('strong',strong_count,193)]:
            path=OUT/'suites'/f'{phase}-{category}-all.json';path.parent.mkdir(exist_ok=True)
            subprocess.run([sys.executable,'tools/make_eval_teams.py','--seed',str(282130019+offset+salt),'--count',str(count),'--out',str(path)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
            suite=load(path)
            for team in suite:
                key=engine.team_search.digest(team);assert key not in old_teams and key not in fresh;fresh.add(key)
                engine.team_search.validate(team)
            if category=='adaptive':
                for chunk in range(chunks):
                    path=OUT/'suites'/f'{phase}-adaptive-{chunk:02d}.json';write(path,suite[chunk*12:(chunk+1)*12])
                    specs.append(dict(key=f'adaptive-{chunk:02d}',category='adaptive',policy='adaptive',games=24,seed=seed(),teamFile=path.relative_to(OUT).as_posix(),opponentId=None))
            else:
                for i,team in enumerate(suite):
                    key=f'{phase}-strong-{i:02d}';folder=OUT/'opponents'/key;folder.mkdir(parents=True,exist_ok=True)
                    write(folder/'team.json',team)
                    subprocess.run([sys.executable,'tools/build_agent.py','--core','archive/v4_7/agent_core.py','--team',str(folder/'team.json'),'--out',str(folder)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
                    specs.append(dict(key=f'strong-{i:02d}',category='strong',policy='frozen',games=4,seed=seed(),teamFile=f'opponents/{key}/team.json',opponentId=key))
        for i in range(12):
            for lead in range(3):
                specs.append(dict(key=f'league-{i:02d}-{lead}',category='league',policy='frozen',games=2*pairs,seed=seed(),teamFile=f'opponents/league-{i:02d}/lead-{lead}.json',opponentId=f'league-{i:02d}'))
        jobs[phase]=specs
    direct=[]
    for role,opponent in [('selected','v4_7'),('selected','v4_6'),('control','v4_6')]:
        for chunk in range(4):
            key=f'{role}-vs-{opponent}-{chunk}'
            direct.append(dict(role=role,spec=dict(key=key,category='direct',policy='frozen',games=32,seed=seed(),teamFile=f'opponents/direct-{opponent}/team.json',opponentId='direct-'+opponent)))
    protocol='''# Selective recovery-override study, version 4

Freeze all sources, preflight, team, suites, simulator seeds, schedules, weights
and rules before outcomes. Exact v4.7 control and unchanged team/mechanics,
priors, UCB allocation and 96-rollout/six-turn budget for both candidates.
Recovery guard falls back to the tactical choice when MC alone asks for Rest
above 65% HP or while the tactical baseline prefers a switch, or when a healing
override replaces an attack whose low-roll default-model damage exceeds 125%
of the observed opponent HP. That damage margin is a heuristic under unknown
sets, not a guaranteed KO. Baseline recovery choices are retained. Cycle adds
the same public unproductive-switch guard as v3: repeated own/replacement/foe
species tuple within 12 turns; foe HP decrease <=2 and own summed HP gain <=2.
All other MC attack/setup/switch overrides retain the original acceptance test.

Historical diagnostics and prior failed prototypes inform development only.
V1 was stopped for a technical last-PP forecast bug (376 games). Corrected v2
failed validation category guards (792 games). Blanket-margin v3 also failed
its validation guards; its 792 validation games and any subsequently completed
records remain excluded here. All retained inputs/results remain preserved.
V4 uses new opposing builds and simulator seed tags, with no retuning after
freeze. It retains v4.7's known recovery/PP/hidden-bench model approximations.

Validation per policy: adaptive 96, strong 96, known league 72. Confirmation:
adaptive 192, strong 192, known league 144. Total planned field games 2,376.
Weights: adaptive 45%, strong 35%, familiar twelve-roster league 20%. Select
only among challengers passing the validation category guards: no adaptive
or strong regression >2 pp and no league regression >5 pp. Rank eligible
challengers by weighted score, HP margin, prefer recovery_guard. If none are
eligible, stop for predeclared futility, audit the 792 validation games and
retain v4.7; no confirmation/promotion claim. Otherwise save selection before
confirmation. Other candidate confirmation results are explanatory only.

216 generated builds are fresh against inspected prior local suites/records.
Strong opponents use exact v4.7 core with new compiled own teams; league uses
all three cyclic leads. Same opponents, simulator seeds and sides across
policies; own boosts sparse and enemy sets/bench hidden. No random-action or
uniform weak-set ceiling games enter the main score.

Promotion: selected confirmation weighted gain >0 and lower paired 95% bound
>0; category guards must hold on validation and confirmation. Controlled
runtime median <2.5x control, p95 <4x control, max <1000ms; these are project
criteria, not organizer limits. All contract/property/hash/schedule/outcome
and packaging checks must pass. No post-hoc source selection or gate changes.

After confirmation: selected-v4.7, selected-v4.6, control-v4.6 each play 128
new direct games (384 extra; total planned 2,760). Selected score >=45% versus
v4.7 and no >10 pp point regression versus v4.6 relative to matched control.
Direct tests do not select/retune sources. Intervals use 4,000 paired stratified
whole-build/base-roster bootstrap samples, seed 384901. Local field estimates
are not tournament probabilities. No practice upload or final entry submission.
'''
    (OUT/'PROTOCOL.md').write_text(protocol,encoding='utf-8')
    inputs=['tools/evaluate_recovery_guard.py','tools/prepare_recovery_guard.py','tools/check_recovery_guard.py',
            'tools/test_v4_7_matchups.py','tools/evaluate_roster_forecast.py','tools/evaluate_diverse_league.py',
            'tools/benchmark.js','tools/worker.py','tools/opponents.js','tools/build_agent.py','tools/make_eval_teams.py',
            'tools/team_search.py','archive/v1/agent.py','archive/v4_6/agent.py','archive/v4_7/agent.py','archive/v4_7/agent_core.py',
            'research/options.json','research/battle_data.json','research/enemy_sets.json','research/SHOWDOWN_LICENSE.txt',
            'package-lock.json','research/robust-rollout-v1/aborted.json','research/robust-rollout-v2/futility.json','research/robust-rollout-v3/futility.json',str((OUT/'recovery_helpers.py').relative_to(ROOT)),str((OUT/'PROTOCOL.md').relative_to(ROOT)),str((OUT/'checks.json').relative_to(ROOT))]
    inputs += [p.relative_to(ROOT).as_posix() for pattern in ('candidates/*/*.py','candidates/*/team.json','candidates/*/team.txt','opponents/*/*.py','opponents/*/*.json','suites/*.json') for p in OUT.glob(pattern)]
    m=dict(jobs=jobs,direct=direct,inputSha256={name:sha(ROOT/name) for name in inputs},
           candidateSha256={s:sha(OUT/'candidates'/s/'agent.py') for s in LABELS},weights=engine.scoring.WEIGHTS,
           fieldGames=2376,directGames=384,generatedOpponents=len(fresh),oldReportsInspected=old_reports,
           priorSeedTagOverlap=[],actualSeedTags=sorted(tags-old_tags),checksSha256=sha(OUT/'checks.json'))
    assert sum(sum(j['games'] for j in specs)*3 for specs in jobs.values())==2376 and len(fresh)==216
    write(OUT/'manifest.json',m);return m


def aggregate(label,rows):
    return engine.aggregate(label,rows)


def rank(rows,phase):
    return sorted([aggregate(label,rows[phase,label]) for label in LABELS],key=lambda r:(r['score'],r['hpMargin'],r['id']=='recovery_guard'),reverse=True)



def choose_challenger(rows):
    ranked=rank(rows,'validation');base=next(r for r in ranked if r['id']=='control')
    eligible=[r for r in ranked if r['id']!='control' and all(100*(r['rates'][c]-base['rates'][c])>=(-5 if c=='league' else -2) for c in base['rates'])]
    return eligible[0]['id'] if eligible else None


def summarize_futility():
    m=prepare();rows={}
    for label in LABELS:rows['validation',label]=[verify_report(label,'validation',j,m) for j in m['jobs']['validation']]
    assert choose_challenger(rows) is None
    comparisons={s:engine.scoring.compare(rows['validation','control'],rows['validation',s]) for s in LABELS if s!='control'}
    failures={s:{c:v['scoreGainPP'] for c,v in data['categories'].items() if v['scoreGainPP']<(-5 if c=='league' else -2)} for s,data in comparisons.items()}
    assert all(failures.values());engine.verify(m)
    result=dict(status='stopped_for_futility',checkedGames=792,plannedGames=2760,allSourcesSchedulesAndOutcomesAudited=True,
                manifestSha256=sha(OUT/'manifest.json'),validationSelected=None,recommended='control',comparisons={'validation':comparisons},direct={},
                gates=dict(validation=False,promote=False),rankings={'validation':rank(rows,'validation')},
                sourceSha256=m['candidateSha256'],failedCompletedCategoryGainsPP=failures,
                reason='No challenger passed the predeclared validation category guards; no confirmation or promotion claim.')
    write(OUT/'futility.json',result);write(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True);return result


def verify_report(label,phase,spec,m):
    path=OUT/'jobs'/f'{phase}-{label}-{spec["key"]}.json'
    assert load(path.with_suffix('.stamp.json'))==dict(manifestSha256=sha(OUT/'manifest.json'),candidateSha256=m['candidateSha256'][label],phase=phase,specification=spec)
    r=load(path);assert r['agentSha256']==m['candidateSha256'][label] and r['team']==load(OUT/'candidates'/label/'team.json')
    assert r['sparseBoosts'] and not r['stateless'] and r['simulatorVersion']=='0.11.11'
    assert r['opponentPolicySha256']==m['inputSha256']['tools/opponents.js']
    assert r['games']==len(r['results'])==spec['games']
    suite=load(OUT/spec['teamFile'])
    if spec['opponentId']:assert r['opponentAgentSha256']==sha(OUT/'opponents'/spec['opponentId']/'agent.py')
    for i,row in enumerate(r['results']):
        assert row['errors']==0 and row['game']==i and row['baseline']==spec['policy']
        assert row['seed']==[1,2,i//2+1,spec['seed']] and row['side']==(2 if i%2 else 1)
        assert row['opponentSets']==(suite if spec['opponentId'] else suite[i//2])
    assert r['wins']==sum(x['winner']=='agent' for x in r['results']) and r['draws']==sum(not x['winner'] for x in r['results'])
    assert r['losses']==sum(x['winner']=='baseline' for x in r['results'])
    return spec,r


def summarize():
    if (OUT/'futility.json').exists():return summarize_futility()
    m=prepare();rows={};comparisons={};games=0
    for phase in ('validation','confirmation'):
        for label in LABELS:
            rows[phase,label]=[verify_report(label,phase,s,m) for s in m['jobs'][phase]]
            games+=sum(r['games'] for _,r in rows[phase,label])
        rankings=rank(rows,phase);write(OUT/(phase+'-ranking.json'),rankings)
        comparisons[phase]={s:engine.scoring.compare(rows[phase,'control'],rows[phase,s]) for s in ('recovery_guard','recovery_cycle')}
    selected=choose_challenger(rows)
    assert load(OUT/'selection.json')==dict(selected=selected,validation=rank(rows,'validation'),manifestSha256=sha(OUT/'manifest.json'))
    direct={}
    for entry in m['direct']:
        label=selected if entry['role']=='selected' else 'control'
        spec=entry['spec'];_,r=verify_report(label,'direct',spec,m);games+=r['games']
        key=entry['role']+'-vs-'+spec['opponentId'].replace('direct-','')
        direct.setdefault(key,[]).extend(r['results'])
    direct={k:dict(wins=sum(x['winner']=='agent' for x in v),losses=sum(x['winner']=='baseline' for x in v),draws=sum(not x['winner'] for x in v),games=len(v),scorePct=100*sum(1 if x['winner']=='agent' else .5 if not x['winner'] else 0 for x in v)/len(v)) for k,v in direct.items()}
    c=comparisons['confirmation'][selected];timing=load(OUT/'checks.json')['latency'];t=timing[selected];b=timing['control']
    gates=dict(strength=c['weightedGainPP']>0 and c['pairedInterval95'][0]>0,
               categories=all(row['scoreGainPP']>=(-5 if category=='league' else -2) for phase in comparisons.values() for category,row in phase[selected]['categories'].items()),
               runtime=t['medianMs']<2.5*b['medianMs'] and t['p95Ms']<4*b['p95Ms'] and t['maxMs']<1000,
               direct=direct['selected-vs-v4_7']['scorePct']>=45 and direct['selected-vs-v4_6']['scorePct']>=direct['control-vs-v4_6']['scorePct']-10)
    gates['promote']=all(gates.values());assert games==2760;engine.verify(m)
    result=dict(status='complete',checkedGames=games,allSourcesSchedulesAndOutcomesAudited=True,manifestSha256=sha(OUT/'manifest.json'),validationSelected=selected,
                recommended=selected if gates['promote'] else 'control',comparisons=comparisons,direct=direct,gates=gates,
                rankings={phase:rank(rows,phase) for phase in ('validation','confirmation')},sourceSha256=m['candidateSha256'])
    write(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True)
    return result


def run(workers):
    m=prepare();rows={};done=0
    for phase in ('validation','confirmation'):
        engine.verify(m)
        if phase=='confirmation':assert (OUT/'selection.json').exists()
        for label in LABELS:rows[phase,label]={}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures={pool.submit(engine.run_one,label,phase,spec,m):label for label in LABELS for spec in m['jobs'][phase]}
            for f in as_completed(futures):
                label=futures[f];spec,r=f.result();rows[phase,label][spec['key']]=(spec,r);done+=r['games']
                write(OUT/'progress.json',dict(phase=phase,candidate=label,completedGames=done,plannedGames=2760))
                print(json.dumps(dict(phase=phase,candidate=label,done=done,job=spec['key'],wins=r['wins'],games=r['games'])),flush=True)
        for label in LABELS:rows[phase,label]=[rows[phase,label][s['key']] for s in m['jobs'][phase]]
        ranked=rank(rows,phase);write(OUT/(phase+'-ranking.json'),ranked)
        if phase=='validation':
            selected=choose_challenger(rows)
            if selected is None:
                summarize_futility();return
            selection=dict(selected=selected,validation=ranked,manifestSha256=sha(OUT/'manifest.json'))
            if (OUT/'selection.json').exists():assert load(OUT/'selection.json')==selection
            else:write(OUT/'selection.json',selection)
        print(json.dumps(dict(phase=phase,ranking=ranked)),flush=True)
    selected=load(OUT/'selection.json')['selected']
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fs=[pool.submit(engine.run_one,selected if e['role']=='selected' else 'control','direct',e['spec'],m) for e in m['direct']]
        for f in as_completed(fs):
            spec,r=f.result();done+=r['games'];write(OUT/'progress.json',dict(phase='direct',completedGames=done,plannedGames=2760))
            print(json.dumps(dict(phase='direct',done=done,job=spec['key'],wins=r['wins'],games=r['games'])),flush=True)
    summarize()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--workers',type=int,default=6);args=p.parse_args()
    if args.run:run(args.workers)
    elif args.audit:summarize()
    else:
        m=prepare();print(json.dumps(dict(games=2760,sources=m['candidateSha256'],manifestSha256=sha(OUT/'manifest.json')),indent=2))
