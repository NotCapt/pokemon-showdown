"""Policy fixtures from public observations and a nondefault Choice move."""
import importlib.util
import json
import os
from pathlib import Path
import random
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
agent=load(os.environ.get('AGENT_FILE','submission/agent.py'),'candidate')
old=load('archive/v4_2/agent.py','reference')

class PolicyTests(unittest.TestCase):
    # These archived positions encode the original Specs Dragapult team.
    # Hold that team fixed when testing policy mechanics across new releases.
    @patch.object(agent,'OWN',old.OWN)
    def test_preserves_full_health_dragapult_in_saved_loss(self):
        fixture=json.loads((ROOT/'research/c-switch-fixture.json').read_text())
        candidate=agent.PokemonAgent();reference=old.PokemonAgent()
        for obs in fixture['observations']:
            actual=candidate.decide(obs);previous=reference.decide(obs)
        self.assertEqual(previous,fixture['reference'])
        self.assertEqual(actual,fixture['expected'])

    def test_choice_lock_can_use_coverage_absent_from_default_set(self):
        a=agent.build_mon({'name':'Metagross','item':'Choice Band'})
        b=agent.build_mon({'name':'Blastoise'})
        self.assertNotIn('thunderpunch',a['moves'])
        agent.apply_move(a,b,agent.DATA['moves']['thunderpunch'],'',.925)
        c=agent.build_mon({'name':'Garchomp'})
        self.assertEqual(agent.best_attack(a,c,'')['id'],'thunderpunch')
        self.assertEqual(agent.damage(a,c,agent.best_attack(a,c,'')),0)
        self.assertNotIn('locked',agent.build_mon({'name':'Metagross','item':'Choice Band'}))

    @patch.object(agent,'OWN',old.OWN)
    def test_weak_reserve_sacrifice_stays_available(self):
        moves=[dict(agent.DATA['moves'][m],index=i+1) for i,m in enumerate(('flareblitz','extremespeed','crunch','playrough'))]
        obs=dict(turn=97,my_active=dict(name='Arcanine',hp_percent=66),
                 foe=dict(name='Snorlax',hp_percent=68),valid_moves=moves,
                 valid_switches=[dict(name='Dragonite',hp_percent=6,index=1),dict(name='Dragapult',hp_percent=10,index=2)])
        self.assertEqual(agent.PokemonAgent().decide(obs),'switch 1')

    @patch.object(agent,'OWN',old.OWN)
    def test_last_turn_actions_preserve_hp_objective(self):
        rng=random.Random(11747)
        own=list(agent.OWN.values());names=list(agent.DATA['species'])
        for i in range(24):
            p=own[i%3]
            obs=dict(turn=100,my_active=dict(name=p['name'],hp_percent=rng.randrange(1,101)),
                     foe=dict(name=rng.choice(names),hp_percent=rng.randrange(1,101)),
                     valid_moves=[dict(agent.DATA['moves'][agent.ident(m)],index=j+1) for j,m in enumerate(p['moves'])],
                     valid_switches=[dict(name=q['name'],hp_percent=rng.randrange(1,101),index=j+1) for j,q in enumerate(own) if p!=q])
            self.assertEqual(agent.PokemonAgent().decide(obs),old.PokemonAgent().decide(obs))

if __name__=='__main__':unittest.main()
