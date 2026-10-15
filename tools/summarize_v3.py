"""Produce cluster-bootstrap intervals for paired benchmark games."""
import hashlib
import json
import random
from pathlib import Path
root=Path(__file__).resolve().parents[1]
digest=hashlib.sha256((root/'submission/agent.py').read_bytes()).hexdigest()
summaries={}
for filename in ['v3-final-v1.json','v3-final-v2.json','v3-final-custom.json','v3-final-stateless.json']:
    path=root/'research'/filename
    if not path.exists(): continue
    report=json.loads(path.read_text())
    assert report['agentSha256']==digest, f'{filename} describes a different artifact'
    results=report['results'];assert all(r['errors']==0 for r in results)
    pairs=[sum(r['winner']=='agent' for r in results[i:i+2])/2 for i in range(0,len(results),2)]
    rng=random.Random(8741)
    boot=sorted(sum(rng.choice(pairs) for _ in pairs)/len(pairs) for _ in range(5000))
    summaries[filename]=dict(wins=report['wins'],games=report['games'],pairedBootstrap95=[boot[125],boot[4874]],latencyMs=report['latencyMs'])
out=dict(agentSha256=digest,method='Resample two-game matchup/side pairs, 5000 replicates, seed 8741. Descriptive only; does not account for policy or team selection.',reports=summaries)
(root/'research/v3-summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
