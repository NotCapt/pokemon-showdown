"""Historical contracts plus real replay checks for the narrow MC guards."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/robust-rollout-v3'
assert not (OUT/'manifest.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
paths={'control':ROOT/'archive/v4_7/agent.py',**{s:OUT/'candidates'/s/'agent.py' for s in ('margin','cycle')}}
modules={};checks={}
for label,path in paths.items():
    spec=importlib.util.spec_from_file_location(label,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);modules[label]=m
    if label=='control':continue
    env=dict(os.environ,AGENT_FILE=str(path))
    with (OUT/f'checks-{label}.log').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
        subprocess.run(['node','--test','tests/opponents.test.js','tests/choice.test.js'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    p=m.PokemonAgent();p.mc_cycles[('old',)]=(1,100,300);p.decide(dict(team_preview=True));assert not p.mc_cycles
    checks[label]=dict(passed=True,pythonTests=63,javascriptChecks=2,previewResetsCycles=True,sourceSha256=sha(path))
    print('Checks passed:',label,flush=True)
# Historical replay stream is development data, not extra wins. Check the real
# sampled scores and veto contract without replacing the actual MC function.
replay=ROOT/'research/robust-rollout-v1/diagnostics/coherent-adaptive-01-v4_7-game-02/traces/game-2.json'
observations=[r['observation'] for r in json.loads(replay.read_text())['decisions']]
replayed={}
for label,m in modules.items():
    p=m.PokemonAgent();actions=[]
    for o in observations:
        initial=digest(o);action=p.decide(copy.deepcopy(o));assert initial==digest(o)
        d=p.mc_last or {}
        if label!='control' and d.get('changed'):
            i=d['actions'].index(action);assert d['estimates'][i]-d['estimates'][0]>=5
        actions.append(dict(turn=o['turn'],action=action,diagnostic=d))
    replayed[label]=actions
assert next(x for x in replayed['control'] if x['turn']==9)['action']=='move 3'
assert next(x for x in replayed['margin'] if x['turn']==9)['action']=='move 1'
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
write(OUT/'development-replay.json',dict(purpose='Historical forced observation stream; action diagnostics, not new battle outcomes.',policies=replayed))
# Standalone cycle guard property using the unchanged sampler's diagnostic
# boundary. Root safety and the tactical fallback remain the real policy.
m=modules['cycle'];original=m._v47_choice
try:
    def choose(p,*args):
        p.mc_last=dict(baseline='move 3',changed=True,actions=['move 3','switch 2'],estimates=[0,20]);return 'switch 2'
    m._v47_choice=choose;p=m.PokemonAgent();a=m.build_mon(dict(name='Corviknight'));b=m.build_mon(dict(name='Dragapult',hp_percent=50))
    actions=[('move 3',m.DATA['moves']['roost'],None),('switch 2',None,dict(name='Snorlax',index=2,hp_percent=100))]
    obs=dict(my_team=[dict(name='Corviknight',hp_percent=60),dict(name='Snorlax',hp_percent=100)])
    assert m.monte_carlo_choice(p,[],actions,a,b,'',20,obs,[])=='switch 2'
    assert m.monte_carlo_choice(p,[],actions,a,b,'',25,obs,[])=='move 3'
    obs['my_team'][0]['hp_percent']=70
    assert m.monte_carlo_choice(p,[],actions,a,b,'',26,obs,[])=='switch 2'
finally:m._v47_choice=original
rng=random.Random(2917291);timings={s:[] for s in paths};ran={s:0 for s in paths};vetoes={s:0 for s in paths};fixtures=[]
base=modules['control'];team=list(base.OWN.values());foes=list(base.DATA['species'].values())
for i in range(72):
    own=team[i%3];members=[dict(name=p['name'],hp_percent=rng.choice([12,45,75,100]),fainted=False,active=p is own) for p in team]
    fixtures.append(dict(turn=[2,10,40,90,95,97,98,99,100][(i//3)%9],weather='',force_switch=i%19==0,
                         my_active=dict(members[i%3],boosts={}),my_team=members,foe=dict(name=foes[i%24]['name'],hp_percent=rng.choice([25,70,100])),
                         valid_moves=[dict(index=j+1,id=base.ident(v),pp=16) for j,v in enumerate(own['moves'])],
                         valid_switches=[dict(v,index=j+1) for j,v in enumerate(members) if not v['active']]))
for repeat in range(2):
    for o in fixtures:
        labels=list(paths);rng.shuffle(labels)
        for label in labels:
            m=modules[label];p=m.PokemonAgent();p.last_turn=o['turn']-1;request=copy.deepcopy(o);before=digest(request);static=digest(m.DATA)
            start=time.perf_counter();action=p.decide(request);timings[label].append((time.perf_counter()-start)*1000)
            legal={f"switch {v['index']}" for v in o['valid_switches']}
            if not o['force_switch']:legal|={f"move {v['index']}" for v in o['valid_moves']}
            assert action in legal and digest(request)==before and digest(m.DATA)==static
            d=p.mc_last or {};ran[label]+=repeat==0 and bool(d.get('rollouts'));vetoes[label]+=repeat==0 and bool(d.get('veto'))
            if repeat==0:
                other=m.PokemonAgent();other.last_turn=o['turn']-1
                assert other.decide(copy.deepcopy(o))==action and other.mc_last==p.mc_last
            if label!='control' and d.get('changed'):
                i=d['actions'].index(action);assert d['estimates'][i]-d['estimates'][0]>=5
stats={s:dict(medianMs=statistics.median(v),p95Ms=sorted(v)[int(.95*len(v))],maxMs=max(v),decisions=len(v)) for s,v in timings.items()}
result=dict(checks=checks,latency=stats,sampledPositions=ran,marginVetoes=vetoes,
            sourceSha256={s:sha(p) for s,p in paths.items()},
            timingMethod='72 public synthetic positions, two interleaved repetitions after all battle/unit workers end; import/init/copy excluded; not strength evidence.')
write(OUT/'checks.json',result);print(json.dumps(result,indent=2))
