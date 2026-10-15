"""Tests for bounded own-team continuation after a predicted faint."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate',ROOT/'research/v6-revenge-fast/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class RevengeTests(unittest.TestCase):
    def test_fainted_members_stay_charged_to_team_value(self):
        roster={name:agent.build_mon({'name':name},True) for name in ['Dragonite','Dragapult','Arcanine']}
        foe=agent.build_mon({'name':'Garchomp'})
        before=agent.team_value(roster,foe)
        roster['Dragonite']['hp']=0
        self.assertEqual(agent.team_value(roster,foe),before-200)
        roster['Dragapult']['hp']=0
        self.assertEqual(agent.team_value(roster,foe),before-400)

    def test_entry_uses_live_reserve_without_spending_an_attack(self):
        a=agent.build_mon({'name':'Dragonite','hp_percent':1},True)
        b=agent.build_mon({'name':'Arcanine'},True)
        dead=agent.build_mon({'name':'Dragapult','hp_percent':0},True)
        foe=agent.build_mon({'name':'Scizor','hp_percent':1})
        roster={p['key']:p for p in [a,b,dead]}
        entering=agent.revenge_entry(roster,foe,'',1)
        self.assertIs(entering,b)
        self.assertEqual((a['hp'],b['hp'],dead['hp'],foe['hp']),(1,100,0,1))
        self.assertEqual(foe['boosts'].get('atk'),-1)
        self.assertEqual(a['boosts'],{})

    def test_no_resurrection_after_team_faints(self):
        a=agent.build_mon({'name':'Dragonite','hp_percent':0},True)
        self.assertIsNone(agent.revenge_entry({a['key']:a},agent.build_mon({'name':'Garchomp'}),'',1))

if __name__=='__main__':unittest.main()
