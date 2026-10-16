"""Execute both exact Monte Carlo agents without repository or site packages."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/monte-carlo-v1'
script='''
import copy,hashlib,importlib.util,json,random
s=importlib.util.spec_from_file_location('agent','agent.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
static=digest(m.DATA);priors=digest(m.MC_PRIORS);rng=random.Random(274123)
team=list(m.OWN.values());cases=0;ran=changed=0
for i in range(144):
 active=team[i%3];enemy=list(m.DATA['species'].values())[(i//3)%24]
 members=[dict(name=p['name'],hp_percent=rng.choice([5,30,75,100]),active=p is active,fainted=False) for p in team]
 o=dict(turn=[1,5,25,97,99,100][i%6],force_switch=i%13==0,my_active=dict(members[i%3],boosts={}),my_team=members,
        foe=dict(name=enemy['name'],types=enemy['types'],hp_percent=rng.choice([15,70,100])),weather='',
        valid_moves=[dict(index=j+1,id=m.ident(v),pp=16) for j,v in enumerate(active['moves'])],
        valid_switches=[dict(v,index=j+1) for j,v in enumerate(members) if not v['active']])
 before=digest(o);p=m.PokemonAgent();action=p.decide(o)
 legal={f"switch {v['index']}" for v in o['valid_switches']}
 if not o['force_switch']:legal|={f"move {v['index']}" for v in o['valid_moves']}
 assert action in legal and before==digest(o)
 if p.mc_last and p.mc_last['rollouts']:ran+=1;changed+=p.mc_last['changed']
 cases+=1
assert digest(m.DATA)==static and digest(m.MC_PRIORS)==priors
assert ran>0
print(json.dumps(dict(cases=cases,allActionsLegal=True,inputsAndStaticDataUnchanged=True,monteCarloRan=ran,changedChoices=changed)))
'''
result={}
for label in ('mc','phased_mc'):
    source=(OUT/'candidates'/label/'agent.py').read_bytes()
    with tempfile.TemporaryDirectory(prefix='redline-monte-carlo-') as directory:
        (Path(directory)/'agent.py').write_bytes(source)
        run=subprocess.run([sys.executable,'-I','-S','-c',script],cwd=directory,capture_output=True,text=True,timeout=180)
        assert run.returncode==0,run.stderr[-3000:]
        result[label]=dict(sourceSha256=hashlib.sha256(source).hexdigest(),isolatedStdlibExecutionPassed=True,**json.loads(run.stdout))
(OUT/'standalone.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
