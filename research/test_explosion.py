"""Execution gates must prevent Explosion's self-KO when it never executes."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('agent',Path(__file__).with_name('v4_3-explosion-agent.py'))
agent=importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


class ExplosionTests(unittest.TestCase):
    def test_miss_still_faints(self):
        a=agent.build_mon({'name':'Metagross'})
        b=agent.build_mon({'name':'Blastoise'})
        agent.apply_move(a,b,dict(agent.DATA['moves']['explosion'],_hit=False),'',.925)
        self.assertEqual((a['hp'],b['hp']),(0,100))

    def test_sleep_and_freeze_prevent_execution(self):
        for status in ('slp','frz'):
            a=agent.build_mon({'name':'Metagross','status':status})
            b=agent.build_mon({'name':'Blastoise'})
            agent.apply_move(a,b,agent.DATA['moves']['explosion'],'',.925)
            self.assertEqual((a['hp'],b['hp']),(100,100))

    def test_flinch_prevents_explosion(self):
        a=agent.build_mon({'name':'Metagross'})
        b=agent.build_mon({'name':'Togekiss'})
        agent.turn(a,b,agent.DATA['moves']['explosion'],
                   dict(agent.DATA['moves']['airslash'],_hit=True,_flinch=True),'',.925)
        self.assertGreater(a['hp'],0)
        self.assertEqual(b['hp'],100)


if __name__ == '__main__':
    unittest.main()
