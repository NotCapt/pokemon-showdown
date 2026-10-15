"""Budgeted, resumable CPU team search against multiple opponent policies.

Full mode screens all 2024 species trios with one legal default build each,
then mutates survivor moves, items, abilities, EVs, natures and lead order.
It does not enumerate the complete set space or establish tournament strength.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = json.loads((ROOT/'research/options.json').read_text())
INCUMBENT = json.loads((ROOT/'team.json').read_text())
POLICIES = ('adaptive', 'tactical', 'frozen')

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2))
    temp.replace(path)

def validate(team):
    assert len(team) == 3 and len({p['name'] for p in team}) == 3
    for p in team:
        legal = OPTIONS['pokemon'][p['name']]
        assert p['ability'] in legal['abilities']
        assert p['item'] in OPTIONS['items'] and p['nature'] in OPTIONS['natures']
        assert p['evs'] in OPTIONS['evPresets']
        assert 1 <= len(set(p['moves'])) == len(p['moves']) <= 4
        assert all(m in legal['legalMoves'] for m in p['moves'])

def default(name):
    p = OPTIONS['pokemon'][name]
    evs = next(e for e in OPTIONS['evPresets'] if e.split(' (')[0] == p['defaultEvs'].split(' (')[0])
    return dict(name=name, moves=p['defaultMoves'][:], ability=p['defaultAbility'],
                item=p['defaultItem'], nature=p['defaultNature'] if p['defaultNature'] in OPTIONS['natures'] else 'Impish', evs=evs)

def mutate(team, rng):
    team = copy.deepcopy(team)
    p = rng.choice(team)
    kind = rng.choice(['species', 'moves', 'item', 'ability', 'nature', 'evs', 'order'])
    legal = OPTIONS['pokemon'][p['name']]
    if kind == 'species':
        name = rng.choice([n for n in OPTIONS['pokemon'] if n not in {x['name'] for x in team}])
        team[team.index(p)] = default(name)
    elif kind == 'order':
        rng.shuffle(team)
    elif kind == 'moves':
        p['moves'][rng.randrange(len(p['moves']))] = rng.choice([m for m in legal['legalMoves'] if m not in p['moves']])
    else:
        choices = {'item': OPTIONS['items'], 'ability': legal['abilities'], 'nature': OPTIONS['natures'], 'evs': OPTIONS['evPresets']}
        p[kind] = rng.choice(choices[kind])
    validate(team)
    return team

def unique(teams):
    return list({digest(t): t for t in teams}.values())

def run(args):
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    config = {k: v for k, v in vars(args).items() if k not in ('out', 'hours', 'max_games', 'workers')}
    files = ['agent_core.py', 'team.json', 'tools/team_search.py', 'tools/build_agent.py', 'tools/benchmark.js',
             'tools/worker.py', 'tools/opponents.js', 'tools/make_eval_teams.py', 'package-lock.json',
             'research/options.json', 'research/battle_data.json', 'research/enemy_sets.json', 'research/SHOWDOWN_LICENSE.txt',
             'archive/v4_3/agent.py', 'archive/v4_3/team.json', 'archive/v1/agent.py']
    provenance = dict(config=config, hashes={f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    manifest = out/'manifest.json'
    if manifest.exists():
        assert json.loads(manifest.read_text()) == provenance, 'Inputs changed. Use a new output directory.'
    else: write(manifest, provenance)
    deadline = time.monotonic() + args.hours*3600
    completed = sum(json.loads(p.read_text())['games'] for p in (out/'jobs').glob('*.json')) if (out/'jobs').exists() else 0
    suites = {}
    for phase, offset in [('development', 0), ('validation', 10000), ('confirmation', 20000)]:
        suites[phase] = out/(phase+'.json')
        if not suites[phase].exists():
            subprocess.run([sys.executable, str(ROOT/'tools/make_eval_teams.py'), '--seed', str(args.seed+offset),
                            '--count', '192', '--out', str(suites[phase])], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    def prepare(team):
        validate(team)
        folder = out/'candidates'/digest(team)[:20]
        write(folder/'team.json', team)
        subprocess.run([sys.executable, 'tools/build_agent.py', '--team', str(folder/'team.json'), '--out', str(folder)],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        return folder

    def job(spec):
        team, phase, games, policy, seed = spec
        folder = out/'candidates'/digest(team)[:20]
        key = digest([team, phase, games, policy, seed, digest(provenance), hashlib.sha256(suites[phase].read_bytes()).hexdigest()])
        report = out/'jobs'/(key+'.json'); report.parent.mkdir(exist_ok=True)
        sha = hashlib.sha256((folder/'agent.py').read_bytes()).hexdigest()
        if report.exists():
            result = json.loads(report.read_text())
            assert result['agentSha256'] == sha and result['games'] == games and result['team'] == team
            assert len(result['results']) == games and not any(r['errors'] for r in result['results'])
            return result
        env = os.environ.copy()
        for name in ('CUSTOM', 'MIRROR', 'STATELESS', 'SAVE_LOGS', 'TRACE_DIR', 'OPP_TEAM_FILE', 'OPP_AGENT_FILE'):
            env.pop(name, None)
        temporary = report.with_suffix('.pending')
        env.update(AGENT_FILE=str(folder/'agent.py'), TEAM_FILE=str(folder/'team.json'), OPPONENT=policy,
                   SEED=str(seed), SPARSE='1', REPORT=str(temporary), NO_LAST_LOSS='1')
        if policy == 'frozen':
            env.update(OPP_TEAM_FILE=str(ROOT/'archive/v4_3/team.json'), OPP_AGENT_FILE=str(ROOT/'archive/v4_3/agent.py'))
        else: env['CUSTOM'] = str(suites[phase])
        with report.with_suffix('.log').open('w') as log:
            subprocess.run(['node', 'tools/benchmark.js', str(games)], cwd=ROOT, env=env, check=True,
                           stdout=log, stderr=subprocess.STDOUT, timeout=max(1, deadline-time.monotonic()))
        result = json.loads(temporary.read_text())
        assert result['agentSha256'] == sha and result['games'] == games and not any(r['errors'] for r in result['results'])
        temporary.replace(report)
        return result

    def evaluate(teams, phase, games, round_id):
        nonlocal completed
        seed = args.seed + {'development': 0, 'validation': 10000, 'confirmation': 20000}[phase] + round_id*101
        ranked = []
        # One candidate per batch avoids concurrent writes to its compiled files.
        for index, team in enumerate(teams):
            if time.monotonic() >= deadline: raise TimeoutError('Time budget reached; rerun to resume.')
            specs = [(team, phase, games, policy, seed) for policy in POLICIES]
            # Conservatively require room for a complete candidate before starting it.
            keys = [digest([team, phase, games, p, seed, digest(provenance), hashlib.sha256(suites[phase].read_bytes()).hexdigest()]) for p in POLICIES]
            missing = sum(not (out/'jobs'/(k+'.json')).exists() for k in keys)
            if completed + missing*games > args.max_games: raise TimeoutError('Battle budget reached; increase --max-games to resume.')
            prepare(team)
            # Compilation happens once here; each policy gets a separate immutable copy path.
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                reports = list(executor.map(job, specs))
            completed += missing*games
            rates = [(r['wins']+.5*r['draws'])/r['games'] for r in reports]
            record = dict(id=digest(team)[:20], team=team, score=.7*sum(rates)/len(rates)+.3*min(rates),
                          rates=dict(zip(POLICIES, rates)), games=sum(r['games'] for r in reports),
                          incumbent=team == INCUMBENT)
            ranked.append(record)
            write(out/'progress.json', dict(phase=phase, round=round_id, candidatesDone=index+1,
                                          candidatesTotal=len(teams), completedGames=completed))
            print(f'{phase}/{round_id} {index+1}/{len(teams)} score={record["score"]:.3f} total_games={completed}', flush=True)
        ranked.sort(key=lambda r: (r['score'], r['incumbent']), reverse=True)
        write(out/f'{phase}-{round_id}-ranking.json', ranked)
        return ranked

    rng = random.Random(args.seed)
    pool = [[default(n) for n in trio] for trio in itertools.combinations(OPTIONS['pokemon'], 3)]
    if args.profile != 'full': pool = rng.sample(pool, 3 if args.profile == 'smoke' else 47)
    teams = unique([INCUMBENT]+pool)
    schedule = [2] if args.profile == 'smoke' else ([4, 12, 48] if args.profile == 'full' else [4, 12])
    try:
        for round_id, games in enumerate(schedule):
            ranking = evaluate(teams, 'development', games, round_id)
            keep = max(2, len(ranking)//(8 if args.profile == 'full' and round_id == 0 else 4))
            teams = unique([INCUMBENT]+[r['team'] for r in ranking[:keep]])
        children = [mutate(t, rng) for t in teams[:12] for _ in range(1 if args.profile == 'smoke' else 8)]
        ranking = evaluate(unique(teams+children), 'development', 2 if args.profile == 'smoke' else 24, 4)
        finalists = unique([INCUMBENT]+[r['team'] for r in ranking[:3]])
        ranking = evaluate(finalists, 'validation', 2 if args.profile == 'smoke' else 96, 0)
        challenger = next(r['team'] for r in ranking if not r['incumbent'])
        confirmation = evaluate([INCUMBENT, challenger], 'confirmation', 2 if args.profile == 'smoke' else 192, 0)
        selected = confirmation[0]
        folder = prepare(selected['team'])
        with zipfile.ZipFile(out/'best_candidate.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for name in ('agent.py', 'team.txt'): z.write(folder/name, name)
        write(out/'result.json', dict(status='complete', selected=selected, confirmation=confirmation,
                                    warning='Exploratory league result, not proof of tournament superiority. Review paired held-out results before promotion.',
                                    completedGames=completed, provenance=provenance))
    except (TimeoutError, subprocess.TimeoutExpired) as exc:
        write(out/'status.json', dict(status='paused', reason=str(exc), completedGames=completed))
        print(str(exc), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['smoke', 'quick', 'full'], default='quick')
    parser.add_argument('--out', default='runs/team-search')
    parser.add_argument('--seed', type=int, default=43179)
    parser.add_argument('--hours', type=float, default=6)
    parser.add_argument('--max-games', type=int, default=60000)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    assert args.hours > 0 and args.max_games > 0 and 1 <= args.workers <= 3
    run(args)
