"""Explain the audited Monte Carlo trial without changing selection rules."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/monte-carlo-v1'
load = lambda p: json.loads(p.read_text())
r, a, m = [load(OUT/name) for name in ('result.json','audit.json','manifest.json')]
assert a['allSourcesSchedulesScoresAndGatesVerified'] and a['checkedGames'] == 6048
lines = ['# Monte Carlo rollout search: frozen trial','',
         'Completed and audited **6,048 new scheduled games** across four unchanged, same-team policies. Each plays 216 development, 432 validation and 864 confirmation games. The validation-selected challenger is **'+r['validationSelected']+'**; recommended by the fixed gates: **'+r['recommended']+'**.','',
         '## Confirmation','',
         '| Build | Wins / games | Weighted score | Adaptive | Tactical | Frozen league |',
         '| --- | ---: | ---: | ---: | ---: | ---: |']
ranking = load(OUT/'confirmation-ranking.json')
for row in ranking:
    lines.append(f"| {row['id']} | {row['wins']}/{row['games']} | {100*row['score']:.2f}% | "+' | '.join(f"{100*row['rates'][c]:.2f}%" for c in ('adaptive','tactical','league'))+' |')
lines += ['','| Paired comparison | Weighted gain | Descriptive 95% interval |','| --- | ---: | ---: |']
for label, c in r['comparisons']['confirmation'].items():
    lo,hi=c['pairedInterval95']
    lines.append(f"| {label} | {c['weightedGainPP']:+.3f} pp | [{lo:+.2f}, {hi:+.2f}] pp |")
lines += ['','## Decision and cost','',
          'Promotion gates: `'+json.dumps(r['gates'],sort_keys=True)+'`. Only the challenger selected before confirmation can be promoted; other confirmation contrasts are explanatory. No retuning on results.','',
          '| Build | Median decision | p95 | Maximum |','| --- | ---: | ---: | ---: |']
preflight=load(OUT/'preflight.json')
for label,v in preflight['latency'].items():
    lines.append(f"| {label} | {v['medianMs']:.2f} ms | {v['p95Ms']:.2f} ms | {v['maxMs']:.2f} ms |")
lines += ['', 'Monte Carlo activated on '+str(preflight['properties']['mc']['sampledPositions'])+'/96 synthetic positions for mc and '+str(preflight['properties']['phased_mc']['sampledPositions'])+'/96 for phased_mc. The timing table includes positions where the guard retained the original search, including forced switches and turn-98+ endgames.']
lines += ['',preflight['timingMethod'],'',
          'Monte Carlo receives additional computation, not equal CPU. Runtime gates are our engineering choices, not organizer-published limits. Each exact source passed 63 Python tests and two JavaScript checks. Information-isolation, legal-prior, speed-tie, budget, deterministic-repeat, preview-reset and action-legality properties passed.','',
          'Both exact Monte Carlo sources also imported and ran under `python -I -S` in empty temporary directories: 144 cases each, all actions legal, requests/static data unchanged, active Monte Carlo searches observed.','',
          '## Algorithm and limits','',
          'Root-bandit Monte Carlo adds 96 adaptively allocated sampled rollouts of at most six turns when two or more near-leading actions remain. It blends 65% original tactical score with 35% rollout value; an override also needs a positive paired-sample margin. It preserves forced-entry/capped-endgame handling and a conservative healthy-reserve guard. The same policy is tested on original v4.6 mechanics (mc) and the existing recovery/Phantom Force prototype (phased_mc), with both parent engines as controls.','',
          'Where legal alternatives exist, enemy sets are sampled with a 50% chance of using one of 38 complete validated presets and a 50% chance of using the organizer defaults. Species without retained alternatives use defaults. Review found that some organizer defaults already used by both parent engines have EV allocations or a nature absent from the selectable options; the default branch is an approximate prior, not entirely validated selectable builds. See default-prior-review.json. Own submission configurations are separately validated. Rollout move policies see their own configuration and public opponent views. They do not select responses after observing the other simultaneous action. Own known faint replacements are modeled. No unseen enemy bench or voluntary enemy switch is invented. This is neither full tree MCTS nor an exact Pokémon simulator or game-theoretic solution. Continuation PP, status durations, pivots and future observation reporting remain approximate. This compares complete hybrid policy bundles, including priors, continuation heuristics and sampled paralysis/flinch handling; it does not isolate random sampling from every other implementation change. No actual hidden enemy state reaches any Python agent.','',
          'All four use the identical v4.6 Dragapult / Snorlax / Corviknight team. Generated sets and simulator seeds are new and disjoint from preceding campaigns. The twelve frozen roster identities are known; they cover all 24 allowed species and all three cyclic leads. Main observations hide enemy sets/bench and own boosts. Weights are adaptive 40%, tactical 20%, frozen league 40%. Paired intervals use 4,000 stratified bootstrap replicates with whole opposing-build/base-roster clusters, seed 384901. Scores describe this local league, not tournament win probabilities.','',
          'Frozen protocol, manifests, exact sources and all raw result records remain alongside this report. Source/schedule audits verify hashes, seeds, sides, legal execution, ranks, paired comparisons, validation selection and gates. Practice compatibility is recorded separately below. No final competition entry was submitted.']
lines += ['','## Development and validation','',
          '| Phase | Build | Wins / games | Weighted score |','| --- | --- | ---: | ---: |']
for phase in ('development','validation'):
    for row in load(OUT/(phase+'-ranking.json')):
        lines.append(f"| {phase} | {row['id']} | {row['wins']}/{row['games']} | {100*row['score']:.2f}% |")
lines += ['','The exact frozen experiment inputs, result records and audit tools are preserved in `dist/REDLINE_Monte_Carlo_Project_v1.zip`. Extract into a separate directory, install the pinned runtime with `npm ci`, then run `python tools/audit_monte_carlo.py`.']
lines += ['','## Confirmation fixed rosters','',
          '| Opposing team, all three leads | Control | Monte Carlo | Corrected Monte Carlo | Games each |',
          '| --- | ---: | ---: | ---: | ---: |']
for i in range(12):
    key=f'{i:02d}'
    name='/'.join(p['name'] for p in load(OUT/'opponents'/key/'team.json'))
    specs=[j for j in m['jobs']['confirmation'] if j['opponentId']==key]
    wins=[sum(load(OUT/'jobs'/f'confirmation-{label}-{j["key"]}.json')['wins'] for j in specs) for label in ('control','mc','phased_mc')]
    lines.append('| '+name+' | '+' | '.join(str(v) for v in wins)+' | '+str(sum(j['games'] for j in specs))+' |')
if not r['gates']['promote']:
    lines += ['','**Retain the original v4.6 submission.** This trial does not establish a stronger Monte Carlo replacement.']
elif (OUT/'release.json').exists():
    release=load(OUT/'release.json')
    lines += ['','## Release','',
              'Promoted as **'+release['version']+'**, source SHA256 `'+release['sourceSha256']+'`. Artifact: `'+release['zip']+'`. The original v4.6 remains archived and its ZIP is unchanged. The selected mc source retains the original Roost/Rest forecasting limitations; the corrected-model Monte Carlo variant was not selected. The local gate does not certify an exact simulator.','']
    readiness=load(OUT/'release-readiness.json')
    latency=readiness['isolated']['latencyMs']
    lines.append(f"The exact packaged source passes {readiness['isolated']['cases']} isolated legal-action cases. This separate, broader workload measured {latency['median']:.2f} ms median, {latency['p95']:.2f} ms p95 and {latency['max']:.2f} ms maximum; these are not the controlled preflight workload. No numeric CPU/memory limit is published in the reviewed rules.")
    if (OUT/'portal-summary.json').exists():
        portal=load(OUT/'portal-summary.json')
        lines.append('Practice compatibility result: `'+json.dumps(portal,sort_keys=True)+'`. This single sample-baseline game is outside the strength study.')
    else:
        lines.append('No new practice upload has been performed. Local isolated execution and package checks pass; practice-service confirmation remains pending authorization.')
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(recommended=r['recommended'],selected=r['validationSelected'],gates=r['gates'],confirmation=ranking),indent=2))
