"""Tests for bounded hidden-speed hypotheses; no enemy set is read."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate',ROOT/'research/v6-scarf/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class SpeedTests(unittest.TestCase):
    def test_only_adds_scarf_when_speed_order_can_change(self):
        foe=agent.build_mon({'name':'Garchomp'})
        slow=agent.build_mon({'name':'Dragonite'},True)
        fast=agent.build_mon({'name':'Dragapult'},True)
        self.assertEqual(len(agent.speed_cases(foe,{slow['key']:slow},'')),1)
        cases=agent.speed_cases(foe,{fast['key']:fast},'')
        self.assertEqual([p for _,p in cases],[.88,.12])
        self.assertLess(agent.stat(foe,'spe'),agent.stat(fast,'spe'))
        self.assertGreater(agent.stat(cases[1][0],'spe'),agent.stat(fast,'spe'))
        cases[1][0]['boosts']['atk']=5
        self.assertEqual(foe['boosts'],{})
        self.assertNotEqual(foe['item'],'choicescarf')

    def test_known_item_and_existing_scarf_are_not_duplicated(self):
        foe=agent.build_mon({'name':'Garchomp'})
        own=agent.build_mon({'name':'Dragapult'},True)
        roster={own['key']:own}
        self.assertEqual(len(agent.speed_cases(foe,roster,'',True)),1)
        foe['item']='choicescarf'
        self.assertEqual(len(agent.speed_cases(foe,roster,'')),1)
        own['hp']=0;foe['item']='lifeorb'
        self.assertEqual(len(agent.speed_cases(foe,roster,'')),1)

if __name__=='__main__':unittest.main()
