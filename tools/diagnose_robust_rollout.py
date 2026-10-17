"""Replay selected historical failures; diagnostic development data only."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / 'research/v4_7-matchups-v1'
OUT = ROOT / 'research/robust-rollout-v1/diagnostics'
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
plan = load(PRIOR / 'plan.json')
specs = {s['name']: s for s in plan['jobs']}
cases = [('coherent-adaptive-00', 0), ('coherent-adaptive-00', 22),
         ('coherent-adaptive-01', 2), ('uniform-adaptive-01', 28),
         ('coherent-tactical-01', 10), ('coherent-adaptive-00', 6)]
jobs = [(name + '-' + label, game) for name, game in cases for label in ('v4_7', 'v4_6')]
jobs += [('head-native-00', 22), ('head-native-05', 7)]


def run(pair):
    name, game = pair
    spec = specs[name]
    folder = OUT / f'{name}-game-{game:02d}'
    folder.mkdir(parents=True, exist_ok=True)
    expected = load(PRIOR / 'jobs' / (name + '.json'))['results'][game]
    report = folder / 'report.json'
    if not report.exists():
        env = dict(os.environ)
        for key in ('CUSTOM', 'MIRROR', 'STATELESS', 'SAVE_LOGS', 'TRACE_DIR', 'OPP_TEAM_FILE',
                    'OPP_AGENT_FILE', 'AGENT_FILE', 'TEAM_FILE', 'OPPONENT', 'SEED', 'SPARSE', 'REPORT'):
            env.pop(key, None)
        env.update(AGENT_FILE=f"archive/{spec['candidate']}/agent.py", TEAM_FILE=spec['teamFile'],
                   OPPONENT=spec['policy'], SEED=str(spec['seed']), SPARSE='1', NO_LAST_LOSS='1',
                   REPORT=str(report), TRACE_GAME=str(game), TRACE_DIR=str(folder / 'traces'), SAVE_LOGS=str(folder / 'logs'))
        if 'opponent' in spec:
            env.update(OPP_AGENT_FILE=f"archive/{spec['opponent']}/agent.py",
                       OPP_TEAM_FILE=spec.get('opponentTeam', f"archive/{spec['opponent']}/team.json"))
        else:
            env['CUSTOM'] = spec['custom']
        with (folder / 'runner.log').open('w', encoding='utf-8') as log:
            subprocess.run(['node', 'tools/trace_matchup.js', str(spec['games'])], cwd=ROOT, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
    actual = load(report)
    assert actual['games'] == len(actual['results']) == 1
    assert actual['agentSha256'] == plan['sourceSha256'][spec['candidate']]
    assert actual['results'][0] == expected, (name, game, 'Historical outcome did not reproduce')
    trace = load(folder / 'traces' / f'game-{game}.json')
    changes = [dict(turn=x['observation']['turn'], own=x['observation'].get('my_active', {}).get('name'),
                    foe=x['observation'].get('foe', {}).get('name'), action=x['action'],
                    diagnostic=x['diagnostics']['mc'])
               for x in trace['decisions'] if (x.get('diagnostics', {}).get('mc') or {}).get('changed')]
    return dict(name=name, game=game, historicalOutcomeReproduced=True, winner=expected['winner'],
                turns=expected['turns'], finalHP=expected['finalHP'], monteCarloOverrides=changes)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=6) as pool:
        values = []
        for future in as_completed([pool.submit(run, pair) for pair in jobs]):
            value = future.result()
            values.append(value)
            print(json.dumps(value), flush=True)
    record = dict(purpose='Post-hoc development diagnoses; these replays are not new strength evidence.',
                  sourceSha256=plan['sourceSha256'], cases=sorted(values, key=lambda x: (x['name'], x['game'])),
                  instrumentSha256={name: sha(ROOT / 'tools' / name) for name in
                                    ('trace_matchup.js', 'trace_worker.py', 'diagnose_robust_rollout.py')})
    (OUT / 'summary.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
