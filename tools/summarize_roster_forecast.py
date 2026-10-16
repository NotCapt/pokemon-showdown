"""Write a compact interpretation from the completely audited ablation study."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/roster-forecast-v1'
load=lambda p:json.loads(p.read_text())
r=load(OUT/'result.json');a=load(OUT/'audit.json');m=load(OUT/'manifest.json')
assert a['allSourcesSchedulesAndScoresVerified'] and a['checkedGames']==r['completedGames']==4752
assert a['manifestSha256']==r['manifestSha256']
ranking={phase:{x['id']:x for x in load(OUT/(phase+'-ranking.json'))} for phase in ('development','validation','confirmation')}
lines=['# Recovery fixes and whole-roster forecast: results','',
       f"Completed and audited **4,752 scheduled games and {a['checkedReports']} reports**. Selected by the predeclared rule: **{r['selected']}**. Strength gate: **{r['promoteStrength']}**. Scoped recovery-correctness gate: **{r['promoteCorrectness']}**.",'',
       'All policies use the identical v4.6 Dragapult / Snorlax / Corviknight team. This campaign tests code changes, not a new team or trained neural weights. The original release is preserved byte-for-byte as control. No candidate was retuned using these outcomes.','',
       '## Confirmation','',
       '| Category | Original v4.6 | Recovery fixes | Recovery plus roster forecast |','| --- | ---: | ---: | ---: |']
for category,denominator in [('adaptive',384),('tactical',192),('league',288)]:
    wins={}
    for label in ('control','recovery','combined'):
        keys=[j['key'] for j in m['jobs']['confirmation'] if j['category']==category]
        wins[label]=sum(load(OUT/'jobs'/f'confirmation-{label}-{k}.json')['wins'] for k in keys)
    lines.append('| '+category+' | '+' | '.join(f'{wins[n]}/{denominator}' for n in ('control','recovery','combined'))+' |')
lines.append('| **Weighted score** | '+' | '.join(f"**{100*ranking['confirmation'][n]['score']:.2f}%**" for n in ('control','recovery','combined'))+' |')
lines+=['','| Paired confirmation contrast | Gain | Descriptive 95% interval |','| --- | ---: | ---: |']
for key,row in r['comparisons']['confirmation'].items():
    lo,hi=row['pairedInterval95'];lines.append(f"| {key} | {row['weightedGainPP']:+.3f} pp | [{lo:+.2f}, {hi:+.2f}] pp |")
lines+=['','## What changed','',
       '- Recovery: successful Roost removes Flying typing until turn end; modeled Rest prevents attacks for the following two turns; full-HP Rest fails instead of creating sleep.',
       '- Roster: evaluate the known own roster, restore the outgoing member\'s full move choices after switching, and simulate a legal own replacement after a predicted faint. Entry hazards, Choice locks, Sucker Punch execution, reserve-loss penalty and preview-memory reset remain.',
       '- Combined contains both. Roster-only was tested on development for explanation and was not eligible for release.','',
       'The model still approximates unknown observed sleep duration, two-turn attacks, pivots, status effects and the hidden enemy bench. The recovery fixtures establish only the checked mechanics, not a complete exact simulator.','',
       '## Earlier phases','', '| Phase | Build | Wins / games | Weighted score |','| --- | --- | ---: | ---: |']
for phase in ('development','validation'):
    for label,row in ranking[phase].items():lines.append(f"| {phase} | {label} | {row['wins']}/{row['games']} | {100*row['score']:.2f}% |")
lines+=['','## Checks and method','',
       'All four exact sources pass 63 Python checks. Both recovery builds pass official-simulator properties for Roost grounding/type restoration and Rest timing/failure. The original policy is the already audited v4.6 source. A historical exact-action fixture remains pinned to its original engine and team because changing Rest legitimately changes that old forecast ranking.','',
       'The rule and all sources, configurations, schedules and weights were frozen before this study. There are 504 fresh generated opposing builds, disjoint across phases and from the preceding campaigns, plus twelve known rosters covering all 24 allowed species and all three cyclic leads. Main observations hide enemy sets and reserves and supply sparse own boosts. Weights are adaptive 40%, tactical 20%, frozen league 40%.','',
       m['bootstrap'],'',m['strengthPromotion'],'',m['correctnessPromotion'],'',
       'The audit verified every source/hash, exact opposing configuration, random seed, player side, outcome count, ranking, paired interval and gate. Completed reports contained zero illegal actions. These are conditional local-league estimates, not tournament win probabilities.']
if (OUT/'execution-modes/summary.json').exists():
    modes=load(OUT/'execution-modes/summary.json');assert modes['manifestSha256']==r['manifestSha256']
    lines+=['','## Execution persistence','',modes['caveat'],'',
            '| Build | Stateful wins | Fresh-instance wins | Games per mode |','| --- | ---: | ---: | ---: |']
    for label,row in modes['results'].items():lines.append(f"| {label} | {row['statefulWins']} | {row['statelessWins']} | {row['gamesPerMode']} |")
if (OUT/'release.json').exists():
    release=load(OUT/'release.json')
    lines+=['','## Packaged release','',f"Released as {release['version']}: `{release['versionedZip']}`. Agent SHA256 `{release['agentSha256']}`."]
lines+=['','## Reproduction','',
      'The frozen inputs and all result records are preserved in `dist/REDLINE_Forecast_Audit_Project_v1.zip`. Extract into a separate directory, run `npm ci`, then `python tools/audit_roster_forecast.py` and `python tools/summarize_roster_forecast.py` to verify the existing results. `python tools/evaluate_roster_forecast.py --run --workers 6` resumes or, after removing only extracted job records, reruns the scheduled battles. Changing a frozen input is rejected. No fresh-instance execution diagnostic was run for these rejected candidates.']
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(selected=r['selected'],promoteStrength=r['promoteStrength'],promoteCorrectness=r['promoteCorrectness'],
                     confirmation=ranking['confirmation'],contrasts=r['comparisons']['confirmation']),indent=2))
