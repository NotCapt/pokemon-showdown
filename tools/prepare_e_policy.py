"""One fixed opponent-response prior experiment, evaluated before promotion."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
archive=root/'archive/v4_3_1'
archive.mkdir(exist_ok=True)
for source,target in [('submission/agent.py','agent.py'),('submission/team.txt','team.txt'),('agent_core.py','agent_core.py'),('team.json','team.json')]:
    if not (archive/target).exists(): shutil.copyfile(root/source,archive/target)
source=(archive/'agent_core.py').read_text()
old="        weights=[(2 if m['id'] in b['moves'] else .6) for m in candidates]"
new="""        # Default-set priors are tempered by the immediate payoff of each
        # opposing action against public active state. Keep a floor for surprises.
        utilities=[]
        for enemy in candidates:
            d=damage(b,a,enemy,weather)*accuracy(enemy)
            first=enemy.get('priority',0)>0 or (enemy.get('priority',0)==0 and stat(b,'spe',weather)>=stat(a,'spe',weather))
            utility=min(a['hp'],d)+(50 if d>=a['hp'] and first else 0)
            if enemy.get('heal'): utility=min(50,100-b['hp'])
            if enemy.get('boosts'): utility+=25 if b['hp']>50 else 5
            utilities.append(utility)
        top=max(utilities)
        weights=[(2 if m['id'] in b['moves'] else .6)*(.3+.7*math.exp((u-top)/40)) for m,u in zip(candidates,utilities)]"""
assert old in source
(root/'research/e-response-core.py').write_text(source.replace(old,new))
