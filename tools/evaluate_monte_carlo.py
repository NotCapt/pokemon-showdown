"""Frozen Monte Carlo ablation with fresh development/validation/confirmation."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shutil
import subprocess
import sys

import evaluate_roster_forecast as engine

ROOT = engine.ROOT
OUT = ROOT / 'research/monte-carlo-v1'
LABELS = ('control', 'phased', 'mc', 'phased_mc')
BASE = 1712039
engine.OUT = OUT
sha, load, write = engine.sha, engine.load, engine.write


def prepare():
    if (OUT / 'manifest.json').exists():
        m = load(OUT / 'manifest.json')
        engine.verify(m)
        return m
    checks, preflight = load(OUT / 'checks.json'), load(OUT / 'preflight.json')
    assert preflight['passed'] and all(checks[label]['passed'] for label in LABELS)
    for label in LABELS:
        source = OUT / 'candidates' / label
        assert sha(source / 'agent.py') == checks[label]['agentSha256'] == preflight['sourceSha256'][label]
        assert load(source / 'team.json') == load(ROOT / 'archive/v4_6/team.json')
    assert sha(OUT / 'candidates/control/agent.py') == sha(ROOT / 'archive/v4_6/agent.py')
    for i in range(12):
        shutil.copytree(ROOT / 'research/roster-forecast-v1/opponents' / f'{i:02d}', OUT / 'opponents' / f'{i:02d}', dirs_exist_ok=True)
    previous_sets, previous_seeds = set(), set()
    for directory in ('diverse-league-v1', 'kaggle-v4_5-evaluation', 'teammate2-comparison', 'roster-forecast-v1', 'phantom-forecast-v1'):
        folder = ROOT / 'research' / directory
        files = list((folder / 'suites').glob('*.json'))
        if directory == 'teammate2-comparison':
            files += list(folder.glob('teams-*.json'))
        for path in files:
            for team in load(path):
                if isinstance(team, list):
                    previous_sets.add(engine.team_search.digest(team))
        for path in (folder / 'jobs').glob('*.json'):
            if path.name.endswith('.stamp.json'):
                continue
            for row in load(path).get('results', []):
                previous_seeds.add(tuple(row['seed']))
    jobs, generated, actual_seeds = {}, set(), set()
    for phase, (offset, adaptive, tactical, pairs) in dict(development=(0,4,2,1), validation=(10000,8,4,2), confirmation=(20000,16,8,4)).items():
        specs = []
        for c, (category, chunks) in enumerate((('adaptive', adaptive), ('tactical', tactical))):
            for chunk in range(chunks):
                path = OUT / 'suites' / f'{phase}-{category}-{chunk:02d}.json'
                path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run([sys.executable, 'tools/make_eval_teams.py', '--seed', str(BASE+offset+1000*(c+1)+37*chunk),
                                '--count', '12', '--out', str(path)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
                for team in load(path):
                    key = engine.team_search.digest(team)
                    assert key not in generated and key not in previous_sets
                    generated.add(key)
                specs.append(dict(key=f'{category}-{chunk:02d}', category=category, policy=category, games=24,
                                  seed=BASE+offset+6000+997*c+113*chunk, teamFile=path.relative_to(OUT).as_posix(), opponentId=None))
        for i in range(12):
            for lead in range(3):
                specs.append(dict(key=f'league-{i:02d}-{lead}', category='league', policy='frozen', games=2*pairs,
                                  seed=BASE+offset+8000+131*i, teamFile=f'opponents/{i:02d}/lead-{lead}.json', opponentId=f'{i:02d}'))
        jobs[phase] = specs
        for spec in specs:
            for i in range(spec['games']):
                actual_seeds.add((1,2,i//2+1,spec['seed']%65536))
    assert not actual_seeds & previous_seeds, 'Simulator seeds overlap earlier campaigns'
    inputs = ['tools/evaluate_monte_carlo.py','tools/prepare_monte_carlo.py','tools/check_monte_carlo.py',
              'tools/preflight_monte_carlo.py','tools/evaluate_roster_forecast.py','tools/evaluate_diverse_league.py',
              'tools/benchmark.js','tools/worker.py','tools/opponents.js','tools/team_search.py',
              'tools/build_agent.py','tools/make_eval_teams.py','package-lock.json',
              'archive/v1/agent.py','archive/v4_6/agent.py','research/options.json',
              'research/battle_data.json','research/enemy_sets.json','research/SHOWDOWN_LICENSE.txt',
              'research/monte-carlo-v1/rollout_helpers.py','research/monte-carlo-v1/PROTOCOL.md',
              'research/monte-carlo-v1/preflight.json','research/monte-carlo-v1/checks.json']
    inputs += [p.relative_to(ROOT).as_posix() for pattern in ('candidates/*/*.py','candidates/*/team.json','candidates/*/team.txt','opponents/*/*.py','opponents/*/*.json','suites/*.json') for p in OUT.glob(pattern)]
    m = dict(candidates=list(LABELS), jobs=jobs, candidateSha256={label:sha(OUT/'candidates'/label/'agent.py') for label in LABELS},
             inputSha256={name:sha(ROOT/name) for name in inputs}, weights=engine.scoring.WEIGHTS,
             primaryGames=6048, generatedOpponents=len(generated), actualSeedOverlapWithPrior=[],
             actualDistinctSeeds=len(actual_seeds), selection='One challenger chosen on validation before any confirmation. Weighted score, HP margin, prefer mc.',
             promotion='Selected challenger: higher confirmation weighted mean and positive lower paired 95% bound versus control; no validation/confirmation category regression >5 pp; positive confirmation mean versus parent. All checks/audits; preflight median<2x control, p95<4x control, max<500ms.',
             caveat='Root-bandit hybrid rollouts, not full MCTS. Same team. Additional CPU, not equal-CPU. Limited transition/opponent/hidden-set models; no unseen enemy bench. Frozen rosters are known. Scores are not tournament probabilities.')
    assert len(generated) == 504
    assert sum(sum(j['games'] for j in specs)*len(LABELS) for specs in jobs.values()) == 6048
    write(OUT/'manifest.json', m)
    return m


def ranking(evidence, phase):
    rows = [engine.aggregate(label, evidence[phase,label]) for label in LABELS]
    rows.sort(key=lambda r:(r['score'],r['hpMargin'],r['id']=='mc'), reverse=True)
    return rows


def promotion(m, selected, comparisons):
    c = comparisons['confirmation'][selected+'-vs-control']
    parent = 'control' if selected == 'mc' else 'phased'
    parent_c = comparisons['confirmation'][selected+'-vs-'+parent]
    timing = load(OUT/'preflight.json')['latency']
    runtime = timing[selected]['medianMs'] < 2*timing['control']['medianMs'] and timing[selected]['p95Ms'] < 4*timing['control']['p95Ms'] and timing[selected]['maxMs'] < 500
    strength = c['weightedGainPP'] > 0 and c['pairedInterval95'][0] > 0 and parent_c['weightedGainPP'] > 0
    category = all(row['scoreGainPP'] >= -5 for phase in comparisons.values() for row in phase[selected+'-vs-control']['categories'].values())
    return dict(strength=strength, categories=category, runtime=runtime, promote=strength and category and runtime)


def run(workers):
    m = prepare(); done = 0; evidence = {}; comparisons = {}
    for phase in ('development','validation','confirmation'):
        engine.verify(m)
        if phase == 'confirmation':
            assert (OUT/'selection.json').exists()
            selected = load(OUT/'selection.json')['challenger']
        for label in LABELS:
            rows = {}
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for f in as_completed([pool.submit(engine.run_one,label,phase,spec,m) for spec in m['jobs'][phase]]):
                    j,r=f.result(); rows[j['key']] = (j,r); done += r['games']
                    write(OUT/'progress.json',dict(phase=phase,candidate=label,completedGames=done,plannedGames=6048))
            evidence[phase,label] = [rows[j['key']] for j in m['jobs'][phase]]
            print(json.dumps(dict(phase=phase,completedGames=done,**engine.aggregate(label,evidence[phase,label]))), flush=True)
        ranked = ranking(evidence,phase)
        write(OUT/(phase+'-ranking.json'),ranked)
        if phase == 'validation':
            selection = dict(challenger=next(r['id'] for r in ranked if r['id'] in ('mc','phased_mc')),
                             validationRanking=ranked,manifestSha256=sha(OUT/'manifest.json'))
            if (OUT/'selection.json').exists(): assert load(OUT/'selection.json') == selection
            else: write(OUT/'selection.json',selection)
        if phase != 'development':
            comparisons[phase] = {a+'-vs-'+b:engine.scoring.compare(evidence[phase,b],evidence[phase,a])
                                  for a,b in [('mc','control'),('phased_mc','control'),('phased_mc','phased'),('phased','control')]}
    selected = load(OUT/'selection.json')['challenger']
    gates = promotion(m,selected,comparisons)
    assert done == 6048
    result = dict(status='complete',completedGames=done,manifestSha256=sha(OUT/'manifest.json'),validationSelected=selected,
                  comparisons=comparisons,gates=gates,recommended=selected if gates['promote'] else 'control')
    write(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--workers',type=int,default=6);a=p.parse_args()
    if a.run: run(a.workers)
    else:
        m=prepare();print(json.dumps(dict(manifestSha256=sha(OUT/'manifest.json'),games=m['primaryGames'],candidates=m['candidates'])))
