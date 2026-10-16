"""One frozen temporal candidate on shared reference cohorts; no policy tuning."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path

import evaluate_roster_forecast as engine

ROOT=engine.ROOT;REF=ROOT/'research/roster-forecast-v1';OUT=ROOT/'research/phantom-forecast-v1'
m=engine.load(OUT/'manifest.json')
engine.OUT=OUT;engine.verify(m)
assert engine.sha(REF/'manifest.json')==m['referenceManifestSha256']
assert engine.load(REF/'result.json')['status']=='complete'
assert engine.load(OUT/'checks.json')['passed']
execution=dict(evaluatorSha256=engine.sha(Path(__file__)),checksSha256=engine.sha(OUT/'checks.json'),
               mechanicsSha256=engine.sha(OUT/'mechanics.json'),oracleSha256=engine.sha(OUT/'oracle.json'))
if (OUT/'execution.json').exists():assert engine.load(OUT/'execution.json')==execution
else:engine.write(OUT/'execution.json',execution)
evidence={};comparisons={};done=0
for phase in ('validation','confirmation'):
    values={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for f in as_completed([pool.submit(engine.run_one,'phased',phase,j,m) for j in m['jobs'][phase]]):
            j,r=f.result();values[j['key']]=(j,r);done+=r['games']
            engine.write(OUT/'progress.json',dict(phase=phase,completedGames=done,additionalGames=1296))
    rows=[values[j['key']] for j in m['jobs'][phase]];evidence[phase]=rows
    engine.write(OUT/(phase+'-score.json'),engine.aggregate('phased',rows))
    comparisons[phase]={}
    for label in ('control','recovery'):
        reference=[(j,engine.load(REF/'jobs'/f'{phase}-{label}-{j["key"]}.json')) for j in m['jobs'][phase]]
        comparisons[phase][label]=engine.scoring.compare(reference,rows)
    print(json.dumps(dict(phase=phase,score=engine.aggregate('phased',rows),comparisons=comparisons[phase])),flush=True)
assert done==1296
strength=all(r['weightedGainPP']>0 and r['pairedInterval95'][0]>0 and all(s['scoreGainPP']>=-5 for s in r['categories'].values()) for r in comparisons['confirmation'].values())
correctness=comparisons['confirmation']['control']['weightedGainPP']>=0 and comparisons['confirmation']['control']['pairedInterval95'][0]>-3 and all(
    r['scoreGainPP']>=-2 for phase in comparisons.values() for r in phase['control']['categories'].values())
result=dict(status='complete',additionalGames=done,referenceGamesShared=True,manifestSha256=engine.sha(OUT/'manifest.json'),
            comparisons=comparisons,promoteStrength=strength,promoteCorrectness=correctness,sourceSha256=m['candidateSha256']['phased'])
engine.write(OUT/'result.json',result);print(json.dumps(result,indent=2))
