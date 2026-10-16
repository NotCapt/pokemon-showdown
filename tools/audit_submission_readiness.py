"""Audit the exact ZIP against current official options and the Python contract."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zip',default='dist/REDLINE_Search_v4_6.zip')
p.add_argument('--source',default='archive/v4_6' if (ROOT/'archive/v4_6').exists() else 'submission')
p.add_argument('--team',default='archive/v4_6/team.json' if (ROOT/'archive/v4_6').exists() else 'team.json')
p.add_argument('--out',default='research/readiness-v4_6/audit.json');args=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
options=json.loads((ROOT/'research/readiness-v4_6/options-fetch.txt').read_text())
team=json.loads((ROOT/args.team).read_text());assert len(team)==len({x['name'] for x in team})==3
for mon in team:
    legal=options['pokemon'][mon['name']]
    assert mon['ability'] in legal['abilities'] and mon['item'] in options['items']
    assert mon['nature'] in options['natures'] and mon['evs'] in options['evPresets']
    assert len(mon['moves'])==len(set(mon['moves']))==4 and all(m in legal['legalMoves'] for m in mon['moves'])
with zipfile.ZipFile(ROOT/args.zip) as archive:
    assert archive.namelist()==['agent.py','team.txt']
    for name in archive.namelist():assert archive.read(name)==(ROOT/args.source/name).read_bytes()
    agent_source=archive.read('agent.py')
tree=ast.parse(agent_source.decode('utf-8-sig'))
imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
assert all(isinstance(n,ast.Import) and all(a.name in ('math','re') for a in n.names) for n in imports)
for node in ast.walk(tree):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
        assert node.func.id not in ('open','exec','eval','compile','__import__','input')
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PokemonAgent')
method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='decide')
assert [a.arg for a in method.args.args]==['self','observation']
own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='OWN' for t in n.targets))
assert own=={''.join(c for c in mon['name'].lower() if c.isalnum()):mon for mon in team}
subprocess.run(['node','tools/check_submission_team.js',str(ROOT/args.source/'team.txt'),str(ROOT/args.team)],cwd=ROOT,check=True)
isolated='''
import copy,hashlib,importlib.util,json,random,statistics,time
spec=importlib.util.spec_from_file_location('standalone','agent.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=random.Random(1081931); own=list(m.OWN.values()); times=[];count=0
fingerprint=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
static=fingerprint(m.DATA)
for i in range(288):
 p=own[i%3]; enemy=list(m.DATA['species'].values())[(i//3)%24]
 members=[dict(name=x['name'],hp_percent=rng.choice([1,25,70,100]),fainted=False,active=x is p) for x in own]
 a=dict(members[i%3],boosts={} if i%2 else dict(atk=0,def_=0,spa=0,spd=0,spe=0)); a['condition']='100/400'
 moves=[dict(index=j+1,id=m.ident(move),disabled=False) for j,move in enumerate(p['moves'])]
 switches=[dict(x,index=j+1) for j,x in enumerate(members) if not x['active']]
 forced=i%11==0
 o=dict(turn=[1,5,20,98,99,100][i%6],team_preview=False,force_switch=forced,weather='',my_active=a,
        foe=dict(name=enemy['name'],types=enemy['types'],hp_percent=rng.choice([1,30,100])),my_team=members,
        valid_moves=moves,valid_switches=switches)
 before=fingerprint(o); agent=m.PokemonAgent();start=time.perf_counter();action=agent.decide(o);times.append((time.perf_counter()-start)*1000)
 allowed={f"switch {x['index']}" for x in switches}|({f"move {x['index']}" for x in moves} if not forced else set())
 assert action in allowed,(o,action);assert before==fingerprint(o);count+=1
assert fingerprint(m.DATA)==static
a=m.PokemonAgent();assert a.decide(dict(team_preview=True))=='team 123'
print(json.dumps(dict(cases=count,allActionsLegal=True,inputsAndStaticDataUnchanged=True,
                     isolatedStdlibImportPassed=True,latencyMs=dict(median=statistics.median(times),p95=sorted(times)[int(.95*len(times))],max=max(times)))))
'''
with tempfile.TemporaryDirectory(prefix='redline-readiness-') as directory:
    (Path(directory)/'agent.py').write_bytes(agent_source)
    run=subprocess.run([sys.executable,'-I','-S','-c',isolated],cwd=directory,capture_output=True,text=True,timeout=120)
    assert run.returncode==0,run.stderr[-3000:]
    isolated_result=json.loads(run.stdout)
result=dict(zip=args.zip,agentSha256=sha(agent_source),zipSha256=sha((ROOT/args.zip).read_bytes()),
            currentOptionsSha256=sha((ROOT/'research/readiness-v4_6/options-fetch.txt').read_bytes()),
            exactTwoRootFiles=True,teamTextMatches=True,liveTeamLegality=True,interfacePassed=True,
            stdlibOnly=True,noFileOrNetworkOperations=True,isolated=isolated_result,
            rulesSources=['https://redline-aresxshunya.netlify.app/docs','https://unstop.com/hackathons/redline-ares-netaji-subhas-university-of-technology-nsut-delhi-1766284'],
            archiveNaming='User will rename the release ZIP to the registered team name.',
            limits='Compatibility and observed runtime checks do not establish a bug-free strategic model. The public docs specify no numeric per-decision CPU/memory limit.')
destination=ROOT/args.out;destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
