"""Frozen diverse-opponent campaign, with a separate confirmation holdout.

No policy tuning occurs here. Candidate teams, opponents, weights, seeds and
promotion gates are recorded before any campaign battles are started.
"""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import zipfile

import team_search as search

ROOT=Path(__file__).resolve().parents[1]
BASE_SEED=715903
WEIGHTS={'adaptive':.4,'tactical':.2,'league':.4}
PHASES={'qualification':(0,4,2,1),'validation':(10000,8,4,2),'confirmation':(20000,16,8,4)}
SOURCE=ROOT/'research/kaggle-v4_5-evaluation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def added_teams():
    ev=search.OPTIONS['evPresets']
    def mon(name,item,ability,nature,preset,moves):
        return dict(name=name,item=item,ability=ability,nature=nature,
                    evs=next(e for e in ev if e.startswith(preset+' (')),moves=moves.split('|'))
    return [
        [mon('Togekiss','Choice Scarf','Serene Grace','Timid','Special Sweeper','Air Slash|Dazzling Gleam|Aura Sphere|Flamethrower'),
         mon('Metagross','Assault Vest','Clear Body','Adamant','Bulky Attacker','Meteor Mash|Bullet Punch|Earthquake|Ice Punch'),
         mon('Volcarona','Heavy-Duty Boots','Flame Body','Timid','Special Sweeper','Fiery Dance|Bug Buzz|Giga Drain|Quiver Dance')],
        [mon('Gengar','Focus Sash','Cursed Body','Timid','Special Sweeper','Shadow Ball|Sludge Bomb|Focus Blast|Thunderbolt'),
         mon('Gyarados','Leftovers','Intimidate','Jolly','Physical Sweeper','Waterfall|Earthquake|Ice Fang|Dragon Dance'),
         mon('Ferrothorn','Rocky Helmet','Iron Barbs','Impish','Physical Wall','Power Whip|Body Press|Iron Head|Thunder Wave')],
        [mon('Alakazam','Life Orb','Magic Guard','Timid','Special Sweeper','Psychic|Shadow Ball|Focus Blast|Energy Ball'),
         json.loads((ROOT/'team.json').read_text())[2],
         mon('Garchomp','Choice Scarf','Rough Skin','Jolly','Physical Sweeper','Earthquake|Dragon Claw|Stone Edge|Fire Fang')],
        [mon('Greninja','Life Orb','Protean','Timid','Special Sweeper','Hydro Pump|Dark Pulse|Ice Beam|Water Shuriken'),
         mon('Scizor','Choice Band','Technician','Adamant','Bulky Attacker','Bullet Punch|Close Combat|U-turn|Knock Off'),
         mon('Hydreigon','Life Orb','Levitate','Timid','Special Sweeper','Draco Meteor|Dark Pulse|Flamethrower|Flash Cannon')],
        [mon('Lapras','Assault Vest','Water Absorb','Modest','Bulky Special','Freeze-Dry|Surf|Thunderbolt|Ice Shard'),
         mon('Corviknight','Leftovers','Mirror Armor','Impish','Physical Wall','Brave Bird|Body Press|Roost|Iron Defense'),
         mon('Lucario','Choice Band','Inner Focus','Adamant','Physical Sweeper','Close Combat|Extreme Speed|Bullet Punch|Ice Punch')],
        [mon('Venusaur','Black Sludge','Overgrow','Bold','Physical Wall','Giga Drain|Sludge Bomb|Sleep Powder|Synthesis'),
         mon('Charizard','Heavy-Duty Boots','Blaze','Timid','Special Sweeper','Flamethrower|Air Slash|Focus Blast|Roost'),
         mon('Blastoise','Assault Vest','Torrent','Modest','Bulky Special','Hydro Pump|Ice Beam|Flash Cannon|Aura Sphere')],
    ]


def team_id(team):return search.digest(team)[:20]


def prepare(out):
    prior=json.loads((SOURCE/'manifest.json').read_text())
    assert sha(ROOT/'submission/agent.py')==prior['inputSha256']['submission/agent.py']
    assert sha(ROOT/'agent_core.py')==prior['inputSha256']['agent_core.py']
    original=prior['teams'];lookup={team_id(t):t for t in original}
    fresh=added_teams()
    candidates=search.unique(original+fresh)
    roster_ids=['7b2d4f06582e4d83957d','11ffdae55a2672c0b629','94392de8a0fe5f2879de',
                'eb298c29c5082e81ef44','490d4e455abee8099a5a','63c4eeac0273f6bbcb4d']
    roster=[lookup[i] for i in roster_ids]+fresh
    for t in candidates:search.validate(t)
    assert len(candidates)==25 and len(roster)==12
    assert {p['name'] for t in roster for p in t}==set(search.OPTIONS['pokemon'])
    out.mkdir(parents=True,exist_ok=True)
    inputs=['agent_core.py','team.json','submission/agent.py','submission/team.txt','tools/evaluate_diverse_league.py',
            'tools/build_agent.py','tools/benchmark.js','tools/worker.py','tools/opponents.js','tools/make_eval_teams.py',
            'tools/team_search.py','package-lock.json','research/options.json','research/battle_data.json',
            'research/enemy_sets.json','research/SHOWDOWN_LICENSE.txt','archive/v1/agent.py']
    for name in ('agent.py','team.txt'):
        destination=out/'reference'/name;destination.parent.mkdir(exist_ok=True)
        if destination.exists():assert destination.read_bytes()==(ROOT/'submission'/name).read_bytes()
        else:shutil.copyfile(ROOT/'submission'/name,destination)
    core=out/'reference/agent_core.py'
    if core.exists():assert core.read_bytes()==(ROOT/'agent_core.py').read_bytes()
    else:shutil.copyfile(ROOT/'agent_core.py',core)
    for team in candidates:
        folder=out/'candidates'/team_id(team);folder.mkdir(parents=True,exist_ok=True)
        if (folder/'team.json').exists():assert json.loads((folder/'team.json').read_text())==team
        else:write(folder/'team.json',team)
        if not (folder/'agent.py').exists():
            subprocess.run([sys.executable,'tools/build_agent.py','--core',str(core),'--team',str(folder/'team.json'),
                            '--out',str(folder)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    assert sha(out/'candidates'/team_id(original[0])/'agent.py')==sha(out/'reference/agent.py')
    jobs={};suite_hashes={}
    for phase,(offset,adaptive_chunks,tactical_chunks,pairs) in PHASES.items():
        phase_jobs=[]
        for category,chunks,salt in [('adaptive',adaptive_chunks,1000),('tactical',tactical_chunks,3000)]:
            full=out/'suites'/f'{phase}-{category}.json';full.parent.mkdir(exist_ok=True)
            if not full.exists():
                subprocess.run([sys.executable,'tools/make_eval_teams.py','--seed',str(BASE_SEED+offset+salt),
                                '--count',str(chunks*12),'--out',str(full)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
            teams=json.loads(full.read_text());assert len(teams)==chunks*12
            for chunk in range(chunks):
                path=out/'suites'/f'{phase}-{category}-{chunk:02}.json'
                subset=teams[chunk*12:(chunk+1)*12]
                if path.exists():assert json.loads(path.read_text())==subset
                else:write(path,subset)
                suite_hashes[str(path.relative_to(out))]=sha(path)
                phase_jobs.append(dict(key=f'{category}-{chunk:02}',category=category,policy=category,games=24,
                    seed=BASE_SEED+offset+salt+chunk*97,teamFile=str(path.relative_to(out)),opponentId=None))
        for index,team in enumerate(roster):
            identifier=team_id(team)
            for rotation in range(3):
                path=out/'opponents'/identifier/f'rotation-{rotation}.json'
                rotated=team[rotation:]+team[:rotation]
                if path.exists():assert json.loads(path.read_text())==rotated
                else:write(path,rotated)
                suite_hashes[str(path.relative_to(out))]=sha(path)
                phase_jobs.append(dict(key=f'league-{identifier}-r{rotation}',category='league',policy='frozen',
                    games=2*pairs,seed=BASE_SEED+offset+5000+index*131+rotation*17,
                    teamFile=str(path.relative_to(out)),opponentId=identifier))
        jobs[phase]=phase_jobs
    manifest=dict(methodVersion=1,engineVersion='v4.5',baseSeed=BASE_SEED,weights=WEIGHTS,candidates=candidates,
        incumbentId=team_id(original[0]),opponents=roster,jobs=jobs,suiteSha256=suite_hashes,
        candidateSha256={team_id(t):sha(out/'candidates'/team_id(t)/'agent.py') for t in candidates},
        inputSha256={p:sha(ROOT/p) for p in inputs},priorManifestSha256=sha(SOURCE/'manifest.json'),
        cloudAuditSha256=sha(ROOT/'research/kaggle-results-v4_3_2/final/audit.json'),
        promotionRule='One challenger chosen on validation. Confirmation weighted mean must exceed incumbent with positive lower paired 95% bootstrap interval; no category may regress more than five percentage points. Otherwise retain incumbent.',
        bootstrap='4000 paired stratified bootstrap replicates, seed 384901. Resample opposing-set pairs for adaptive/tactical and complete base-roster clusters (all leads and seeds together) for the fixed league. Descriptive interval conditional on this experimental population.',
        selectionRule='25 candidates in qualification; top three non-incumbents plus incumbent in validation; one validation-selected challenger plus incumbent in confirmation. Rank by weighted mean only, then HP margin, then incumbent preference.',
        caveat='Roster and candidate teams were informed by previous campaigns. New seeds and generated teams are held out, but the fixed roster compositions are known. No neural model or policy weights are trained here.')
    manifest['maxScheduledGames']=sum(sum(j['games'] for j in jobs[p])*n for p,n in [('qualification',25),('validation',4),('confirmation',2)])
    assert manifest['maxScheduledGames']==8856
    path=out/'manifest.json'
    if path.exists():assert json.loads(path.read_text())==manifest,'Inputs changed; choose a new --out directory'
    else:write(path,manifest)
    return manifest


def ranking_key(row):return row['score'],row['hpMargin'],row['incumbent'],row['id']


def aggregate(identifier,phase,reports,manifest):
    by_category={c:[r for j,r in reports if j['category']==c] for c in WEIGHTS}
    rates={c:sum(r['wins']+.5*r['draws'] for r in rs)/sum(r['games'] for r in rs) for c,rs in by_category.items()}
    games=sum(r['games'] for _,r in reports)
    return dict(id=identifier,team=next(t for t in manifest['candidates'] if team_id(t)==identifier),
        score=sum(WEIGHTS[c]*rates[c] for c in WEIGHTS),rates=rates,games=games,
        wins=sum(r['wins'] for _,r in reports),draws=sum(r['draws'] for _,r in reports),
        hpMargin=sum(x['finalHP']['agent']-x['finalHP']['opponent'] for _,r in reports for x in r['results'])/games,
        incumbent=identifier==manifest['incumbentId'])


def compare(control,challenger):
    score=lambda x:1. if x['winner']=='agent' else .5 if not x['winner'] else 0.
    groups={c:{} for c in WEIGHTS};stats={c:dict(controlWins=0,challengerWins=0,games=0,delta=0.) for c in WEIGHTS}
    improved=regressed=0
    for (job,a),(other,b) in zip(control,challenger):
        assert job==other and a['games']==b['games']
        category=job['category'];s=stats[category]
        s['controlWins']+=a['wins'];s['challengerWins']+=b['wins'];s['games']+=a['games']
        for x,y in zip(a['results'],b['results']):
            for key in ('seed','side','opponentSets','baseline'):assert x[key]==y[key]
            delta=score(y)-score(x);s['delta']+=delta;improved+=delta>0;regressed+=delta<0
            key=job['opponentId'] if category=='league' else search.digest(x['opponentSets'])
            groups[category].setdefault(key,[]).append(delta)
    for s in stats.values():s['scoreGainPP']=100*s.pop('delta')/s['games']
    rng=random.Random(384901);boot=[]
    for _ in range(4000):
        value=0.
        for category in WEIGHTS:
            clusters=list(groups[category].values());sample=[rng.choice(clusters) for _ in clusters]
            value+=WEIGHTS[category]*sum(map(sum,sample))/sum(map(len,sample))
        boot.append(100*value)
    boot.sort()
    return dict(categories=stats,weightedGainPP=sum(WEIGHTS[c]*stats[c]['scoreGainPP'] for c in WEIGHTS),
        pairedInterval95=[boot[100],boot[3899]],improvedGames=improved,regressedGames=regressed,
        clusterCounts={c:len(g) for c,g in groups.items()})


def run(out,workers):
    manifest=prepare(out);completed=0;evidence={}
    def verify_inputs():
        for path,digest in manifest['inputSha256'].items():assert sha(ROOT/path)==digest,'Input changed: '+path
        for path,digest in manifest['suiteSha256'].items():assert sha(out/path)==digest
    def job(spec):
        identifier,phase,specification=spec;source=out/'candidates'/identifier
        report=out/'jobs'/f'{phase}-{identifier}-{specification["key"]}.json';report.parent.mkdir(exist_ok=True)
        stamp=report.with_suffix('.stamp.json')
        signature=dict(manifestSha256=sha(out/'manifest.json'),candidateSha256=manifest['candidateSha256'][identifier],
                       phase=phase,specification=specification)
        if report.exists():
            assert json.loads(stamp.read_text())==signature
            result=json.loads(report.read_text())
        else:
            env=dict(os.environ)
            for k in ('CUSTOM','MIRROR','STATELESS','SAVE_LOGS','TRACE_DIR','OPP_TEAM_FILE','OPP_AGENT_FILE','AGENT_FILE','TEAM_FILE','OPPONENT','SEED','SPARSE','REPORT'):
                env.pop(k,None)
            pending=report.with_suffix('.pending')
            env.update(AGENT_FILE=str(source/'agent.py'),TEAM_FILE=str(source/'team.json'),
                OPPONENT=specification['policy'],SEED=str(specification['seed']),SPARSE='1',REPORT=str(pending),NO_LAST_LOSS='1')
            if specification['opponentId']:
                env.update(OPP_AGENT_FILE=str(out/'candidates'/specification['opponentId']/'agent.py'),
                           OPP_TEAM_FILE=str(out/specification['teamFile']))
            else:env['CUSTOM']=str(out/specification['teamFile'])
            with report.with_suffix('.log').open('w',encoding='utf-8') as log:
                subprocess.run(['node','tools/benchmark.js',str(specification['games'])],cwd=ROOT,env=env,
                               check=True,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
            result=json.loads(pending.read_text());pending.replace(report);write(stamp,signature)
        assert result['agentSha256']==manifest['candidateSha256'][identifier]
        assert result['team']==json.loads((source/'team.json').read_text())
        assert result['games']==len(result['results'])==specification['games']
        assert all(r['errors']==0 for r in result['results'])
        if specification['opponentId']:
            assert result['opponentAgentSha256']==manifest['candidateSha256'][specification['opponentId']]
        return specification,result
    def evaluate(identifiers,phase):
        nonlocal completed
        verify_inputs();ranked=[]
        for index,identifier in enumerate(identifiers):
            specs=manifest['jobs'][phase]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                future={pool.submit(job,(identifier,phase,j)):j['key'] for j in specs};received={}
                for f in as_completed(future):
                    j,r=f.result();received[j['key']]=(j,r);completed+=r['games']
                    write(out/'progress.json',dict(phase=phase,candidate=index+1,totalCandidates=len(identifiers),
                        candidateJobsDone=len(received),candidateJobsTotal=len(specs),completedGames=completed))
            reports=[received[j['key']] for j in specs];evidence[(phase,identifier)]=reports
            row=aggregate(identifier,phase,reports,manifest);ranked.append(row)
            print(json.dumps(dict(phase=phase,candidate=index+1,total=len(identifiers),id=identifier,
                names=[p['name'] for p in row['team']],wins=row['wins'],games=row['games'],score=row['score'],
                rates=row['rates'],completedGames=completed)),flush=True)
        ranked.sort(key=ranking_key,reverse=True);write(out/(phase+'-ranking.json'),ranked);return ranked
    qualification=evaluate([team_id(t) for t in manifest['candidates']],'qualification')
    finalists=[manifest['incumbentId']]+[r['id'] for r in qualification if not r['incumbent']][:3]
    validation=evaluate(finalists,'validation')
    challenger=next(r['id'] for r in validation if not r['incumbent'])
    confirmation=evaluate([manifest['incumbentId'],challenger],'confirmation')
    comparison=compare(evidence[('confirmation',manifest['incumbentId'])],evidence[('confirmation',challenger)])
    control=next(r for r in confirmation if r['incumbent']);candidate=next(r for r in confirmation if not r['incumbent'])
    promote=(candidate['score']>control['score'] and comparison['pairedInterval95'][0]>0 and
             all(s['scoreGainPP']>=-5 for s in comparison['categories'].values()))
    selected=candidate if promote else control
    assert completed==manifest['maxScheduledGames']
    result=dict(status='complete',completedGames=completed,manifestSha256=sha(out/'manifest.json'),
                incumbent=control,challenger=candidate,selected=selected,promote=promote,comparison=comparison,
                validationCandidates=finalists,sourceSha256=manifest['candidateSha256'][selected['id']],
                caveat=manifest['caveat'],bootstrap=manifest['bootstrap'])
    with zipfile.ZipFile(out/'selected_candidate.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in ('agent.py','team.txt'):archive.write(out/'candidates'/selected['id']/name,name)
    write(out/'result.json',result)
    print(json.dumps(dict(status='complete',promote=promote,selected=[p['name'] for p in selected['team']],comparison=comparison)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='research/diverse-league-v1')
    p.add_argument('--workers',type=int,default=6);p.add_argument('--run',action='store_true');args=p.parse_args()
    out=(ROOT/args.out).resolve()
    if args.run:run(out,args.workers)
    else:
        m=prepare(out);print(json.dumps(dict(candidates=len(m['candidates']),rosters=len(m['opponents']),
                                          weights=m['weights'],games=m['maxScheduledGames'])))
