"""Verify exact release hashes and summarize matched two-game pairs."""
import hashlib
import json
import random
from pathlib import Path
root=Path(__file__).resolve().parents[1]
digest=hashlib.sha256((root/'submission/agent.py').read_bytes()).hexdigest()
summaries={}
for name in ['v4-arcanine-holdout.json','v4-arcanine-final-custom.json','v4-arcanine-final-v1.json','v4-arcanine-final-v2.json','v4-arcanine-stateless.json']:
    report=json.loads((root/'research'/name).read_text())
    assert report['agentSha256']==digest, name+' is stale'
    assert report['team']==json.loads((root/'team.json').read_text()), name+' uses a different team'
    assert all(r['errors']==0 for r in report['results'])
    pairs=[sum(r['winner']=='agent' for r in report['results'][i:i+2])/2 for i in range(0,report['games'],2)]
    rng=random.Random(8741)
    boot=sorted(sum(rng.choice(pairs) for _ in pairs)/len(pairs) for _ in range(5000))
    summaries[name]=dict(wins=report['wins'],games=report['games'],pairedBootstrap95=[boot[125],boot[4874]],latencyMs=report['latencyMs'])
summary=dict(agentSha256=digest,method='Resample two-game side-reversed pairs, 5000 replicates, seed 8741. Descriptive; does not adjust for candidate selection.',reports=summaries)
(root/'research/v4-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
