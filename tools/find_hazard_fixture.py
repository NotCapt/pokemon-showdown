"""Find a controlled public decision exposing a lethal entry-cost error."""
import importlib.util
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,root/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
old=load('archive/v4_3_2/agent.py','old');new=load('submission/agent.py','new')
for foe in ['Corviknight','Scizor','Ferrothorn','Metagross','Togekiss','Snorlax','Lapras']:
    for foe_hp in [15,20,25,30,40,50,60,80,100]:
        for pult_hp in [5,10,15,20,25,30,40,60,75]:
            o=dict(turn=100,force_switch=False,my_active=dict(name='Dragonite',hp_percent=pult_hp),
                   foe=dict(name=foe,hp_percent=foe_hp),valid_moves=[dict(new.DATA['moves']['earthquake'],index=2)],
                   valid_switches=[dict(name='Arcanine',hp_percent=24,index=3)])
            p=old.PokemonAgent();q=new.PokemonAgent()
            q.forced_entry=('dragonite',100,89)
            mon=new.build_mon(dict(name='Dragonite',hp_percent=100),True)
            mon['hp']-=new.entry_damage(mon,(True,0));q.observe_entry(mon,90)
            p.last_turn=q.last_turn=99
            a,b=p.decide(o),q.decide(o)
            if a=='switch 3' and b=='move 2':
                result=dict(observation=o,reference=a,candidate=b,priorPublicEntry=dict(name='Dragonite',beforeHP=100,afterHP=mon['hp'],turn=90))
                (root/'research/f-hazard-fixture.json').write_text(json.dumps(result,indent=2))
                print(json.dumps(result));raise SystemExit
raise SystemExit('No fixture found')
