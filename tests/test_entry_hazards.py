"""Inference from public entry HP only; ambiguity and immunity must be kept."""
import importlib.util
import os
from pathlib import Path
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hazard_agent',root/os.environ.get('AGENT_FILE','submission/agent.py'))
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class HazardTests(unittest.TestCase):
    def mon(self,name,hp=100,**kw):return agent.build_mon(dict(name=name,hp_percent=hp,**kw),True)
    def enter(self,p,name,state,health=100):
        mon=self.mon(name);loss=agent.entry_damage(mon,state)
        p.forced_entry=(mon['key'],health,10)
        mon['hp']=max(0,health-loss);p.observe_entry(mon,11)
        return mon

    def test_unknown_field_has_no_invented_damage(self):
        self.assertEqual(agent.PokemonAgent().entry_loss(self.mon('Dragonite')),0)

    def test_flying_rock_entry_does_not_invent_spikes(self):
        p=agent.PokemonAgent();self.enter(p,'Dragonite',(True,3))
        self.assertTrue(all(rock for rock,layers in p.hazard_states))
        self.assertEqual(p.entry_loss(self.mon('Dragapult')),agent.entry_damage(self.mon('Dragapult'),(True,0)))

    def test_neutral_entry_retains_rock_spikes_ambiguity(self):
        p=agent.PokemonAgent();self.enter(p,'Dragapult',(True,0))
        self.assertIn((False,1),p.hazard_states)
        self.assertIn((True,0),p.hazard_states)
        self.assertEqual(p.entry_loss(self.mon('Dragonite')),0)

    def test_cleared_field_replaces_contradicted_estimate(self):
        p=agent.PokemonAgent();self.enter(p,'Dragonite',(True,0))
        self.enter(p,'Dragonite',(False,0))
        self.assertEqual(p.entry_loss(self.mon('Arcanine')),0)

    def test_immune_entry_cannot_prove_field_is_clear(self):
        p=agent.PokemonAgent();self.enter(p,'Dragonite',(True,0))
        mon=self.mon('Arcanine',item='Heavy-Duty Boots')
        p.forced_entry=(mon['key'],100,10);p.observe_entry(mon,11)
        self.assertGreater(p.entry_loss(self.mon('Arcanine')),0)
        self.assertEqual(p.entry_loss(mon),0)
        self.assertEqual(agent.entry_damage(self.mon('Alakazam',ability='Magic Guard'),(True,3)),0)

    def test_fainted_entry_is_censored_not_exact_damage(self):
        p=agent.PokemonAgent();self.enter(p,'Dragonite',(True,0),health=1)
        self.assertTrue(all(rock for rock,layers in p.hazard_states))
        self.assertGreater(p.entry_loss(self.mon('Dragonite')),20)

    def test_stale_or_different_entry_is_not_learned(self):
        p=agent.PokemonAgent();p.forced_entry=('dragonite',100,3)
        p.observe_entry(self.mon('Dragonite',50),20)
        self.assertIsNone(p.hazard_states)
        p.forced_entry=('dragonite',100,3);p.observe_entry(self.mon('Arcanine',50),4)
        self.assertIsNone(p.hazard_states)

    def test_missing_hp_does_not_create_a_field_observation(self):
        p=agent.PokemonAgent();p.forced_entry=('dragonite',100,10)
        p.decide(dict(turn=11,my_active={'name':'Dragonite'},foe={'name':'Snorlax','hp_percent':30},
                      valid_moves=[dict(agent.DATA['moves']['extremespeed'],index=1)]))
        self.assertIsNone(p.hazard_states)

    def test_living_pivot_is_not_a_clean_hazard_observation(self):
        p=agent.PokemonAgent()
        p.decide(dict(turn=10,force_switch=True,my_active=dict(name='Dragapult',hp_percent=50),
                      foe=dict(name='Snorlax',hp_percent=100),valid_moves=[],
                      valid_switches=[dict(name='Dragonite',hp_percent=100,index=1)]))
        self.assertIsNone(p.forced_entry)

    def test_avoids_known_lethal_rock_entry_in_saved_position(self):
        import json
        fixture=json.loads((root/'research/f-hazard-fixture.json').read_text())
        p=agent.PokemonAgent()
        mon=self.mon('Dragonite',fixture['priorPublicEntry']['afterHP'])
        p.forced_entry=('dragonite',100,89);p.observe_entry(mon,90);p.last_turn=98
        self.assertEqual(p.decide(fixture['observation']),fixture['candidate'])

    def test_fatal_entry_spends_residual_turn_only_on_voluntary_switch(self):
        original=agent.end_turn
        try:
            for forced in (False,True):
                recorded=[]
                def tracked(a,b,weather):
                    before=b['hp'];original(a,b,weather)
                    if a['key']=='arcanine' and a['hp']<=0:recorded.append(b['hp']-before)
                agent.end_turn=tracked
                p=agent.PokemonAgent();p.hazard_states=[(True,0)]
                p.decide(dict(turn=100,force_switch=forced,my_active=dict(name='Dragapult',hp_percent=80),
                              foe=dict(name='Snorlax',hp_percent=60),valid_moves=[dict(agent.DATA['moves']['shadowball'],index=1)],
                              valid_switches=[dict(name='Arcanine',hp_percent=24,index=3)]))
                if forced:self.assertFalse(recorded)
                else:
                    self.assertTrue(recorded)
                    self.assertTrue(all(x==6.25 for x in recorded))
        finally:agent.end_turn=original

if __name__=='__main__':unittest.main()
