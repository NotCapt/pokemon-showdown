"""Frozen follow-up: exact v4.7/v4.6 head-to-head, self-play and new opponents."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import team_search

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/v4_7-matchups-v1'
LABELS = ('v4_6', 'v4_7')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
score = lambda row: 1.0 if row['winner'] == 'agent' else 0.0 if row['winner'] == 'baseline' else 0.5


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix('.tmp')
    pending.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    for attempt in range(20):
        try:
            pending.replace(path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(.05)


def relative(path):
    return path.relative_to(ROOT).as_posix()


def verify(plan):
    for name, digest in plan['inputSha256'].items():
        assert sha(ROOT / name) == digest, 'Changed frozen input: ' + name


def previous_records():
    # Inspect stored results and suites, excluding extracted copies and traces.
    old_tags, old_teams, files = set(), set(), 0
    for path in (ROOT / 'research').rglob('*.json'):
        parts = path.relative_to(ROOT / 'research').parts
        if parts[0] == OUT.name or any('reproducer-check' in p or 'traces' in p for p in parts):
            continue
        if path.name.endswith(('.stamp.json', '.job.json', '.tested.json')):
            continue
        if not (path.parent.name in ('jobs', 'reports', 'suites') or path.parent == ROOT / 'research'
                or path.name.startswith('teams-')):
            continue
        value = load(path)
        if isinstance(value, dict) and isinstance(value.get('results'), list):
            files += 1
            for row in value['results']:
                if isinstance(row.get('seed'), list) and len(row['seed']) == 4:
                    old_tags.add(row['seed'][3])
                if isinstance(row.get('opponentSets'), list):
                    old_teams.add(team_search.digest(row['opponentSets']))
        elif isinstance(value, list):
            for team in value:
                if isinstance(team, list) and team and isinstance(team[0], dict) and 'moves' in team[0]:
                    old_teams.add(team_search.digest(team))
    return old_tags, old_teams, files


def prepare():
    if (OUT / 'plan.json').exists():
        plan = load(OUT / 'plan.json')
        verify(plan)
        return plan
    OUT.mkdir(parents=True, exist_ok=True)
    options = load(ROOT / 'research/options.json')
    old_tags, old_teams, old_reports = previous_records()
    teams = {label: load(ROOT / 'archive' / label / 'team.json') for label in LABELS}
    assert teams['v4_6'] == teams['v4_7']
    for label in LABELS:
        team_search.validate(teams[label])
        tree = ast.parse((ROOT / 'archive' / label / 'agent.py').read_text(encoding='utf-8'))
        own = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and getattr(n.targets[0], 'id', None) == 'OWN')
        assert list(own.values()) == teams[label]
    # Coherent builds use the unchanged earlier generator, with a new seed.
    coherent_path = OUT / 'suites/coherent-all.json'
    coherent_path.parent.mkdir(exist_ok=True)
    subprocess.run([sys.executable, 'tools/make_eval_teams.py', '--seed', '260716903',
                    '--count', '64', '--out', relative(coherent_path)], cwd=ROOT, check=True)
    coherent = load(coherent_path)
    rng = random.Random(260716927)
    uniform = []
    for _ in range(64):
        team = []
        for name in rng.sample(list(options['pokemon']), 3):
            legal = options['pokemon'][name]
            team.append(dict(name=name, ability=rng.choice(legal['abilities']),
                             item=rng.choice(options['items']), nature=rng.choice(options['natures']),
                             evs=rng.choice(options['evPresets']), moves=rng.sample(legal['legalMoves'], 4)))
        uniform.append(team)
    write(OUT / 'suites/uniform-all.json', uniform)
    fresh = set()
    for cohort, suite in (('coherent', coherent), ('uniform', uniform)):
        for team in suite:
            team_search.validate(team)
            key = team_search.digest(team)
            assert key not in old_teams and key not in fresh
            fresh.add(key)
        assert {p['name'] for team in suite for p in team} == set(options['pokemon'])
        for chunk in range(4):
            write(OUT / 'suites' / f'{cohort}-{chunk:02d}.json', suite[chunk*16:(chunk+1)*16])
    permutations = list(itertools.permutations(range(3)))
    for index, order in enumerate(permutations):
        write(OUT / 'orders' / f'{index}.json', [teams['v4_7'][i] for i in order])
    jobs, used_tags = [], set(old_tags)

    def tag():
        result = next(value for value in range(48001, 65000) if value not in used_tags)
        used_tags.add(result)
        return result

    def job(name, candidate, games, seed, policy, category, **extra):
        jobs.append(dict(name=name, candidate=candidate, games=games, seed=seed, policy=policy,
                         category=category, teamFile=f'archive/{candidate}/team.json', **extra))

    for chunk in range(8):
        job(f'head-native-{chunk:02d}', 'v4_7', 32, tag(), 'frozen', 'head-native', opponent='v4_6')
    for label in ('v4_7', 'v4_6'):
        for chunk in range(4):
            job(f'self-native-{label}-{chunk:02d}', label, 32, tag(), 'frozen', 'self-native', opponent=label)
    for cohort in ('coherent', 'uniform'):
        for policy in ('random', 'tactical', 'adaptive'):
            for chunk in range(4):
                seed = tag()
                for label in LABELS:
                    job(f'{cohort}-{policy}-{chunk:02d}-{label}', label, 32, seed, policy, 'random-field',
                        cohort=cohort, custom=relative(OUT / 'suites' / f'{cohort}-{chunk:02d}.json'), chunk=chunk)
    for candidate, opponent, category in (('v4_7', 'v4_6', 'head-orders'), ('v4_7', 'v4_7', 'self-orders')):
        for i in range(6):
            for j in range(6):
                spec = dict(opponent=opponent, ownOrder=i, opponentOrder=j,
                            opponentTeam=relative(OUT / 'orders' / f'{j}.json'))
                job(f'{category}-{i}-{j}', candidate, 4, tag(), 'frozen', category, **spec)
                jobs[-1]['teamFile'] = relative(OUT / 'orders' / f'{i}.json')
    protocol = '''# Fresh v4.7 matchup tests

Freeze exact v4.6/v4.7 sources, teams, simulator, suites and schedule before results.
No policy/team changes, selection, tuning or release promotion during this test.
Local only; no practice uploads or final competition submission.

- Native head-to-head: 256 games, v4.7 versus v4.6.
- Native self-play: 128 games each for v4.7 and v4.6 (symmetry control).
- All 36 team-order pairings: 4 games each, both v4.7-v4.6 and v4.7-v4.7.
- Fresh random field: 64 coherent builds plus 64 uniformly sampled legal builds,
  each played twice (alternating sides) under random, tactical and adaptive policy,
  for each release. 768 games per release; 2,336 games overall.

All 24 allowed species appear in each random-build cohort. Uniform legal builds
can have poor set synergy; coherent builds use the unchanged independent generator.
Random policy samples legal moves and uses the first legal forced replacement;
tactical policy uses the existing damage heuristic; adaptive policy can switch
voluntarily using its own true state and a model of public enemy information.
Only documented public information reaches Python agents; own boosts are sparse,
enemy sets and bench hidden. Native sources retain their exact compiled own-team
configurations; changing team order does not change any species configuration.

Each two-game seed pair alternates sides. The two releases share the same random
opponents/seeds/sides. New simulator seed tags and build fingerprints do not occur
in inspected earlier stored results/suites. HP adjudicates battles after turn 100.

Report raw wins/losses/draws, win+half-draw scores, game lengths, capped games,
and all-order matrices. Native head intervals resample whole two-game seed pairs.
Random-field gains use 10,000 paired bootstrap samples (seed 260716991), clustering
whole builds across all three policies and sides, stratified by build cohort.
Intervals are descriptive local-field estimates. Self-play is a symmetry and
order diagnostic, not evidence of strength against outside players. Concurrent
battle latency is diagnostic only and is not a controlled performance benchmark.
'''
    (OUT / 'PROTOCOL.md').write_text(protocol, encoding='utf-8')
    inputs = ['tools/test_v4_7_matchups.py', 'tools/benchmark.js', 'tools/worker.py', 'tools/opponents.js',
              'tools/make_eval_teams.py', 'tools/team_search.py', 'archive/v1/agent.py',
              'research/options.json', 'research/battle_data.json', 'package-lock.json', relative(OUT / 'PROTOCOL.md')]
    inputs += [f'archive/{label}/{name}' for label in LABELS for name in ('agent.py', 'team.json')]
    inputs += [relative(p) for directory in ('suites', 'orders') for p in (OUT / directory).glob('*.json')]
    plan = dict(methodVersion=1, jobs=jobs, inputSha256={name: sha(ROOT / name) for name in inputs},
                sourceSha256={label: sha(ROOT / 'archive' / label / 'agent.py') for label in LABELS},
                plannedGames=sum(j['games'] for j in jobs), freshBuilds=len(fresh), inspectedPriorReports=old_reports,
                priorSeedTags=len(old_tags), actualSeedTags=sorted(used_tags - old_tags), priorSeedTagOverlap=[],
                generatedBuildOverlap=[], simulatorVersion='0.11.11', permutations=[list(p) for p in permutations],
                note='Exact existing releases; no candidate modification, new release or tournament probability claim.')
    assert plan['plannedGames'] == 2336 and len(fresh) == 128
    assert plan['sourceSha256']['v4_7'] == '5dac01afbde238d621a27ca2c11f8bc4e2ee0e094af26f5bb9c47d0c170b62fb'
    assert plan['sourceSha256']['v4_6'] == '07b1e968db139b43ebf4dcf49900719977096ac42434d217f1f8534984183ac5'
    write(OUT / 'plan.json', plan)
    return plan


def audit_report(spec, report, plan):
    assert report['agentSha256'] == plan['sourceSha256'][spec['candidate']]
    assert report['team'] == load(ROOT / spec['teamFile'])
    assert report['simulatorVersion'] == plan['simulatorVersion'] and report['sparseBoosts'] and not report['stateless']
    assert report['opponentPolicySha256'] == plan['inputSha256']['tools/opponents.js']
    assert report['games'] == len(report['results']) == spec['games']
    if 'opponent' in spec:
        assert report['opponentAgentSha256'] == plan['sourceSha256'][spec['opponent']]
        team = load(ROOT / spec.get('opponentTeam', f"archive/{spec['opponent']}/team.json"))
    else:
        assert report['opponentAgentSha256'] is None
        suite = load(ROOT / spec['custom'])
    for i, row in enumerate(report['results']):
        assert row['errors'] == 0 and row['game'] == i and row['baseline'] == spec['policy']
        assert row['seed'] == [1, 2, i//2+1, spec['seed']] and row['side'] == (2 if i % 2 else 1)
        assert row['winner'] in ('agent', 'baseline', '')
        assert row['opponentSets'] == (team if 'opponent' in spec else suite[i//2])
    assert report['wins'] == sum(row['winner'] == 'agent' for row in report['results'])
    assert report['losses'] == sum(row['winner'] == 'baseline' for row in report['results'])
    assert report['draws'] == sum(not row['winner'] for row in report['results'])
    if spec['category'] == 'self-native':
        for a, b in zip(report['results'][::2], report['results'][1::2]):
            assert score(a) + score(b) == 1, 'Native self-play side symmetry failed'


def run_one(spec, plan):
    path = OUT / 'jobs' / (spec['name'] + '.json')
    path.parent.mkdir(exist_ok=True)
    stamp = dict(planSha256=sha(OUT / 'plan.json'), specification=spec)
    if path.exists():
        assert load(path.with_suffix('.stamp.json')) == stamp
        result = load(path)
    else:
        env = dict(os.environ)
        for name in ('CUSTOM', 'MIRROR', 'STATELESS', 'SAVE_LOGS', 'TRACE_DIR', 'OPP_TEAM_FILE',
                     'OPP_AGENT_FILE', 'AGENT_FILE', 'TEAM_FILE', 'OPPONENT', 'SEED', 'SPARSE', 'REPORT'):
            env.pop(name, None)
        pending = path.with_suffix('.pending')
        env.update(AGENT_FILE=f"archive/{spec['candidate']}/agent.py", TEAM_FILE=spec['teamFile'],
                   OPPONENT=spec['policy'], SEED=str(spec['seed']), SPARSE='1', REPORT=str(pending), NO_LAST_LOSS='1')
        if 'opponent' in spec:
            env.update(OPP_AGENT_FILE=f"archive/{spec['opponent']}/agent.py",
                       OPP_TEAM_FILE=spec.get('opponentTeam', f"archive/{spec['opponent']}/team.json"))
        else:
            env['CUSTOM'] = spec['custom']
        with path.with_suffix('.log').open('w', encoding='utf-8') as log:
            subprocess.run(['node', 'tools/benchmark.js', str(spec['games'])], cwd=ROOT, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1800)
        result = load(pending)
        audit_report(spec, result, plan)
        pending.replace(path)
        write(path.with_suffix('.stamp.json'), stamp)
    audit_report(spec, result, plan)
    return spec, result


def counts(rows):
    wins, losses, draws = [sum(row['winner'] == name for row in rows) for name in ('agent', 'baseline', '')]
    return dict(wins=wins, losses=losses, draws=draws, games=len(rows),
                scorePct=100 * (wins + .5*draws) / len(rows),
                averageTurns=sum(row['turns'] for row in rows)/len(rows),
                turn101Adjudications=sum(row['turns'] > 100 for row in rows),
                meanFinalHPDifference=sum(row['finalHP']['agent']-row['finalHP']['opponent'] for row in rows)/len(rows))


def interval(values):
    values.sort()
    return [values[250], values[9749]]


def summarize():
    plan = prepare()
    reports = []
    for spec in plan['jobs']:
        path = OUT / 'jobs' / (spec['name'] + '.json')
        assert load(path.with_suffix('.stamp.json')) == dict(planSha256=sha(OUT / 'plan.json'), specification=spec)
        report = load(path)
        audit_report(spec, report, plan)
        reports.append((spec, report))
    assert sum(r['games'] for _, r in reports) == plan['plannedGames']
    flatten = lambda category, label: [row for job, r in reports if job['category'] == category
                                      and job['candidate'] == label for row in r['results']]
    result = dict(completedGames=plan['plannedGames'], planSha256=sha(OUT / 'plan.json'), allSourcesSchedulesAndActionsAudited=True,
                  headNative=counts(flatten('head-native', 'v4_7')), headOrders=counts(flatten('head-orders', 'v4_7')),
                  selfNative={label: counts(flatten('self-native', label)) for label in LABELS},
                  selfOrders=counts(flatten('self-orders', 'v4_7')), randomField={},
                  sourceSha256=plan['sourceSha256'], policyOrTeamChanges=False)
    rng = random.Random(260716991)
    native = flatten('head-native', 'v4_7')
    clusters = [(score(a)+score(b))/2 for a, b in zip(native[::2], native[1::2])]
    result['headNative']['pairedSeedBootstrap95Pct'] = interval([100*sum(rng.choices(clusters, k=len(clusters)))/len(clusters) for _ in range(10000)])
    paired = {}
    random_jobs = {(job['cohort'], job['policy'], job['chunk'], job['candidate']): report
                   for job, report in reports if job['category'] == 'random-field'}
    for cohort in ('coherent', 'uniform'):
        paired[cohort] = {}
        result['randomField'][cohort] = {}
        for policy in ('random', 'tactical', 'adaptive'):
            result['randomField'][cohort][policy] = {}
            rows = {label: [row for chunk in range(4) for row in random_jobs[cohort, policy, chunk, label]['results']] for label in LABELS}
            for label in LABELS:
                result['randomField'][cohort][policy][label] = counts(rows[label])
            for a, b in zip(rows['v4_6'], rows['v4_7']):
                for key in ('seed', 'side', 'opponentSets', 'baseline'):
                    assert a[key] == b[key]
                key = team_search.digest(a['opponentSets'])
                paired[cohort].setdefault(key, []).append(score(b)-score(a))
        assert len(paired[cohort]) == 64 and all(len(v) == 6 for v in paired[cohort].values())
    combined = {label: counts(flatten('random-field', label)) for label in LABELS}
    gains = []
    cohort_means = {cohort: [sum(v)/len(v) for v in groups.values()] for cohort, groups in paired.items()}
    for _ in range(10000):
        gains.append(50*sum(sum(rng.choices(values, k=len(values)))/len(values) for values in cohort_means.values()))
    improved = regressed = 0
    for groups in paired.values():
        for values in groups.values():
            improved += sum(v > 0 for v in values)
            regressed += sum(v < 0 for v in values)
    result['randomFieldCombined'] = dict(versions=combined,
        scoreGainPP=combined['v4_7']['scorePct']-combined['v4_6']['scorePct'],
        pairedBuildBootstrap95PP=interval(gains), improvedGames=improved, regressedGames=regressed,
        method='10,000 paired whole-build bootstrap samples across all policies/sides; stratified coherent/uniform; descriptive local-field interval')
    result['orderMatrices'] = {category: [[counts(next(r['results'] for j, r in reports if j['category'] == category
                                                   and j['ownOrder'] == i and j['opponentOrder'] == k))
                                         for k in range(6)] for i in range(6)]
                               for category in ('head-orders', 'self-orders')}
    verify(plan)
    result['auditorSha256'] = sha(Path(__file__))
    write(OUT / 'result.json', result)
    render(result, plan)
    print(json.dumps({k: v for k, v in result.items() if k != 'orderMatrices'}, indent=2), flush=True)


def render(result, plan):
    show = lambda v: f"{v['wins']}-{v['losses']}-{v['draws']}"
    lines = ['# Fresh v4.7 matchup results', '',
             '**2,336 new local simulator games**, with sources, schedules, legal execution and native self-play symmetry verified. Exact archived releases; no policy or team changes. These are follow-up tests, not a new release-selection study.', '',
             '| Matchup | v4.7 wins-losses-draws | Score | Games reaching turn 101 |',
             '| --- | ---: | ---: | ---: |']
    for label, key in (('v4.7 versus v4.6, native team order', 'headNative'), ('v4.7 versus v4.6, all 36 order pairings', 'headOrders'),
                       ('v4.7 versus itself, native order', None), ('v4.7 versus itself, all 36 order pairings', 'selfOrders')):
        v = result[key] if key else result['selfNative']['v4_7']
        lines.append(f"| {label} | {show(v)} | {v['scorePct']:.2f}% | {v['turn101Adjudications']} |")
    native = result['headNative']
    lines += ['', f"Native head-to-head descriptive paired-seed 95% interval: {native['pairedSeedBootstrap95Pct'][0]:.2f}% to {native['pairedSeedBootstrap95Pct'][1]:.2f}%. Side-swapped v4.6 self-play control: {show(result['selfNative']['v4_6'])}. Native self-play pairs must sum to one scored point; this passed for both releases. A roughly 50% self-play score measures symmetry and team-order effects, not strength against outside agents.", '',
              '## Fresh random opponent builds', '',
              'Each cohort contains 64 new legal three-Pokémon builds covering all 24 species. Coherent sets favor usable attacks, coverage and EVs; uniformly random sets can have poor synergy. Each build plays both sides under each of three fixed policies. Random actions choose legal moves and the first forced replacement; tactical uses the existing damage heuristic; adaptive models public enemy information and can switch voluntarily.', '',
              '| Builds | Opponent policy | v4.6 W-L-D | v4.7 W-L-D | v4.7 score gain |',
              '| --- | --- | ---: | ---: | ---: |']
    for cohort, policies in result['randomField'].items():
        for policy, versions in policies.items():
            a, b = versions['v4_6'], versions['v4_7']
            lines.append(f"| {cohort} | {policy} | {show(a)} | {show(b)} | {b['scorePct']-a['scorePct']:+.2f} pp |")
    field = result['randomFieldCombined']
    lo, hi = field['pairedBuildBootstrap95PP']
    lines += ['', f"Across the equally weighted six cells (768 games per release), v4.6: **{show(field['versions']['v4_6'])}**; v4.7: **{show(field['versions']['v4_7'])}**. Paired gain **{field['scoreGainPP']:+.3f} pp**, descriptive 95% interval **[{lo:+.2f}, {hi:+.2f}] pp**. {field['improvedGames']} outcomes improved and {field['regressedGames']} regressed. Intervals cluster whole builds across all policies and both sides, stratified by cohort (10,000 replicates). Raw wins alone should not be mistaken for performance against well-built tournament teams.", '',
              '## Team order diagnostics', '',
              'D = Dragapult, S = Snorlax, C = Corviknight. Rows use v4.7; columns use the opponent. Each cell is wins-losses-draws in four games. Every order contains the same original legal configurations.']
    names = [''.join('DSC'[i] for i in order) for order in plan['permutations']]
    for category, title in (('head-orders', 'v4.7 versus v4.6'), ('self-orders', 'v4.7 versus v4.7')):
        lines += ['', '### ' + title, '', '| Own / foe | ' + ' | '.join(names) + ' |', '| --- | ' + ' | '.join(['---:']*6) + ' |']
        for name, row in zip(names, result['orderMatrices'][category]):
            lines.append('| ' + name + ' | ' + ' | '.join(show(v) for v in row) + ' |')
    lines += ['', '## Reproduction and limits', '',
              'Pinned Showdown 0.11.11; Python 3.10; Node 24. Read PROTOCOL.md and plan.json for the frozen inputs and seeds. Reports contain the actual opponent configurations for audit; Python agents never receive them. Enemy bench/sets remain hidden and own boosts sparse. The benchmark adjudicates unfinished games by summed HP after turn 100. Native sources preserve the same Roost/Rest forecasting limitations documented in v4.7. Concurrent decision times are not a controlled latency benchmark. These scores and intervals describe this local test field, not tournament win probabilities.', '',
              'Run `python tools/test_v4_7_matchups.py --audit` to recompute the report from frozen records, or `--run --workers 6` to resume missing jobs. Existing results require matching plan stamps. No practice upload or final competition entry was performed by this test.']
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def run(workers):
    plan = prepare()
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, spec, plan) for spec in plan['jobs']]
        for future in as_completed(futures):
            spec, report = future.result()
            done += report['games']
            write(OUT / 'progress.json', dict(completedGames=done, plannedGames=plan['plannedGames'], lastJob=spec['name']))
            print(json.dumps(dict(completedGames=done, plannedGames=plan['plannedGames'], job=spec['name'],
                                  wins=report['wins'], losses=report['losses'], draws=report['draws'])), flush=True)
    verify(plan)
    summarize()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--audit', action='store_true')
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    if args.run:
        run(args.workers)
    elif args.audit:
        summarize()
    else:
        plan = prepare()
        print(json.dumps(dict(plannedGames=plan['plannedGames'], jobs=len(plan['jobs']), freshBuilds=plan['freshBuilds'],
                              inspectedPriorReports=plan['inspectedPriorReports'], planSha256=sha(OUT / 'plan.json')), indent=2))
