import argparse
import collections
import importlib.util
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--agent',default='submission/agent.py');parser.add_argument('--out',default='research/damage-errors.json');args=parser.parse_args()
spec=importlib.util.spec_from_file_location('agent',root/args.agent)
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
errors=[];moves=collections.defaultdict(list)
for f in json.loads((root/'research/damage-oracle.json').read_text()):
    a,b=agent.build_mon(f['source']),agent.build_mon(f['target'])
    predicted=agent.damage(a,b,agent.DATA['moves'][f['move']],f['weather'],f['roll'])*f['maxhp']/100
    error=abs(predicted-f['damage'])
    moves[f['move']].append(error)
    errors.append(dict(error=error,predicted=predicted,actual=f['damage'],source=a['name'],target=b['name'],move=f['move'],roll=f['roll'],weather=f['weather']))
errors.sort(key=lambda e:e['error'],reverse=True)
summary=dict(fixtures=len(errors),meanAbsoluteHPError=sum(e['error'] for e in errors)/len(errors),
             over5HP=sum(e['error']>5 for e in errors),over20HP=sum(e['error']>20 for e in errors),
             worstMoves=sorted(((k,sum(v)/len(v)) for k,v in moves.items()),key=lambda pair:pair[1],reverse=True)[:15])
(root/args.out).write_text(json.dumps(dict(summary=summary,worst=errors[:100]),indent=2))
print(json.dumps(summary,indent=2));print(json.dumps(errors[:8],indent=2))
