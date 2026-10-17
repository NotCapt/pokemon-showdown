"""Targeted recovery-override and public switch-cycle guards around exact v4.7."""
_v47_choice = monte_carlo_choice


def monte_carlo_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches):
    command = _v47_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches)
    diagnostic = agent.mc_last or {}
    baseline = diagnostic.get('baseline', command)
    if command != baseline:
        selected_move = next(m for cmd, m, _ in actions if cmd == command)
        baseline_move = next(m for cmd, m, _ in actions if cmd == baseline)
        if selected_move and (selected_move.get('heal') or selected_move.get('id') == 'rest'):
            premature_rest = selected_move.get('id') == 'rest' and (a['hp'] > 65 or baseline.startswith('switch '))
            finishing_attack = (baseline_move and baseline_move.get('category') != 'Status'
                                and damage(a, b, baseline_move, weather, .85) >= 1.25*b['hp'])
            if premature_rest or finishing_attack:
                command = baseline
                diagnostic['veto'] = 'premature_rest' if premature_rest else 'preserve_finishing_pressure'
    if CYCLE_GUARD and command != baseline and command.startswith('switch ') and observation.get('my_team'):
        target = next(s for cmd, _, s in actions if cmd == command)
        signature = (a['key'], ident(target.get('species') or target.get('name', '')), b['key'])
        total = sum(float(p.get('hp_percent', 0) or 0) for p in observation['my_team'] if not p.get('fainted'))
        previous = agent.mc_cycles.get(signature)
        if (previous and 0 < turn_no-previous[0] <= 12 and b['hp'] >= previous[1]-2
                and total <= previous[2]+2):
            command = baseline
            diagnostic['veto'] = 'repeated_unproductive_switch'
        else:
            agent.mc_cycles[signature] = (turn_no, b['hp'], total)
    diagnostic['changed'] = command != baseline
    return command
