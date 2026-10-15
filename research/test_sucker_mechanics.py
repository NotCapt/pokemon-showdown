"""Independent move-execution fixtures for the Sucker Punch candidate."""
import importlib.util
from pathlib import Path
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate',root/'research/e-sucker/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class SuckerPunchTests(unittest.TestCase):
    def test_fails_after_higher_priority_attack(self):
        a=agent.build_mon({'name':'Dragonite','item':''})
        b=agent.build_mon({'name':'Dragapult','item':''})
        start=a['hp']
        agent.turn(a,b,dict(agent.DATA['moves']['extremespeed'],_hit=True),
                   dict(agent.DATA['moves']['suckerpunch'],_hit=True),'',.925)
        self.assertEqual(a['hp'],start)

    def test_hits_before_regular_attack(self):
        a=agent.build_mon({'name':'Dragonite','item':''})
        b=agent.build_mon({'name':'Dragapult','item':''})
        agent.turn(a,b,dict(agent.DATA['moves']['icepunch'],_hit=True),
                   dict(agent.DATA['moves']['suckerpunch'],_hit=True),'',.925)
        self.assertLess(a['hp'],100)

    def test_switch_is_not_an_attack(self):
        a=agent.build_mon({'name':'Dragonite','item':''})
        b=agent.build_mon({'name':'Dragapult','item':''})
        a['using_status']=True
        agent.apply_move(b,a,dict(agent.DATA['moves']['suckerpunch'],_hit=True),'',.925)
        self.assertEqual(a['hp'],100)

    def test_execution_flags_reset_next_turn(self):
        a=agent.build_mon({'name':'Dragonite','item':''})
        b=agent.build_mon({'name':'Dragapult','item':''})
        a['acted']=b['acted']=True
        agent.turn(a,b,dict(agent.DATA['moves']['icepunch'],_hit=True),
                   dict(agent.DATA['moves']['suckerpunch'],_hit=True),'',.925)
        self.assertLess(a['hp'],100)

if __name__=='__main__':unittest.main()
