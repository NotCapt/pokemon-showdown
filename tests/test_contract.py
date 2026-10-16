"""The documented portal contract, independent of a particular move ranking."""
import importlib.util
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract_agent', ROOT / os.environ.get('AGENT_FILE', 'submission/agent.py'))
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


class ContractTests(unittest.TestCase):
    def observation(self, **extra):
        obs = dict(turn=50, my_active=dict(name='Dragapult', hp_percent=30),
                   foe=dict(name='Snorlax', hp_percent=70), valid_moves=[], valid_switches=[])
        obs.update(extra)
        return obs

    def test_documented_moves_need_no_pp_field(self):
        obs = self.observation(valid_moves=[dict(index=4, id='flamethrower', name='Flamethrower', type='Fire',
                                                category='Special', base_power=90, accuracy=100, disabled=False)])
        self.assertEqual(agent.PokemonAgent().decide(obs), 'move 4')

    def test_sparse_move_metadata_retains_original_slot(self):
        self.assertEqual(agent.PokemonAgent().decide(self.observation(valid_moves=[dict(index=3, id='flamethrower')])), 'move 3')

    def test_disabled_and_exhausted_moves_leave_a_legal_switch(self):
        obs = self.observation(valid_moves=[dict(index=1, id='dragondarts', pp=0),
                                           dict(index=4, id='uturn', pp=3, disabled=True)],
                               valid_switches=[dict(index=1, name='Snorlax', hp_percent=60)])
        self.assertEqual(agent.PokemonAgent().decide(obs), 'switch 1')

    def test_forced_switch_never_uses_an_available_move(self):
        obs = self.observation(force_switch=True, valid_moves=[dict(index=1, id='dragondarts')],
                               valid_switches=[dict(index=1, name='Snorlax', hp_percent=60)])
        self.assertEqual(agent.PokemonAgent().decide(obs), 'switch 1')

    def test_active_and_fainted_switch_targets_are_excluded(self):
        obs = self.observation(valid_moves=[dict(index=2, id='flamethrower')],
                               valid_switches=[dict(index=1, name='Snorlax', hp_percent=100, active=True),
                                               dict(index=3, name='Corviknight', hp_percent=0, fainted=True)])
        self.assertEqual(agent.PokemonAgent().decide(obs), 'move 2')

    def test_struggle_is_safe_even_without_an_embedded_move_definition(self):
        obs = self.observation(valid_moves=[dict(index=1, id='struggle', type='Normal', category='Physical',
                                                base_power=50, accuracy=True, pp=1)])
        self.assertEqual(agent.PokemonAgent().decide(obs), 'move 1')

    def test_only_capped_setup_still_returns_a_legal_action(self):
        obs = self.observation(my_active=dict(name='Corviknight', hp_percent=100, boosts=dict(def_=6, **{'def': 6})),
                               valid_moves=[dict(index=2, id='irondefense')])
        self.assertEqual(agent.PokemonAgent().decide(obs), 'move 2')

    def test_terminal_or_absent_observation_is_safe(self):
        self.assertEqual(agent.PokemonAgent().decide({}), 'pass')
        self.assertEqual(agent.PokemonAgent().decide(None), 'pass')


if __name__ == '__main__':
    unittest.main()
