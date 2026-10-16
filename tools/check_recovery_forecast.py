"""Check selected recovery forecasts against simulator-established properties."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--agent',required=True);p.add_argument('--require-fixed',action='store_true');args=p.parse_args()
spec=importlib.util.spec_from_file_location('recovery_agent',ROOT/args.agent)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
oracle=json.loads((ROOT/'research/roster-forecast-v1/recovery-oracle.json').read_text())
assert oracle['simulatorVersion']=='0.11.11'
def mon(name,**kw):return module.build_mon(dict(name=name,item='',**kw))
a=mon('Corviknight',hp_percent=50,nature='Impish',evs='252 HP / 252 Def / 4 SpD')
b=mon('Snorlax')
module.turn(a,b,module.DATA['moves']['roost'],module.DATA['moves']['earthquake'],'',.925)
grounded=a['hp']<100
restored=a['types']==['Flying','Steel'] or set(a['types'])=={'Flying','Steel'}
a=mon('Snorlax',hp_percent=50);b=mon('Blastoise');hp=[]
for turn in range(4):
    module.apply_move(a,b,module.DATA['moves']['rest' if turn==0 else 'bodyslam'],'',.925)
    hp.append(b['hp'])
rest=hp[0]==hp[1]==hp[2] and hp[3]<hp[2]
a=mon('Snorlax');b=mon('Blastoise')
module.apply_move(a,b,module.DATA['moves']['rest'],'',.925)
full_rest=a['status']!='slp'
a=mon('Corviknight');b=mon('Snorlax')
module.apply_move(a,b,module.DATA['moves']['roost'],'',.925)
full_roost='Flying' in a['types']
result=dict(agent=args.agent,roostGroundingCorrect=grounded,roostTypesRestored=restored,
            restBlocksNextTwoTurns=rest,fullHPRestFails=full_rest,fullHPRoostKeepsFlying=full_roost,
            restOpponentHPTimeline=hp)
print(json.dumps(result))
if args.require_fixed:
    assert all(result[k] for k in ('roostGroundingCorrect','roostTypesRestored','restBlocksNextTwoTurns','fullHPRestFails','fullHPRoostKeepsFlying'))
