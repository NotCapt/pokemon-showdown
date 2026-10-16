"""Recompute all frozen Monte Carlo schedules, outcomes and promotion gates."""
import ast
import json

import evaluate_monte_carlo as run

ROOT, OUT = run.ROOT, run.OUT
m = run.prepare()
assert m['primaryGames'] == 6048 and m['generatedOpponents'] == 504
preflight = run.load(OUT / 'preflight.json')
checks = run.load(OUT / 'checks.json')
standalone = run.load(OUT / 'standalone.json')
for label in run.LABELS:
    folder = OUT / 'candidates' / label
    assert run.sha(folder / 'agent.py') == m['candidateSha256'][label] == checks[label]['agentSha256'] == preflight['sourceSha256'][label]
    assert checks[label]['passed'] and checks[label]['pythonTests'] == 63 and checks[label]['javascriptChecks'] == 2
    tree = ast.parse((folder / 'agent.py').read_text(encoding='utf-8'))
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(n, ast.Import) and all(alias.name in ('math','re','random') for alias in n.names) for n in imports)
    own = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t,'id',None)=='OWN' for t in n.targets))
    assert list(own.values()) == run.load(folder / 'team.json') == run.load(ROOT / 'archive/v4_6/team.json')
    assert (folder / 'agent.py').read_text(encoding='utf-8').endswith((folder / 'agent_core.py').read_text(encoding='utf-8'))
    if label in ('mc','phased_mc'):
        proof = standalone[label]
        assert proof['sourceSha256'] == m['candidateSha256'][label]
        assert proof['isolatedStdlibExecutionPassed'] and proof['allActionsLegal'] and proof['inputsAndStaticDataUnchanged']
        assert proof['cases'] == 144 and proof['monteCarloRan'] > 0

evidence = {}; games = reports = 0
for phase in ('development','validation','confirmation'):
    for label in run.LABELS:
        rows = []
        for spec in m['jobs'][phase]:
            path = OUT / 'jobs' / f'{phase}-{label}-{spec["key"]}.json'
            expected_stamp = dict(manifestSha256=run.sha(OUT/'manifest.json'),candidateSha256=m['candidateSha256'][label],phase=phase,specification=spec)
            assert run.load(path.with_suffix('.stamp.json')) == expected_stamp
            r = run.load(path)
            assert r['agentSha256'] == m['candidateSha256'][label]
            assert r['games'] == len(r['results']) == spec['games']
            assert r['team'] == run.load(OUT/'candidates'/label/'team.json')
            assert r['sparseBoosts'] and not r['stateless'] and r['simulatorVersion'] == '0.11.11'
            assert r['opponentPolicySha256'] == m['inputSha256']['tools/opponents.js']
            suite = run.load(OUT/spec['teamFile'])
            if spec['opponentId']:
                assert r['opponentAgentSha256'] == run.sha(OUT/'opponents'/spec['opponentId']/'agent.py')
            for i, row in enumerate(r['results']):
                assert row['errors'] == 0 and row['game'] == i and row['baseline'] == spec['policy']
                assert row['seed'] == [1,2,i//2+1,spec['seed']%65536] and row['side'] == (2 if i%2 else 1)
                assert row['opponentSets'] == (suite if spec['opponentId'] else suite[i//2])
            assert r['wins'] == sum(row['winner']=='agent' for row in r['results'])
            assert r['draws'] == sum(not row['winner'] for row in r['results'])
            assert r['losses'] == sum(row['winner']=='baseline' for row in r['results'])
            rows.append((spec,r));games += r['games'];reports += 1
        evidence[phase,label] = rows
    assert run.ranking(evidence,phase) == run.load(OUT/(phase+'-ranking.json'))
assert games == 6048
selected = next(r['id'] for r in run.ranking(evidence,'validation') if r['id'] in ('mc','phased_mc'))
assert run.load(OUT/'selection.json') == dict(challenger=selected,validationRanking=run.ranking(evidence,'validation'),manifestSha256=run.sha(OUT/'manifest.json'))
comparisons = {phase:{a+'-vs-'+b:run.engine.scoring.compare(evidence[phase,b],evidence[phase,a])
                     for a,b in [('mc','control'),('phased_mc','control'),('phased_mc','phased'),('phased','control')]}
               for phase in ('validation','confirmation')}
r = run.load(OUT/'result.json')
assert r['status'] == 'complete' and r['completedGames'] == games and r['manifestSha256'] == run.sha(OUT/'manifest.json')
assert r['comparisons'] == comparisons and r['validationSelected'] == selected
gates = run.promotion(m,selected,comparisons)
assert r['gates'] == gates and r['recommended'] == (selected if gates['promote'] else 'control')
audit = dict(checkedGames=games,checkedReports=reports,allSourcesSchedulesScoresAndGatesVerified=True,
             manifestSha256=run.sha(OUT/'manifest.json'),sourceSha256=m['candidateSha256'],
             validationSelected=selected,gates=gates,recommended=r['recommended'],
             caveat=m['caveat'])
audit['standaloneEvidenceSha256'] = run.sha(OUT/'standalone.json')
audit['auditorSha256'] = run.sha(ROOT/'tools/audit_monte_carlo.py')
run.write(OUT/'audit.json',audit)
print(json.dumps(audit,indent=2))
