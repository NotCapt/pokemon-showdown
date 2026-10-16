"""Mechanics, information isolation, reproducibility and controlled runtime."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import statistics
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/monte-carlo-v1'
digest = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()
modules = {}
for label in ('control', 'phased', 'mc', 'phased_mc'):
    spec = importlib.util.spec_from_file_location(label, OUT / 'candidates' / label / 'agent.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    modules[label] = m

properties = {}
for label in ('mc', 'phased_mc'):
    m = modules[label]
    before = digest(m.DATA)
    foe = m.build_mon(dict(name='Garchomp', hp_percent=70))
    hidden = m.clone_mon(foe)
    hidden.update(item='choicescarf', ability='sandveil', moves=['swordsdance'])
    hidden['stats'] = {k: v * 3 for k, v in hidden['stats'].items()}
    own = m.build_mon(dict(name='Dragapult'), True)
    assert m.mc_public(foe) == m.mc_public(hidden)
    for seed in range(40):
        assert m.mc_policy(own, foe, '', random.Random(seed)) == m.mc_policy(own, hidden, '', random.Random(seed))
    assert digest(m.DATA) == before
    sets = sum(len(v) for v in m.MC_PRIORS.values())
    assert sets == 38
    options = json.loads((ROOT / 'research/options.json').read_text())
    for configs in m.MC_PRIORS.values():
        for config in configs:
            legal = options['pokemon'][config['name']]
            assert config['nature'] in options['natures'] and config['evs'] in options['evPresets']
            assert config['item'] in options['items'] and config['ability'] in legal['abilities']
            assert all(move in legal['legalMoves'] for move in config['moves'])
    first_wins = 0
    for seed in range(200):
        a = m.build_mon(dict(name='Dragapult', item='', hp_percent=1))
        b = m.clone_mon(a)
        m.mc_turn(a, b, m.DATA['moves']['shadowball'], m.DATA['moves']['shadowball'], '', random.Random(seed))
        first_wins += a['hp'] > 0
    assert 65 < first_wins < 135, first_wins
    p = m.PokemonAgent()
    p.mc_last = {'stale': True}
    assert p.decide(dict(team_preview=True)) == 'team 123' and p.mc_last is None
    properties[label] = dict(publicOpponentPolicyIsolated=True, staticDataUnchanged=True,
                             validHiddenPresets=sets, speedTieOwnSurvivors=first_wins,
                             previewResetsDiagnostics=True)

rng = random.Random(1729123)
workloads = []
m = modules['control']
team = list(m.OWN.values())
for i in range(96):
    active = team[i % 3]
    enemy = list(m.DATA['species'].values())[(i // 3) % 24]
    members = [dict(name=p['name'], hp_percent=rng.choice([15, 45, 75, 100]), active=p is active, fainted=False) for p in team]
    workloads.append(dict(turn=[1, 5, 20, 97, 99, 100][i % 6], team_preview=False, force_switch=i % 17 == 0,
                          weather='', my_active=dict(members[i % 3], boosts={}), my_team=members,
                          foe=dict(name=enemy['name'], types=enemy['types'], hp_percent=rng.choice([25, 60, 100])),
                          valid_moves=[dict(index=j + 1, id=m.ident(move), pp=16, disabled=False) for j, move in enumerate(active['moves'])],
                          valid_switches=[dict(p, index=j + 1) for j, p in enumerate(members) if not p['active']]))

timings = {label: [] for label in modules}
changed = {label: 0 for label in properties}
active_searches = {label: 0 for label in properties}
for repeat in range(2):
    for request in workloads:
        actions = {}
        labels = list(modules)
        rng.shuffle(labels)
        for label in labels:
            m = modules[label]
            o = copy.deepcopy(request)
            before = digest(o)
            p = m.PokemonAgent()
            start = time.perf_counter()
            action = p.decide(o)
            timings[label].append((time.perf_counter() - start) * 1000)
            assert digest(o) == before
            legal = {f"switch {v['index']}" for v in o['valid_switches']}
            if not o['force_switch']:
                legal |= {f"move {v['index']}" for v in o['valid_moves']}
            assert action in legal, (label, action)
            actions[label] = action
            if label in properties:
                diagnostic = p.mc_last or {}
                assert diagnostic.get('rollouts', 0) in (0, m.MC_ROLLOUTS)
                if diagnostic.get('rollouts'):
                    assert sum(diagnostic['samples']) == m.MC_ROLLOUTS
                    active_searches[label] += repeat == 0
                    changed[label] += repeat == 0 and diagnostic['changed']
                if o['turn'] >= 98 or o['force_switch']:
                    assert diagnostic.get('rollouts', 0) == 0
                if repeat == 0:
                    again = m.PokemonAgent()
                    assert again.decide(copy.deepcopy(request)) == action
                    assert again.mc_last == p.mc_last
for label in properties:
    assert active_searches[label] > 0, label
    properties[label].update(deterministicGivenPublicObservation=True, fixedRolloutBudget=True,
                              cappedEndgamesAndForcedEntriesPreserved=True, sampledPositions=active_searches[label],
                              changedChoices=changed[label], testedPositions=len(workloads))
stats = {label: dict(medianMs=statistics.median(v), p95Ms=sorted(v)[int(.95 * len(v))], maxMs=max(v), decisions=len(v)) for label, v in timings.items()}
result = dict(passed=True, properties=properties, latency=stats, timingMethod='Same 96 public synthetic observations; two randomly interleaved repetitions, no battle workers. Import/init/copy excluded; not strength evidence.',
              sourceSha256={label: hashlib.sha256((OUT / 'candidates' / label / 'agent.py').read_bytes()).hexdigest() for label in modules})
(OUT / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
