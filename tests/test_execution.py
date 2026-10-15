"""Sucker Punch execution gates, also checked in the official simulator."""
import importlib.util
import os
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('execution_agent',ROOT/os.environ.get('AGENT_FILE','submission/agent.py'))
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class ExecutionTests(unittest.TestCase):
    def test_sucker_punch_fails_after_higher_priority_attack(self):
        a=agent.build_mon({'name':'Dragonite','item':''})
        b=agent.build_mon({'name':'Dragapult','item':''})
        agent.turn(a,b,dict(agent.DATA['moves']['extremespeed'],_hit=True),
                   dict(agent.DATA['moves']['suckerpunch'],_hit=True),'',.925)
        self.assertEqual(a['hp'],100)

    def test_sucker_punch_hits_before_regular_attack(self):
        a=agent.build_mon({'name':'Dragonite','item':''})
        b=agent.build_mon({'name':'Dragapult','item':''})
        agent.turn(a,b,dict(agent.DATA['moves']['icepunch'],_hit=True),
                   dict(agent.DATA['moves']['suckerpunch'],_hit=True),'',.925)
        self.assertLess(a['hp'],100)

    def test_sucker_punch_fails_on_switch(self):
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
