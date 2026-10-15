"""Generate deterministic legal custom-set suites, independent of agent tuning."""
import argparse
import json
from pathlib import Path
import random
import re

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--seed',type=int,required=True)
parser.add_argument('--count',type=int,default=24)
parser.add_argument('--out',required=True)
args=parser.parse_args();rng=random.Random(args.seed)
options=json.loads((root/'research/options.json').read_text())
data=json.loads((root/'research/battle_data.json').read_text())
def ident(s):return re.sub('[^a-z0-9]','',s.lower())
def make_set(name):
    p=options['pokemon'][name];species=data['species'][ident(name)]
    physical=species['stats']['atk']>=species['stats']['spa']
    if rng.random()<.15:physical=not physical
    category='Physical' if physical else 'Special'
    available=[data['moves'][ident(m)] for m in p['legalMoves']]
    attacks=[m for m in available if m['category']==category]
    if len(attacks)<2:
        physical=not physical;category='Physical' if physical else 'Special'
        attacks=[m for m in available if m['category']==category]
    ranked=sorted(attacks,key=lambda m:((m['base_power'] or 65)*(1.5 if m['type'] in p['types'] else 1)+20*m['priority'])*rng.uniform(.8,1.2),reverse=True)
    selected=[];types=set()
    for m in ranked:
        if m['type'] not in types:
            selected.append(m['name']);types.add(m['type'])
        if len(selected)==4:break
    for m in ranked:
        if len(selected)<4 and m['name'] not in selected:selected.append(m['name'])
    support=[m for m in available if m['category']=='Status' and (m.get('heal') or m.get('boosts',{}).get('atk' if physical else 'spa',0)>0)]
    bulky=rng.random()<.35
    if support and rng.random()<.55:
        selected=selected[:3]+[rng.choice(support)['name']]
    for m in available:
        if len(selected)<4 and m['name'] not in selected:selected.append(m['name'])
    has_status=any(data['moves'][ident(m)]['category']=='Status' for m in selected)
    items=['Life Orb','Expert Belt','Leftovers','Lum Berry','Focus Sash']
    if not has_status:items+=['Choice Band' if physical else 'Choice Specs','Choice Scarf','Assault Vest']
    prefix=('Bulky Attacker' if physical else 'Bulky Special') if bulky else ('Physical Sweeper' if physical else 'Special Sweeper')
    result=dict(name=name,ability=rng.choice(p['abilities']),item=rng.choice(items),
                nature=('Adamant' if physical else 'Modest') if bulky or rng.random()<.5 else ('Jolly' if physical else 'Timid'),
                evs=next(e for e in options['evPresets'] if e.startswith(prefix)),moves=selected)
    assert len(result['moves'])==4 and len(set(result['moves']))==4
    assert all(m in p['legalMoves'] for m in result['moves'])
    assert result['item'] in options['items'] and result['nature'] in options['natures']
    return result
teams=[[make_set(n) for n in rng.sample(list(options['pokemon']),3)] for _ in range(args.count)]
(root/args.out).write_text(json.dumps(teams,indent=2))
print(json.dumps(dict(seed=args.seed,teams=len(teams),output=args.out)))
