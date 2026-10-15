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
METHOD_VERSION = 2

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

def population(profile, seed):
    pool = [[default(n) for n in trio] for trio in itertools.combinations(OPTIONS['pokemon'], 3)]
    if profile != 'full': pool = random.Random(seed).sample(pool, 6 if profile == 'smoke' else 47)
    return pool

def shard_indices(size, index, count):
    assert 0 <= index < count
    return list(range(index, size, count))

def ranking_key(record):
    return (record['score'], record['hpMargin'], record['incumbent'], record['id'])

def read_screenings(paths, campaign, pool, count):
    """Read compact data only; never execute or extract code from other runs."""
    seen=set(); teams=[INCUMBENT]; covered=set()
    for path in paths:
        with zipfile.ZipFile(path) as z:
            assert z.namelist() == ['screening.json'], 'Unexpected screening archive contents'
            assert z.getinfo('screening.json').file_size < 10_000_000
            payload=json.loads(z.read('screening.json'))
        assert payload['status']=='complete' and payload['campaign']==campaign, 'Mismatched or incomplete search'
        index=payload['shardIndex']
        assert payload['shardCount']==count and index not in seen, 'Duplicate or mismatched shard'
        expected=shard_indices(len(pool), index, count)
        assert payload['populationIndices']==expected and payload['populationSha256']==digest(pool), 'Incorrect shard coverage'
        assert not covered.intersection(expected)
        covered.update(expected);seen.add(index)
        assert payload['finalists'], 'Missing finalists'
        for team in payload['finalists']:
            validate(team);teams.append(team)
    assert seen==set(range(count)) and covered==set(range(len(pool))), 'All completed shards are required'
    return unique(teams)

def compare_confirmation(control, challenger):
    """Matched outcomes with a descriptive interval conditional on this league."""
    rng=random.Random(61273); strata=[]; policies={}
    improved=regressed=0
    for policy, a, b in zip(POLICIES,control,challenger):
        assert a['games']==b['games'] and a['team']==INCUMBENT
        groups={};deltas=[]
        for x,y in zip(a['results'],b['results']):
            for key in ('seed','side','opponentSets','baseline'):assert x[key]==y[key]
            score=lambda r:1. if r['winner']=='agent' else .5 if not r['winner'] else 0.
            delta=score(y)-score(x);deltas.append(delta)
            improved+=delta>0;regressed+=delta<0
            # Frozen opponent is one fixed team: resample its side-reversed
            # seed pairs. Other policies resample complete opposing-set clusters.
            cluster=x['seed'] if policy=='frozen' else x['opponentSets']
            groups.setdefault(digest(cluster),[]).append(delta)
        strata.append(list(groups.values()))
        policies[policy]=dict(controlWins=a['wins'],challengerWins=b['wins'],games=a['games'],
                              scoreGainPP=100*sum(deltas)/len(deltas))
    boot=[]
    for _ in range(2000):
        values=[]
        for groups in strata:
            sample=[rng.choice(groups) for _ in groups]
            values.append(sum(map(sum,sample))/sum(map(len,sample)))
        boot.append(100*sum(values)/len(values))
    boot.sort()
    return dict(policies=policies,improvedGames=improved,regressedGames=regressed,
                meanScoreGainPP=sum(p['scoreGainPP'] for p in policies.values())/len(policies),
                pairedScoreInterval95=[boot[50],boot[1949]],
                method='2000 stratified paired bootstrap replicates, seed 61273; opposing-set clusters for adaptive/tactical, seed pairs for fixed frozen team. Conditional on this experimental league; not a tournament win probability.')

def run(args):
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    config = {k: v for k, v in vars(args).items() if k not in ('out', 'hours', 'max_games', 'workers', 'screening')}
    config['screeningSha256']=sorted(hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in args.screening)
    files = ['agent_core.py', 'team.json', 'tools/team_search.py', 'tools/build_agent.py', 'tools/benchmark.js',
             'tools/worker.py', 'tools/opponents.js', 'tools/make_eval_teams.py', 'package-lock.json',
             'research/options.json', 'research/battle_data.json', 'research/enemy_sets.json', 'research/SHOWDOWN_LICENSE.txt',
             'archive/v4_3/agent.py', 'archive/v4_3/team.json', 'archive/v1/agent.py']
    provenance = dict(config=config, hashes={f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    campaign=dict(methodVersion=METHOD_VERSION, profile=args.profile, seed=args.seed, hashes=provenance['hashes'])
    pool=population(args.profile,args.seed)
    merged=read_screenings(args.screening,campaign,pool,args.shard_count) if args.mode=='finalize' else None
    manifest = out/'manifest.json'
    if manifest.exists():
        assert json.loads(manifest.read_text()) == provenance, 'Inputs changed. Use a new output directory.'
    else: write(manifest, provenance)
    deadline = time.monotonic() + args.hours*3600
    evidence={}
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
            evidence[digest(team)]=reports
            completed += missing*games
            rates = [(r['wins']+.5*r['draws'])/r['games'] for r in reports]
            record = dict(id=digest(team)[:20], team=team, score=.7*sum(rates)/len(rates)+.3*min(rates),
                          rates=dict(zip(POLICIES, rates)), games=sum(r['games'] for r in reports),
                          hpMargin=sum(x['finalHP']['agent']-x['finalHP']['opponent'] for r in reports for x in r['results'])/sum(r['games'] for r in reports),
                          incumbent=team == INCUMBENT)
            ranked.append(record)
            write(out/'progress.json', dict(phase=phase, round=round_id, candidatesDone=index+1,
                                          candidatesTotal=len(teams), completedGames=completed))
            print(f'{phase}/{round_id} {index+1}/{len(teams)} score={record["score"]:.3f} total_games={completed}', flush=True)
        ranked.sort(key=ranking_key, reverse=True)
        write(out/f'{phase}-{round_id}-ranking.json', ranked)
        return ranked

    rng = random.Random(args.seed)
    indices=shard_indices(len(pool),args.shard_index,args.shard_count) if args.mode=='screen' else list(range(len(pool)))
    teams = unique([INCUMBENT]+[pool[i] for i in indices])
    schedule = [2] if args.profile == 'smoke' else ([4, 12, 48] if args.profile == 'full' else [4, 12])
    if args.mode=='screen' and args.profile!='smoke':schedule[0]=8
    try:
        if args.mode=='finalize':
            ranking=evaluate(merged,'development',2 if args.profile=='smoke' else 48,5)
        else:
            for round_id, games in enumerate(schedule):
                ranking = evaluate(teams, 'development', games, round_id)
                keep = max(2, len(ranking)//(8 if args.profile == 'full' and round_id == 0 else 4))
                teams = unique([INCUMBENT]+[r['team'] for r in ranking[:keep]])
            rng=random.Random(args.seed+args.shard_index*7919)
            children = [mutate(t, rng) for t in teams[:12] for _ in range(1 if args.profile == 'smoke' else 8)]
            ranking = evaluate(unique(teams+children), 'development', 2 if args.profile == 'smoke' else 24, 4)
            if args.mode=='screen':
                payload=dict(status='complete',campaign=campaign,shardIndex=args.shard_index,shardCount=args.shard_count,
                             populationIndices=indices,populationSha256=digest(pool),
                             finalists=[r['team'] for r in ranking if not r['incumbent']][:6],
                             ranking=ranking,completedGames=completed)
                write(out/'screening.json',payload)
                with zipfile.ZipFile(out/f'redline-screen-{args.shard_index+1}.zip','w',zipfile.ZIP_DEFLATED) as z:
                    z.write(out/'screening.json','screening.json')
                print('Screening complete. Run the final comparison after all shards complete.',flush=True)
                return
        finalists = unique([INCUMBENT]+[r['team'] for r in ranking[:3]])
        ranking = evaluate(finalists, 'validation', 2 if args.profile == 'smoke' else 96, 0)
        challenger = next(r['team'] for r in ranking if not r['incumbent'])
        confirmation = evaluate([INCUMBENT, challenger], 'confirmation', 2 if args.profile == 'smoke' else 192, 0)
        comparison=compare_confirmation(evidence[digest(INCUMBENT)],evidence[digest(challenger)])
        selected = confirmation[0]
        folder = prepare(selected['team'])
        with zipfile.ZipFile(out/'best_candidate.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for name in ('agent.py', 'team.txt'): z.write(folder/name, name)
        write(out/'result.json', dict(status='complete', selected=selected, confirmation=confirmation,comparison=comparison,
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
    parser.add_argument('--mode',choices=['search','screen','finalize'],default='search')
    parser.add_argument('--shard-index',type=int,default=0,help='Zero-based screen partition')
    parser.add_argument('--shard-count',type=int,default=3)
    parser.add_argument('--screening',nargs='*',default=[],help='Completed compact screening ZIPs for finalize')
    args = parser.parse_args()
    assert args.hours > 0 and args.max_games > 0 and 1 <= args.workers <= 3
    assert 1 <= args.shard_count <= 16 and 0 <= args.shard_index < args.shard_count
    if args.mode=='finalize':assert len(args.screening)==args.shard_count, 'Provide every completed screening ZIP'
    run(args)
