import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/phantom-forecast-v1'
spec=importlib.util.spec_from_file_location('phased',OUT/'candidates/phased/agent.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks={}
for protecting in (False,True):
    a=m.build_mon(dict(name='Dragapult',hp_percent=100),True)
    b=m.build_mon(dict(name='Metagross' if protecting else 'Lucario',item=''))
    first=(a['hp'],b['hp'])
    enemy=dict(id='splash',category='Status',target='self') if protecting else m.DATA['moves']['icepunch']
    m.turn(a,b,m.DATA['moves']['phantomforce'],enemy,'',.925)
    checks['noDamageOnCharge'+str(protecting)]=(a['hp'],b['hp'])==first
    checks['forcedContinuation'+str(protecting)]=m.best_attack(a,b,'')['id']=='phantomforce'
    m.turn(a,b,m.DATA['moves']['phantomforce'],m.DATA['moves']['protect'] if protecting else enemy,'',.925)
    checks['laterHit'+str(protecting)]=b['hp']<first[1]
    checks['phaseCleared'+str(protecting)]=not a.get('phantom_hidden') and not a.get('phantom_charging')
assert all(checks.values()),checks
(OUT/'mechanics.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks))
