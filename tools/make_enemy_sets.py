"""Small coherent hidden-set hypotheses; public roster/configuration only."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
options=json.loads((root/'research/options.json').read_text())['pokemon']
sets={}
for name,r in options.items():
    default=dict(name=name,item=r['defaultItem'],ability=r['defaultAbility'],nature=r['defaultNature'],evs=r['defaultEvs'],moves=r['defaultMoves'])
    sets[''.join(c for c in name.lower() if c.isalnum())]=[default]
for team in json.loads((root/'research/custom-opponents.json').read_text())+[json.loads((root/'team.json').read_text())]:
    for p in team:
        key=p['name'].lower()
        if p not in sets[key]: sets[key].append(p)
for key,profiles in sets.items():
    p=dict(profiles[0]);p['item']='Choice Scarf'
    if p not in profiles:profiles.append(p)
    sets[key]=profiles[:4]
(root/'research/enemy_sets.json').write_text(json.dumps(sets,indent=2))
