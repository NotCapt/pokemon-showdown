"""Verify source provenance and collect the second improvement pass results."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
paths=sorted((root/'research').glob('v4_3-*.json'))
paths += [root/'research'/n for n in (
    'v5-dev-control.json','v5-dev-bulky.json','v5-dev-coverage.json',
    'v5-dev-water.json','v5-validation-control.json','v5-validation-coverage.json')]
rows=[]
for path in paths:
    report=json.loads(path.read_text())
    if 'results' not in report:
        continue
    assert report['games']==len(report['results'])
    assert all(r['errors']==0 for r in report['results'])
    assert hashlib.sha256((root/report['agentFile']).read_bytes()).hexdigest()==report['agentSha256']
    rows.append(dict(report=path.name, games=report['games'], wins=report['wins'],
                     agentSha256=report['agentSha256'], latencyMs=report['latencyMs']))
summary=dict(recommended='dist/REDLINE_Search.zip (unchanged v4.2)',
             totalGames=sum(r['games'] for r in rows), illegalActions=0, reports=rows,
             candidateStatus='Coverage and Explosion candidates remain experimental; no release promotion.')
(root/'research/improvement-b-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
