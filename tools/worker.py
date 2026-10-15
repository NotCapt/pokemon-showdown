import importlib.util
import json
from pathlib import Path
import sys
import time
import os

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('agent',root/os.environ.get('AGENT_FILE','submission/agent.py'))
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
policies={}
def policy_module(name):
    if name not in ('v1','v2','v3','v4','v4_1','frozen'): return module
    if name not in policies:
        path=root/(os.environ['OPP_AGENT_FILE'] if name=='frozen' else 'archive/'+name+'/agent.py')
        spec=importlib.util.spec_from_file_location('policy_'+name,path)
        impl=importlib.util.module_from_spec(spec);spec.loader.exec_module(impl)
        policies[name]=impl
    return policies[name]
agents={}
for line in sys.stdin:
    try:
        req=json.loads(line); key=req.get('key','default')
        if req.get('reset') or os.environ.get('STATELESS')=='1': agents.pop(key,None)
        if key not in agents:
            impl=policy_module(req.get('policy'))
            agents[key]=impl.PokemonAgent()
        start=time.perf_counter()
        if req.get('policy')=='tactical':
            old=policy_module('v1')
            o=req['observation']; switches=o.get('valid_switches',[])
            a=old.build_mon(o.get('my_active',{})); b=old.build_mon(o.get('foe',{}))
            if o.get('team_preview'): action='team 123'
            elif o.get('force_switch') or not o.get('valid_moves'):
                def matchup(s):
                    x=old.build_mon(s)
                    return old.damage(x,b,old.best_attack(x,b,''))-old.damage(b,x,old.best_attack(b,x,''))
                action='switch '+str(max(switches,key=matchup)['index']) if switches else 'pass'
            else:
                def score(raw):
                    m=dict(old.DATA['moves'].get(raw['id'],{}));m.update(raw)
                    d=old.damage(a,b,m)*old.accuracy(m)
                    first=m.get('priority',0)>0 or old.stat(a,'spe')>=old.stat(b,'spe')
                    return min(d,b['hp'])+ (100 if d>=b['hp'] and first else 0)
                action='move '+str(max(o['valid_moves'],key=score)['index'])
        elif req.get('policy')=='v1': action=agents[key].decide(req['observation'])
        elif req.get('policy')=='v2': action=agents[key].decide(req['observation'])
        elif req.get('policy')=='v3': action=agents[key].decide(req['observation'])
        elif req.get('policy')=='search':
            prior=module.OWN
            module.OWN={}
            try: action=agents[key].decide(req['observation'])
            finally: module.OWN=prior
        else: action=agents[key].decide(req['observation'])
        print(json.dumps({'action':action,'ms':(time.perf_counter()-start)*1000}),flush=True)
    except Exception as exc:
        print(json.dumps({'error':str(exc)}),flush=True)
