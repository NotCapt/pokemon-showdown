"""Compare decisions on the reference's public observations and same history.

These are diagnostic counterfactual decisions, not replayed battle outcomes.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--traces',required=True)
p.add_argument('--candidate',required=True)
p.add_argument('--reference',default='submission/agent.py')
p.add_argument('--out',required=True)
a=p.parse_args()
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
old=module(a.reference,'reference');new=module(a.candidate,'candidate')
reference_hash=hashlib.sha256(Path(a.reference).read_bytes()).hexdigest()
differences=[];count=0
for path in sorted(Path(a.traces).glob('game-*.json')):
    trace=json.loads(path.read_text())
    assert trace['agentSha256']==reference_hash
    ref=old.PokemonAgent()
    for d in trace['decisions']:
        candidate=new.PokemonAgent()
        candidate.__dict__=copy.deepcopy(ref.__dict__)
        obs=d['observation']
        expected=ref.decide(copy.deepcopy(obs))
        assert expected==d['action'], 'reference trace cannot be reproduced'
        actual=candidate.decide(copy.deepcopy(obs));count+=1
        if actual!=expected:
            differences.append(dict(game=trace['game'],winner=trace['winner'],
                                    reference=expected,candidate=actual,observation=obs))
result=dict(referenceSha256=reference_hash,candidateSha256=hashlib.sha256(Path(a.candidate).read_bytes()).hexdigest(),
            decisions=count,differences=differences,
            caveat='Same public observation and reference history; does not estimate the outcome of playing the alternative action.')
Path(a.out).write_text(json.dumps(result,indent=2))
print(json.dumps(dict(decisions=count,changed=len(differences),output=a.out)))
