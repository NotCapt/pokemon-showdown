"""Bounded root-bandit Monte Carlo; injected into a standalone agent.

This is rollout search, not full information-set MCTS or a Nash solver.
Both players choose using public opponent views. The transition model retains
the selected base engine's approximations; no enemy reserve is invented.
"""
import random

MC_ROLLOUTS = 96
MC_HORIZON = 6


def mc_seed(turn_no, a, b):
    text = repr((turn_no, a['key'], b['key'], round(a['hp'], 2), round(b['hp'], 2),
                 sorted(a['boosts'].items()), sorted(b['boosts'].items()), a['status'], b['status']))
    seed = 2166136261
    for char in text:
        seed = ((seed ^ ord(char)) * 16777619) & 0xffffffff
    return seed


def mc_public(mon):
    # Do not let a rollout policy condition on the other player's sampled set.
    view = build_mon(dict(name=mon['name'], hp_percent=mon['hp'],
                          types=mon['types'], status=mon['status'], boosts=mon['boosts']))
    return view


def mc_hypothesis(foe, observed, rng):
    priors = MC_PRIORS.get(foe['key'], [])
    config = rng.choice(priors) if priors and rng.random() < .5 else {}
    # Explicit public fields take precedence over our sampled hidden prior.
    raw = dict(config)
    raw.update(observed)
    mon = build_mon(raw)
    if config.get('moves'):
        mon['moves'] = [ident(m) for m in config['moves']]
    mon['boosts'] = dict(foe['boosts'])
    return mon


def mc_move_scores(mon, target, weather):
    if mon.get('phantom_charging'):
        return [(DATA['moves']['phantomforce'], 100.)]
    choices = moves_for(mon)
    if mon.get('locked') in DATA['moves']:
        choices = [DATA['moves'][mon['locked']]]
    scored = []
    incoming = damage(target, mon, best_attack(target, mon, weather), weather)
    for move in choices:
        mid = move['id']
        if move.get('category') != 'Status':
            d = damage(mon, target, move, weather)
            first = move.get('priority', 0) > 0 or (move.get('priority', 0) == 0 and stat(mon, 'spe', weather) > stat(target, 'spe', weather))
            score = accuracy(move) * (min(d, target['hp']) + (55 if first else 25) * (d >= target['hp']))
            if mid in ('phantomforce', 'bounce', 'solarbeam', 'gigaimpact'):
                score *= .65
            if move.get('recoil'):
                score -= min(d, target['hp']) * .2
            if mid == 'suckerpunch' and target['status'] == 'slp':
                score *= .3
        elif move.get('heal') or mid == 'rest':
            healing = min(100 - mon['hp'], 100 if mid == 'rest' else 50)
            score = healing * .8 - incoming * .35 - (14 if mid == 'rest' else 0)
            if mon['hp'] >= 85:
                score = -100
        elif move.get('boosts') and move.get('target') == 'self':
            gains = sum(max(0, min(v, 6 - mon['boosts'].get(k, 0))) for k, v in move['boosts'].items())
            score = 13 * gains - incoming * .65
            if mon['hp'] <= incoming or not gains:
                score = -100
        elif move.get('status'):
            score = 20 * accuracy(move) if not target['status'] else -100
        elif mid == 'leechseed':
            score = 16 if not target['seed'] and 'Grass' not in target['types'] else -100
        else:
            score = -100
        scored.append((move, score))
    return scored or [({'id': 'splash', 'category': 'Status', 'base_power': 0}, -100.)]


def mc_policy(mon, opponent, weather, rng):
    # A simulated player sees its own set and only a public view of the other.
    scored = mc_move_scores(mon, mc_public(opponent), weather)
    scored.sort(key=lambda pair: pair[1], reverse=True)
    if rng.random() < .85 or len(scored) == 1:
        return scored[0][0]
    choices = scored[:3]
    weights = [math.exp(max(-20., (score - choices[0][1]) / 18.)) for _, score in choices]
    return rng.choices([move for move, _ in choices], weights=weights, k=1)[0]


def mc_turn(a, b, ma, mb, weather, rng):
    # Simultaneous choices precede all hit, speed-tie, damage and flinch rolls.
    a['using_status'] = ma.get('category') == 'Status'
    b['using_status'] = mb.get('category') == 'Status'
    a['acted'] = b['acted'] = False
    pa, pb = ma.get('priority', 0), mb.get('priority', 0)
    sa, sb = stat(a, 'spe', weather), stat(b, 'spe', weather)
    first = pa > pb or (pa == pb and (sa > sb or (sa == sb and rng.random() < .5)))
    order = ((a, b, ma), (b, a, mb)) if first else ((b, a, mb), (a, b, ma))
    flinched = False
    for i, (p, q, move) in enumerate(order):
        if p['hp'] <= 0 or q['hp'] <= 0 or (i == 1 and flinched):
            continue
        p['acted'] = True
        if p['status'] == 'par' and rng.random() < .25:
            continue
        sampled = dict(move, _hit=rng.random() < accuracy(move))
        before = q['hp']
        apply_move(p, q, sampled, weather, (.85 + rng.randrange(16) / 100))
        if i == 0 and q['hp'] < before:
            flinched = rng.random() < flinch_chance(p, move, q)
    end_turn(a, b, weather)


def mc_roster(observation, active, switches):
    roster = {}
    for raw in observation.get('my_team') or [observation.get('my_active') or {}] + switches:
        mon = build_mon(raw, True)
        if mon['key']:
            if raw.get('fainted'):
                mon['hp'] = 0
            roster[mon['key']] = mon
    roster[active['key']] = clone_mon(active)
    return roster


def mc_enter(roster, active, target, foe, entry_loss):
    outgoing = roster[active['key']]
    outgoing['boosts'] = {}
    outgoing.pop('locked', None)
    outgoing.pop('phantom_charging', None)
    outgoing.pop('phantom_hidden', None)
    if outgoing['key'] in OWN:
        outgoing['moves'] = [ident(m) for m in OWN[outgoing['key']]['moves']]
    entering = roster[target['key']]
    entering['boosts'] = {}
    entering.pop('locked', None)
    entering['hp'] = max(0, entering['hp'] - entry_loss(entering))
    if entering['hp'] > 0:
        enter_intimidate(entering, foe)
    return entering


def mc_replacement(roster, active, foe, weather, entry_loss):
    living = [p for p in roster.values() if p['hp'] > 0 and p['key'] != active['key']]
    if not living:
        return active
    public = mc_public(foe)
    def utility(p):
        return p['hp'] - entry_loss(p) + damage(p, public, best_attack(p, public, weather), weather) - damage(public, p, best_attack(public, p, weather), weather)
    return mc_enter(roster, active, max(living, key=utility), foe, entry_loss)


def mc_rollout(action, a, b, weather, turn_no, observation, roster, entry_loss, seed):
    rng = random.Random(seed)
    team = {key: clone_mon(p) for key, p in roster.items()}
    x = team[a['key']]
    y = mc_hypothesis(b, observation.get('foe') or {}, rng)
    initial_hp = sum(p['hp'] for p in team.values())
    initial_alive = sum(p['hp'] > 0 for p in team.values())
    initial_value = value(x, y)
    enemy_initial_hp = y['hp']
    root_switch_faint = False
    switched_hp = 0
    command, move, switch = action
    for ply in range(min(MC_HORIZON, 101 - turn_no)):
        if x['hp'] <= 0:
            x = mc_replacement(team, x, y, weather, entry_loss)
        if x['hp'] <= 0 or y['hp'] <= 0:
            break
        if ply == 0:
            own_move = move
        else:
            own_move = mc_policy(x, y, weather, rng)
        # Enemy policy cannot see our simultaneous selected move or switch.
        enemy_move = mc_policy(y, x, weather, rng)
        if ply == 0 and switch:
            target = build_mon(switch, True)
            if target['key'] not in team:
                team[target['key']] = target
            switched_hp = team[target['key']]['hp']
            x = mc_enter(team, x, target, y, entry_loss)
            x['using_status'] = True
            x['acted'] = False
            if x['hp'] > 0:
                sampled = dict(enemy_move, _hit=rng.random() < accuracy(enemy_move))
                apply_move(y, x, sampled, weather, .85 + rng.randrange(16) / 100)
            end_turn(x, y, weather)
            root_switch_faint = x['hp'] <= 0
        else:
            mc_turn(x, y, own_move, enemy_move, weather, rng)
    hp_gain = sum(p['hp'] for p in team.values()) - initial_hp - (y['hp'] - enemy_initial_hp)
    faint_gain = int(y['hp'] <= 0) - (initial_alive - sum(p['hp'] > 0 for p in team.values()))
    score = hp_gain + 100 * faint_gain + .12 * (value(x, y) - initial_value)
    if switch:
        score -= 9
        if root_switch_faint:
            score -= .5 * switched_hp
    return score


def monte_carlo_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches):
    ranked = sorted(scored, key=lambda pair: pair[0], reverse=True)
    baseline = ranked[0][1]
    agent.mc_last = dict(rollouts=0, changed=False, baseline=baseline)
    # Preserve forced-entry and exact capped-HP handling from the base engine.
    if observation.get('force_switch') or turn_no >= 98 or len(ranked) < 2:
        return baseline
    choices = {command: (command, move, switch) for command, move, switch in actions}
    def safe_override(command):
        switch = choices[command][2]
        if command == baseline or not switch:
            return True
        entrant = build_mon(switch, True)
        entrant['hp'] = max(0, entrant['hp'] - agent.entry_loss(entrant))
        if entrant['hp'] <= 0:
            return False
        if entrant['hp'] <= 25:
            return True  # Keep deliberate weak-reserve sacrifices available.
        foe = clone_mon(b)
        enter_intimidate(entrant, foe)
        replies = moves_for(foe, True)
        replies.sort(key=lambda m: damage(foe, entrant, m, weather) * accuracy(m), reverse=True)
        # Monte Carlo averages must not bypass the established reserve guard.
        return not any(damage(foe, entrant, move, weather, 1.) >= entrant['hp'] for move in replies[:3])
    arms = [(score, command) for score, command in ranked[:3]
            if score >= ranked[0][0] - 20 and safe_override(command)]
    if len(arms) < 2:
        return baseline
    roster = mc_roster(observation, a, switches)
    seed = mc_seed(turn_no, a, b)
    samples = [[] for _ in arms]
    for trial in range(MC_ROLLOUTS):
        if trial < 12 * len(arms):
            arm = trial % len(arms)
        else:
            def ucb(i):
                values = samples[i]
                return sum(values) / len(values) / 300 + .4 * math.sqrt(math.log(trial + 1) / len(values))
            arm = max(range(len(arms)), key=ucb)
        # The nth sample of each arm shares its seed, reducing comparison noise.
        scenario_seed = (seed + 104729 * len(samples[arm])) & 0xffffffff
        samples[arm].append(mc_rollout(choices[arms[arm][1]], a, b, weather, turn_no,
                                       observation, roster, agent.entry_loss, scenario_seed))
    estimates = [.65 * prior + .35 * sum(values) / len(values) for (prior, _), values in zip(arms, samples)]
    winner = max(range(len(arms)), key=lambda i: estimates[i])
    selected = baseline
    if winner:
        n = min(len(samples[0]), len(samples[winner]))
        differences = [samples[winner][j] - samples[0][j] for j in range(n)]
        mean = sum(differences) / n
        se = math.sqrt(sum((v - mean) ** 2 for v in differences) / max(1, n - 1) / n)
        if mean > se + 2:
            selected = arms[winner][1]
    agent.mc_last = dict(rollouts=MC_ROLLOUTS, changed=selected != baseline, baseline=baseline,
                         actions=[command for _, command in arms], samples=[len(v) for v in samples],
                         estimates=estimates)
    return selected
