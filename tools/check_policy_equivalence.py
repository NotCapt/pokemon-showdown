"""Check decisions and memory on identical public observation sequences."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',required=True)
    p.add_argument('--candidate',required=True);p.add_argument('--traces',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    old,new=load(a.reference,'old'),load(a.candidate,'new');count=0
    for path in sorted(Path(a.traces).glob('game-*.json')):
        agents=[old.PokemonAgent(),new.PokemonAgent()]
        for row in json.loads(path.read_text())['decisions']:
            actions=[agent.decide(copy.deepcopy(row['observation'])) for agent in agents]
            assert actions[0]==actions[1],(path,count,actions)
            assert agents[0].__dict__==agents[1].__dict__,(path,count,'memory')
            count+=1
    result=dict(decisions=count,actionsAndMemoryIdentical=True)
    Path(a.out).write_text(json.dumps(result,indent=2));print(json.dumps(result))
