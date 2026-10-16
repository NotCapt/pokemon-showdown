"""Summarize the frozen temporal follow-up without recounting shared controls."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/phantom-forecast-v1';REF=ROOT/'research/roster-forecast-v1'
load=lambda p:json.loads(p.read_text())
r=load(OUT/'result.json');a=load(OUT/'audit.json');m=load(OUT/'manifest.json')
assert a['allSourcesSchedulesAndScoresVerified'] and a['checkedNewGames']==1296
lines=['# Temporal Phantom Force follow-up','',
       'Completed and audited **1,296 additional scheduled results**: 432 exploratory validation games and 864 confirmation games. Control and recovery reference games are shared with the preceding study and are not counted again. Together the two studies contain 6,048 scheduled results.','',
       f"Strength gate: **{r['promoteStrength']}**. Scoped correctness gate: **{r['promoteCorrectness']}**.",'',
       m['heldout'],'',m['changes'],'',
       '## Confirmation','', '| Category | Original v4.6 | Recovery reference | Temporal candidate |','| --- | ---: | ---: | ---: |']
for category,denominator in [('adaptive',384),('tactical',192),('league',288)]:
    keys=[j['key'] for j in m['jobs']['confirmation'] if j['category']==category]
    cells=[]
    for folder,label in [(REF,'control'),(REF,'recovery'),(OUT,'phased')]:
        wins=sum(load(folder/'jobs'/f'confirmation-{label}-{key}.json')['wins'] for key in keys)
        cells.append(f'{wins}/{denominator}')
    lines.append('| '+category+' | '+' | '.join(cells)+' |')
base={x['id']:x for x in load(REF/'confirmation-ranking.json')}
phased=load(OUT/'confirmation-score.json')
lines+=['| **Weighted score** | '+ ' | '.join(f'**{100*x:.2f}%**' for x in [base['control']['score'],base['recovery']['score'],phased['score']])+' |','',
        '| Candidate compared with | Gain | Descriptive paired 95% interval |','| --- | ---: | ---: |']
for label,c in r['comparisons']['confirmation'].items():
    lo,hi=c['pairedInterval95'];lines.append(f"| {label} | {c['weightedGainPP']:+.3f} pp | [{lo:+.2f}, {hi:+.2f}] pp |")
lines+=['','## Checks and limits','',
        'The exact temporal source passes all 63 Python tests and eight phase properties. Official simulator cases confirm a damage-free/evasive charge turn, a later hit and Protect bypass. It also retains the checked Roost and Rest corrections. All team choices remain the unchanged, currently legal v4.6 configuration.','',
        'Main observations hide enemy sets and bench. The fixed twelve roster identities are known; confirmation generated sets and seeds were not inspected when this new source was frozen. The model still approximates hidden sets, observed sleep duration, pivots, interrupted charge turns and several other effects. It is not an exact replacement for Showdown.','',
        'Weights: adaptive 40%, tactical 20%, frozen league 40%. Paired intervals use 4,000 stratified bootstrap replicates, seed 384901, with whole opposing-set and base-roster clusters. These are descriptive estimates for this local field, not tournament odds.','',
        m['strengthRule'],'',m['correctnessRule'],'',
        'The original whole-roster study remains separate; see `research/roster-forecast-v1/REPORT.md`. Its control/recovery results are shared references. The frozen inputs and all result records are preserved in `dist/REDLINE_Forecast_Audit_Project_v1.zip`; extract into a separate directory, run `npm ci`, audit the roster study first, then run `python tools/audit_phased_forecast.py`.','',
        f"Temporal source SHA256: `{r['sourceSha256']}`."]
if not r['promoteStrength'] and not r['promoteCorrectness']:
    lines+=['','The candidate failed the predeclared release gates. Keep the original v4.6 submission. These corrections remain experimental; passing simulator properties does not establish a better policy.']
if (OUT/'release.json').exists():
    release=load(OUT/'release.json');lines+=['',f"Packaged as {release['version']}: `{release['versionedZip']}`."]
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(candidate=phased,contrasts=r['comparisons']['confirmation'],promoteStrength=r['promoteStrength'],promoteCorrectness=r['promoteCorrectness']),indent=2))
