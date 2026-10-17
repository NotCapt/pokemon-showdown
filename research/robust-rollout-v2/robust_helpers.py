"""Public-history, finite-PP and conservative Monte Carlo continuations."""
_plain_clone = clone_mon
_plain_moves = moves_for
_temporal_apply = apply_move
_plain_mc_scores = mc_move_scores
_plain_best_attack = best_attack


def clone_mon(mon):
    result = _plain_clone(mon)
    if 'pp' in mon:
        result['pp'] = dict(mon['pp'])
    return result


def moves_for(mon, coverage=False):
    choices = _plain_moves(mon, coverage)
    if 'pp' not in mon:
        return choices
    available = [m for m in choices if mon['pp'].get(m['id'], 1) > 0]
    return available or [dict(id='struggle', type='???', category='Physical', base_power=50,
                              accuracy=True, priority=0, target='normal')]


def best_attack(a, b, weather):
    if a.get('locked') and a.get('pp', {}).get(a['locked']) == 0 and not a.get('phantom_charging'):
        a = clone_mon(a)
        a.pop('locked', None)
    return _plain_best_attack(a, b, weather)


def apply_move(a, b, move, weather, roll):
    sleeping = a['status'] == 'slp' and move.get('id') != 'sleeptalk'
    wakes = sleeping and (a.get('rest_sleep') == 0 or ('rest_sleep' not in a and a.get('sleep', 0) >= 1))
    acts = a['hp'] > 0 and a['status'] != 'frz' and (not sleeping or wakes)
    charging = a.get('phantom_charging')
    before = b['hp']
    _temporal_apply(a, b, move, weather, roll)
    mid = move.get('id')
    if acts and not charging and mid in a.get('pp', {}):
        a['pp'][mid] = max(0, a['pp'][mid] - 1)
    if acts and mid == 'struggle' and b['hp'] < before:
        a['hp'] = max(0, a['hp'] - 25)


def observe_public(agent, a, b, observation, turn_no):
    memory = agent.public_state
    for key, default in (('pp', {}), ('rest', {}), ('seen', {})):
        memory.setdefault(key, default)
    pp = memory['pp'].setdefault(a['key'], {ident(m): PP_MAX.get(ident(m), 16)
                                          for m in OWN.get(a['key'], {}).get('moves', [])})
    shown = {ident(m.get('id') or m.get('name')): m['pp'] for m in observation.get('valid_moves', []) if 'pp' in m}
    pp.update(shown)
    previous = memory.get('action')
    if previous and previous['turn'] < turn_no and memory.get('processed') != (turn_no, a['key']):
        if previous['key'] == a['key']:
            mid = previous['move']
            if mid and previous['pp'] == 1 and mid not in shown:
                pp[mid] = 0  # Last known PP is now unavailable; never invent more.
            if (mid == 'rest' and previous['pp'] is not None and shown.get('rest') == previous['pp'] - 1
                    and a['status'] == 'slp'):
                memory['rest'][a['key']] = 2
            elif previous['sleeping'] and mid and a['key'] in memory['rest']:
                memory['rest'][a['key']] = max(0, memory['rest'][a['key']] - 1)
        memory['processed'] = (turn_no, a['key'])
    if a['status'] != 'slp':
        memory['rest'].pop(a['key'], None)
    elif a['key'] in memory['rest']:
        a['rest_sleep'] = memory['rest'][a['key']]
    a['pp'] = dict(pp)
    raw = observation.get('foe') or {}
    if b['key'] and raw.get('hp_percent') is not None:
        public = {key: raw[key] for key in ('name', 'species', 'types', 'hp_percent', 'status', 'boosts') if key in raw}
        public['types'] = list(b['types'])
        if 'boosts' in public:
            public['boosts'] = dict(public['boosts'])
        memory['seen'][b['key']] = public


def remember_action(agent, command, a, actions, turn_no):
    move = next((m for cmd, m, _ in actions if cmd == command), None)
    mid = move.get('id') if move else None
    agent.public_state['action'] = dict(turn=turn_no, key=a['key'], move=mid,
                                       pp=a.get('pp', {}).get(mid), sleeping=a['status'] == 'slp')


def mc_hypothesis(foe, observed, rng):
    group = rng.randrange(3)
    choices = MC_PRIORS.get(foe['key'], []) if group == 1 else MC_GENERIC.get(foe['key'], []) if group == 2 else []
    config = rng.choice(choices) if choices else MC_DEFAULTS.get(foe['key'], {})
    raw = dict(config)
    raw.update(observed)
    mon = build_mon(raw)
    mon['moves'] = [ident(m) for m in raw.get('moves', config.get('moves', [])) if isinstance(m, str)] or mon['moves']
    mon['boosts'] = dict(foe['boosts'])
    return mon


def mc_roster(observation, active, switches):
    roster = {}
    ledger = observation.get('_public_pp', {})
    rests = observation.get('_public_rest', {})
    for raw in observation.get('my_team') or [observation.get('my_active') or {}] + switches:
        mon = build_mon(raw, True)
        if not mon['key']:
            continue
        mon['pp'] = dict(ledger.get(mon['key'], {ident(m): PP_MAX.get(ident(m), 16)
                                                for m in OWN.get(mon['key'], {}).get('moves', [])}))
        if mon['key'] in rests:
            mon['status'] = 'slp'
            mon['rest_sleep'] = rests[mon['key']]
        if raw.get('fainted'):
            mon['hp'] = 0
        roster[mon['key']] = mon
    roster[active['key']] = clone_mon(active)
    return roster


def mc_enter(roster, active, target, foe, entry_loss):
    outgoing = roster[active['key']]
    outgoing['boosts'] = {}
    for key in ('locked', 'phantom_charging', 'phantom_hidden'):
        outgoing.pop(key, None)
    if outgoing['key'] in OWN and 'pp' in outgoing:
        outgoing['moves'] = [ident(m) for m in OWN[outgoing['key']]['moves']]
    entering = roster[target['key']]
    entering['boosts'] = {}
    entering.pop('locked', None)
    entering['hp'] = max(0, entering['hp'] - entry_loss(entering))
    if entering['hp'] > 0:
        enter_intimidate(entering, foe)
    return entering


def mc_move_scores(mon, target, weather):
    if mon.get('phantom_charging'):
        return [(DATA['moves']['phantomforce'], 100.)]
    scores = _plain_mc_scores(mon, target, weather)
    if 'pp' in mon:
        scores = [(m, score) for m, score in scores if mon['pp'].get(m['id'], 1) > 0]
    return scores or [(moves_for(mon)[0], 0.)]


def rollout_action(mon, foe, roster, weather, rng, can_switch):
    # Own configuration is known; opponent configuration is reconstructed publicly.
    public = mc_public(foe)
    selected = mc_policy(mon, foe, weather, rng)
    if not can_switch:
        return selected, None
    def utility(p, entering=False):
        incoming = damage(public, p, best_attack(public, p, weather), weather)
        score = max(s for _, s in mc_move_scores(p, public, weather)) - .65 * min(incoming, p['hp'])
        if incoming >= p['hp']:
            score -= 65
        return score - (22 if entering else 0)
    best = utility(mon)
    target = None
    for p in roster.values():
        if p['hp'] <= 0 or p['key'] == mon['key']:
            continue
        fresh = clone_mon(p)
        fresh['boosts'] = {}
        score = utility(fresh, True)
        if score > best:
            best, target = score, p
    return (None, target) if target else (selected, None)


def mc_rollout(action, a, b, weather, turn_no, observation, roster, entry_loss, seed):
    rng = random.Random(seed)
    team = {key: clone_mon(p) for key, p in roster.items()}
    x = team[a['key']]
    y = mc_hypothesis(b, observation.get('foe') or {}, rng)
    enemies = {y['key']: y}
    if SWITCH_AWARE:
        for key, raw in observation.get('_public_seen', {}).items():
            # Previously seen species may have switched out or fainted. Sample
            # availability; never treat this stale public HP as hidden true state.
            if key != y['key'] and raw.get('hp_percent', 0) > 0 and rng.random() < .65:
                enemies[key] = mc_hypothesis(build_mon(raw), raw, rng)
    own_hp = sum(p['hp'] for p in team.values())
    enemy_hp = sum(p['hp'] for p in enemies.values())
    own_alive = sum(p['hp'] > 0 for p in team.values())
    enemy_alive = len(enemies)
    initial_value = value(x, y)
    root_switch_faint = False
    switched_hp = 0
    own_last_switch = enemy_last_switch = -3
    command, root_move, root_switch = action
    # An early active-foe KO does not reveal that its hidden bench is empty.
    # Keep the terminal HP objective whenever this horizon reaches the cap.
    capped = turn_no + MC_HORIZON >= 101
    for ply in range(min(MC_HORIZON, 101 - turn_no)):
        if x['hp'] <= 0:
            x = mc_replacement(team, x, y, weather, entry_loss)
        if y['hp'] <= 0:
            y = mc_replacement(enemies, y, x, weather, lambda _: 0.)
        if x['hp'] <= 0 or y['hp'] <= 0:
            break
        if ply == 0:
            own_move, own_switch = root_move, team.get(ident(root_switch.get('species') or root_switch.get('name', ''))) if root_switch else None
        else:
            own_move, own_switch = rollout_action(x, y, team, weather, rng, SWITCH_AWARE and ply-own_last_switch >= 3)
        # Both choices precede reveal; the enemy never sees our selected action.
        enemy_move, enemy_switch = rollout_action(y, x, enemies, weather, rng, SWITCH_AWARE and ply-enemy_last_switch >= 3)
        switched_own = own_switch is not None
        switched_enemy = enemy_switch is not None
        if switched_own:
            if ply == 0:
                switched_hp = own_switch['hp']
            x = mc_enter(team, x, own_switch, y, entry_loss)
            own_last_switch = ply
        if switched_enemy:
            y = mc_enter(enemies, y, enemy_switch, x, lambda _: 0.)
            enemy_last_switch = ply
        if switched_own or switched_enemy:
            x['using_status'] = switched_own or (own_move or {}).get('category') == 'Status'
            y['using_status'] = switched_enemy or (enemy_move or {}).get('category') == 'Status'
            x['acted'] = y['acted'] = False
            if x['hp'] > 0 and y['hp'] > 0:
                if not switched_own:
                    apply_move(x, y, dict(own_move, _hit=rng.random() < accuracy(own_move)), weather, .85+rng.randrange(16)/100)
                if not switched_enemy and y['hp'] > 0 and x['hp'] > 0:
                    apply_move(y, x, dict(enemy_move, _hit=rng.random() < accuracy(enemy_move)), weather, .85+rng.randrange(16)/100)
            end_turn(x, y, weather)
            if ply == 0 and switched_own:
                root_switch_faint = x['hp'] <= 0
        else:
            mc_turn(x, y, own_move, enemy_move, weather, rng)
    hp_gain = sum(p['hp'] for p in team.values())-own_hp - (sum(p['hp'] for p in enemies.values())-enemy_hp)
    faint_gain = enemy_alive-sum(p['hp'] > 0 for p in enemies.values()) - (own_alive-sum(p['hp'] > 0 for p in team.values()))
    # At the cap only summed HP counts; living-count and boost bonuses disappear.
    score = hp_gain if capped else hp_gain + 100*faint_gain + .12*(value(x, y)-initial_value)
    if root_switch and not capped:
        score -= 9 + (.5*switched_hp if root_switch_faint else 0)
    return score


def monte_carlo_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches):
    ranked = sorted(scored, key=lambda pair: pair[0], reverse=True)
    baseline = ranked[0][1]
    agent.mc_last = dict(rollouts=0, changed=False, baseline=baseline)
    if observation.get('force_switch') or turn_no >= 100 or len(ranked) < 2:
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
            return True
        foe = clone_mon(b)
        enter_intimidate(entrant, foe)
        replies = moves_for(foe, True)
        replies.sort(key=lambda m: damage(foe, entrant, m, weather)*accuracy(m), reverse=True)
        return not any(damage(foe, entrant, m, weather, 1.) >= entrant['hp'] for m in replies[:3])
    arms = [(score, cmd) for score, cmd in ranked[:3] if score >= ranked[0][0]-20 and safe_override(cmd)]
    if len(arms) < 2:
        return baseline
    obs = dict(observation, _public_pp=agent.public_state.get('pp', {}),
               _public_rest=agent.public_state.get('rest', {}), _public_seen=agent.public_state.get('seen', {}))
    roster = mc_roster(obs, a, switches)
    seed = mc_seed(turn_no, a, b)
    samples = [[] for _ in arms]
    for trial in range(MC_ROLLOUTS):
        arm = trial % len(arms)
        scenario = (seed + 104729*len(samples[arm])) & 0xffffffff
        samples[arm].append(mc_rollout(choices[arms[arm][1]], a, b, weather, turn_no, obs, roster, agent.entry_loss, scenario))
    estimates = []
    for (prior, _), values in zip(arms, samples):
        tail = sorted(values)[:max(1, len(values)//4)]
        robust = .8*sum(values)/len(values) + .2*sum(tail)/len(tail)
        estimates.append(.65*prior + .35*robust)
    winner = max(range(len(arms)), key=lambda i: estimates[i])
    selected = baseline
    if winner:
        differences = [x-y for x, y in zip(samples[winner], samples[0])]
        mean = sum(differences)/len(differences)
        se = math.sqrt(sum((v-mean)**2 for v in differences)/max(1, len(differences)-1)/len(differences))
        if mean > se+2 and sum(v > 0 for v in differences) >= .55*len(differences):
            selected = arms[winner][1]
    agent.mc_last = dict(rollouts=MC_ROLLOUTS, changed=selected != baseline, baseline=baseline,
                         actions=[cmd for _, cmd in arms], samples=[len(v) for v in samples], estimates=estimates)
    return selected
