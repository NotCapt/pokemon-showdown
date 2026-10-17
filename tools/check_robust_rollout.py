"""Check public memory, recovery, PP, action safety and controlled latency."""
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

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/robust-rollout-v1'
assert not (OUT/'manifest.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
paths={'control':ROOT/'archive/v4_7/agent.py',**{s:OUT/'candidates'/s/'agent.py' for s in ('guarded','aware')}}
modules={};checks={}
for label,path in paths.items():
    spec=importlib.util.spec_from_file_location(label,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);modules[label]=m
    if label!='control':
        with (OUT/f'checks-{label}.log').open('w',encoding='utf-8') as log:
            env=dict(os.environ,AGENT_FILE=str(path))
            subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
            subprocess.run(['node','--test','tests/opponents.test.js','tests/choice.test.js'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
            subprocess.run([sys.executable,'tools/check_recovery_forecast.py','--agent',str(path),'--require-fixed'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        static=digest(m.DATA)
        a=m.build_mon(dict(name='Snorlax',hp_percent=50),True);b=m.build_mon(dict(name='Blastoise',item=''))
        a['pp']={'rest':1,'bodyslam':2};hp=[]
        for i in range(4):
            m.apply_move(a,b,m.DATA['moves']['rest' if i==0 else 'bodyslam'],'',.925);hp.append(b['hp'])
        assert hp[0]==hp[1]==hp[2] and hp[3]<hp[2] and a['pp']=={'rest':0,'bodyslam':1}
        a['pp']['bodyslam']=0;a['moves']=['rest','bodyslam'];assert m.moves_for(a)[0]['id']=='struggle'
        clone=m.clone_mon(a);clone['pp']['rest']=99;assert a['pp']['rest']==0
        # Public PP consumption proves Rest executed; sleeping attacks spend no PP.
        p=m.PokemonAgent();p.public_state={'action':dict(turn=1,key='snorlax',move='rest',pp=8,sleeping=False)}
        foe=m.build_mon(dict(name='Blastoise'))
        def observe(turn,status,rest_pp=7):
            mon=m.build_mon(dict(name='Snorlax',status=status),True)
            o=dict(foe=dict(name='Blastoise',hp_percent=70,_hidden_item='not-public'),valid_moves=[dict(id='rest',pp=rest_pp)])
            before=digest(o);m.observe_public(p,mon,foe,o,turn);assert before==digest(o)
            assert '_hidden_item' not in p.public_state['seen']['blastoise']
            return mon
        a=observe(2,'slp');assert a['rest_sleep']==2
        p.public_state['action']=dict(turn=2,key='snorlax',move='bodyslam',pp=24,sleeping=True)
        assert observe(3,'slp')['rest_sleep']==1
        p.public_state['action']=dict(turn=3,key='snorlax',move=None,pp=None,sleeping=True)
        assert observe(7,'slp')['rest_sleep']==1
        p.public_state['action']=dict(turn=7,key='snorlax',move='bodyslam',pp=24,sleeping=True)
        assert observe(8,'slp')['rest_sleep']==0
        observe(9,'');assert 'snorlax' not in p.public_state['rest']
        hidden=m.clone_mon(foe);hidden.update(item='choicescarf',ability='torrent',moves=['protect'],stats={k:v*3 for k,v in foe['stats'].items()})
        assert m.mc_public(foe)==m.mc_public(hidden)
        own=m.build_mon(dict(name='Corviknight'),True)
        for seed in range(16):
            assert m.rollout_action(own,foe,{own['key']:own},'',random.Random(seed),True)==m.rollout_action(own,hidden,{own['key']:own},'',random.Random(seed),True)
        # Terminal cap score must be insensitive to pre-cap boost/KO value bonuses.
        own['pp']={mid:8 for mid in own['moves']};obs=dict(foe=dict(name='Blastoise',hp_percent=70))
        action=('move 1',m.DATA['moves']['bodypress'],None)
        before=m.mc_rollout(action,own,foe,'',99,obs,{own['key']:own},lambda _:0.,734)
        original=m.value
        try:
            m.value=lambda x,y:original(x,y)*17+1234
            assert m.mc_rollout(action,own,foe,'',99,obs,{own['key']:own},lambda _:0.,734)==before
        finally:m.value=original
        assert digest(m.DATA)==static
        checks[label]=dict(passed=True,pythonTests=63,javascriptChecks=2,publicSleepAndPPPassed=True,
                           finitePPAndCloneIsolationPassed=True,hiddenPolicyIsolationPassed=True,terminalHPObjectivePassed=True,sourceSha256=sha(path))
        print('Checks passed:',label,flush=True)

rng=random.Random(2817291);timings={s:[] for s in paths};ran={s:0 for s in paths};seen={s:0 for s in paths}
fixtures=[];base=modules['control'];team=list(base.OWN.values());enemies=list(base.DATA['species'].values())
for i in range(72):
    active=team[i%3];members=[dict(name=p['name'],hp_percent=rng.choice([12,45,75,100]),fainted=False,active=p is active) for p in team]
    fixtures.append(dict(turn=[2,10,40,90,95,97,98,99,100][(i//3)%9],force_switch=i%19==0,weather='',
                         my_active=dict(members[i%3],boosts={}),my_team=members,
                         foe=dict(name=enemies[i%24]['name'],hp_percent=rng.choice([25,70,100])),
                         valid_moves=[dict(index=j+1,id=base.ident(move),pp=rng.choice([1,5,12])) for j,move in enumerate(active['moves'])],
                         valid_switches=[dict(v,index=j+1) for j,v in enumerate(members) if not v['active']]))
for repeat in range(2):
    for index,request in enumerate(fixtures):
        labels=list(paths);rng.shuffle(labels)
        for label in labels:
            m=modules[label];p=m.PokemonAgent();p.last_turn=request['turn']-1;o=copy.deepcopy(request)
            if label!='control':
                p.public_state={'seen':{base.ident(enemies[(index+3)%24]['name']):dict(name=enemies[(index+3)%24]['name'],hp_percent=75)}}
            initial=digest(o);static=digest(m.DATA);start=time.perf_counter();action=p.decide(o);timings[label].append((time.perf_counter()-start)*1000)
            legal={f"switch {v['index']}" for v in o['valid_switches']}
            if not o['force_switch']:legal|={f"move {v['index']}" for v in o['valid_moves']}
            assert action in legal and initial==digest(o) and static==digest(m.DATA)
            mc=p.mc_last or {}
            if mc.get('rollouts'):
                ran[label]+=repeat==0
                if label!='control':
                    assert sum(mc['samples'])==96 and max(mc['samples'])-min(mc['samples'])<=1
                    seen[label]+=repeat==0 and o['turn'] in (98,99)
            if label!='control' and repeat==0:
                p2=m.PokemonAgent();p2.last_turn=request['turn']-1
                p2.public_state={'seen':{base.ident(enemies[(index+3)%24]['name']):dict(name=enemies[(index+3)%24]['name'],hp_percent=75)}}
                assert p2.decide(copy.deepcopy(request))==action and p2.mc_last==p.mc_last
for label in checks:
    assert ran[label]>0 and seen[label]>0
stats={s:dict(medianMs=statistics.median(v),p95Ms=sorted(v)[int(.95*len(v))],maxMs=max(v),decisions=len(v)) for s,v in timings.items()}
result=dict(checks=checks,latency=stats,sampledPositions=ran,lateSearchPositions=seen,
            sourceSha256={s:sha(p) for s,p in paths.items()},
            timingMethod='72 public synthetic positions; two interleaved repetitions after all unit processes ended; one public previously seen foe; import/init/copy excluded. Not strength evidence.')
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
