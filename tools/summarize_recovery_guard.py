"""Report the selected targeted recovery policy, including unsuccessful attempts."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/robust-rollout-v4'
load=lambda p:json.loads(p.read_text())
r=load(OUT/'result.json');m=load(OUT/'manifest.json');checks=load(OUT/'checks.json')
assert r['allSourcesSchedulesAndOutcomesAudited']
complete=r['status']=='complete'
assert r['checkedGames']==(2760 if complete else 792)
lines=['# Targeted recovery-override study','',
       f"**{r['checkedGames']:,} fresh games audited.** "+('Includes 2,376 field games and 384 direct-match guard games.' if complete else 'Stopped under the predeclared validation-futility rule; no confirmation or promotion claim.')+' All policies use the same team and exact v4.7 reference. Sources, opponents, seeds, weights and gates were frozen before outcomes.','',
       'Validation-selected challenger: **'+str(r['validationSelected'])+'**. Fixed gates recommend **'+r['recommended']+'**.','',
       '| Phase | Policy | Wins / games | Weighted score | Adaptive | New-team v4.7 policy | Known league |',
       '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
for phase,rank in r['rankings'].items():
    for row in rank:lines.append(f"| {phase} | {row['id']} | {row['wins']}/{row['games']} | {100*row['score']:.2f}% | "+' | '.join(f"{100*row['rates'][c]:.2f}%" for c in ('adaptive','strong','league'))+' |')
if complete:
    lines+=['','| Confirmation comparison versus v4.7 | Weighted gain | Descriptive paired 95% interval |','| --- | ---: | ---: |']
    for label,c in r['comparisons']['confirmation'].items():
        lo,hi=c['pairedInterval95'];lines.append(f"| {label} | {c['weightedGainPP']:+.3f} pp | [{lo:+.2f}, {hi:+.2f}] pp |")
    selected=r['comparisons']['confirmation'][r['validationSelected']]
    lines+=['',f"The validation-selected candidate improves {selected['improvedGames']} paired outcomes and regresses {selected['regressedGames']}. A lower interval bound of exactly zero does not satisfy the predeclared strictly-positive strength gate; it must not be rounded into a release qualification."]
    lines+=['','## Direct guard games','','| Matchup | Wins-losses-draws | Score |','| --- | ---: | ---: |']
    for label,v in r['direct'].items():lines.append(f"| {label} | {v['wins']}-{v['losses']}-{v['draws']} | {v['scorePct']:.2f}% |")
    capped={}
    for entry in m['direct']:
        label=r['validationSelected'] if entry['role']=='selected' else 'control';spec=entry['spec']
        key=entry['role']+'-vs-'+spec['opponentId'].replace('direct-','')
        rows=load(OUT/'jobs'/f"direct-{label}-{spec['key']}.json")['results']
        capped.setdefault(key,[]).extend(x for x in rows if x['turns']>=101)
    lines+=['','| Matchup | Games reaching turn-limit adjudication | Losses among those games |','| --- | ---: | ---: |']
    for label,rows in capped.items():lines.append(f"| {label} | {len(rows)} | {sum(x['winner']=='baseline' for x in rows)} |")
    lines+=['','These counts describe the unchanged local harness cutoff at turn 101; they do not add games or alter the release gates.']
else:lines+=['','Failed validation category guards: `'+json.dumps(r['failedCompletedCategoryGainsPP'],sort_keys=True)+'`.']
lines+=['','Gates: `'+json.dumps(r['gates'],sort_keys=True)+'`. Only an eligible validation-selected challenger can be promoted; no post-hoc confirmation substitution.','',
       '## Decision policy','',
       'The core, priors and 96-rollout/six-turn UCB budget remain v4.7. Recovery guard uses the tactical choice when Monte Carlo alone proposes Rest above 65% HP or while the tactical baseline prefers a switch, or when a healing override replaces an attack whose low-roll default-model damage is at least 125% of the observed enemy HP. The latter is a pressure heuristic under unknown sets, not a guaranteed KO. Tactical recovery choices and other MC attack/setup/switch decisions remain available.','',
       'Recovery cycle adds a public-history veto for repeated MC switch overrides with the same own/replacement/opponent species within 12 turns when enemy HP has not fallen by more than two points and summed own HP has not risen by more than two. Vetoes fall back to the original tactical action. Preview resets this memory; productive cycling and baseline switches remain available.','',
       'Both exact candidates pass 63 Python tests and both JavaScript checks, deterministic/legal output and observation/static-data checks. Real historical observation streams verify avoidance of three earlier bad healing overrides while preserving a beneficial MC switch. Those counterfactual observation replays are development checks, not extra won battles or independent strength estimates.','',
       '## Earlier attempts and limitations','',
       'Broader corrected-model v1 was stopped for a last-PP forced Phantom Force forecast bug after 376 completed games, preserved and excluded. Corrected v2 passed the added regression property but failed validation in 792 games: guarded league 51/72 versus 55/72; aware adaptive 90/96 versus 94/96. Its scheduled continuation stopped for logical futility. Blanket-margin v3 scored 233/264 for both candidates versus 241/264 for control, failing adaptive and league guards. All 1,000 completed v3 records are preserved, including 208 subsequent records excluded from development selection/strength claims. Earlier early stops are transparently recorded protocol deviations; none earned promotion.','',
       'Those attempts informed development, not this trial\'s validation selection or held-out strength estimates. This policy retains v4.7\'s Roost/Rest, PP, hidden-bench and other transition approximations. The predicates are heuristics, not exact battle dynamics or an equilibrium solution. Better-looking internal forecasts did not automatically produce stronger tested policies.','',
       '## Controlled runtime','','| Policy | Median | p95 | Maximum |','| --- | ---: | ---: | ---: |']
for label,v in checks['latency'].items():lines.append(f"| {label} | {v['medianMs']:.2f} ms | {v['p95Ms']:.2f} ms | {v['maxMs']:.2f} ms |")
lines+=['',checks['timingMethod'],'',
       '## Method and reproduction','',
       'Weights: adaptive 45%, new-team v4.7 policies 35%, familiar twelve-roster league 20%. 216 generated opposing builds and new actual simulator seed tags are disjoint from inspected earlier records/suites. New-team opponents use the v4.7 core compiled with fresh own configurations. All three cyclic leads are tested on the known league. Field policies share enemy sets, seeds and sides; observations hide enemy sets/bench and omit own boosts. Field intervals use 4,000 paired stratified whole-build/base-roster bootstrap samples, seed 384901. Direct schedules use different seed tags across roles; their percentages are unpaired empirical reference checks, despite the protocol calling the v4.6 reference matched. Their point-based gates are unchanged, and no paired direct improvement claim is made. See EVALUATION_NOTES.md. Scores concern this local conditional field, not tournament win odds.','',
       'On Windows, extract `dist/REDLINE_Recovery_Guard_Project_v4.zip` into a separate directory; run `npm ci`, `python tools/evaluate_recovery_guard.py --audit`, and `python tools/audit_robust_history.py`. Frozen manifests retain some Windows-native input paths; original audits require Windows. Exact sources, manifests, schedules and raw results, including excluded earlier attempts, are preserved.']
if (OUT/'release.json').exists():
    release=load(OUT/'release.json');lines+=['','## Release','',
       'Promoted '+release['version']+', candidate '+release['candidate']+', source SHA256 `'+release['sourceSha256']+'`. Artifact: `'+release['zip']+'`. V4.7 remains archived.']
    ready=load(OUT/'release-readiness.json');v=ready['isolated']['latencyMs']
    lines+=['',f"The exact package passes {ready['isolated']['cases']} isolated legal-action cases. This broader separate workload measured {v['median']:.2f} ms median, {v['p95']:.2f} ms p95 and {v['max']:.2f} ms maximum, distinct from the controlled timings above."]
elif r['gates']['promote']:lines+=['','Experimental gates passed; package compatibility must pass before promotion.']
else:lines+=['','**Retain v4.7.** No candidate earned promotion under these rules.']
if (OUT/'portal-summary.json').exists():lines+=['','Authorized practice compatibility, excluded from strength estimates: `'+json.dumps(load(OUT/'portal-summary.json'),sort_keys=True)+'`.']
else:lines+=['','No practice upload or final competition entry was performed for this source.']
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(status=r['status'],games=r['checkedGames'],recommended=r['recommended'],selected=r['validationSelected'],gates=r['gates']),indent=2))
