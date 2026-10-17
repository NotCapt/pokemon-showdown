"""Small practical-margin and public switch-cycle guards around exact v4.7."""
_v47_choice = monte_carlo_choice
MC_MIN_MARGIN = 5.0


def monte_carlo_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches):
    command = _v47_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches)
    diagnostic = agent.mc_last or {}
    baseline = diagnostic.get('baseline', command)
    if command != baseline:
        index = diagnostic['actions'].index(command)
        margin = diagnostic['estimates'][index] - diagnostic['estimates'][0]
        diagnostic['margin'] = margin
        if margin < MC_MIN_MARGIN:
            command = baseline
            diagnostic['veto'] = 'small_practical_margin'
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
