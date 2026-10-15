import json
from pathlib import Path
import subprocess
import os
root=Path(__file__).resolve().parents[1]
original=(root/'team.json').read_text()
base=json.loads(original)
def mon(name,item,ability,nature,evs,moves): return dict(name=name,item=item,ability=ability,nature=nature,evs=evs,moves=moves)
dragapult=mon('Dragapult','Choice Specs','Infiltrator','Timid','Special Sweeper (252 SpA / 252 Spe / 4 SpD)',['Shadow Ball','Draco Meteor','Flamethrower','Thunderbolt'])
corvi=mon('Corviknight','Leftovers','Mirror Armor','Impish','Physical Wall (252 HP / 252 Def / 4 SpD)',['Body Press','Iron Defense','Roost','Brave Bird'])
teams={'original':base,'fast_balance':[base[0],dragapult,corvi],'fairy_balance':[base[1],dragapult,corvi],'fast_offense':[base[0],base[1],dragapult]}
try:
    for name,team in teams.items():
        (root/'team.json').write_text(json.dumps(team,indent=2))
        subprocess.run(['python','tools/build_agent.py'],cwd=root,check=True)
        env=dict(os.environ,REPORT=f'research/compare-{name}.json',OPPONENT='tactical')
        subprocess.run(['node','tools/benchmark.js','40'],cwd=root,env=env,check=True)
finally:
    (root/'team.json').write_text(original)
    subprocess.run(['python','tools/build_agent.py'],cwd=root,check=True)
print({name:json.loads((root/f'research/compare-{name}.json').read_text())['wins'] for name in teams})
