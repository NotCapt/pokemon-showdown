"""Set coherence and priority coverage, without privileged opponent details."""
import importlib.util
import os
from pathlib import Path
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('priority_agent',root/os.environ.get('AGENT_FILE','research/f-final/agent.py'))
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class PriorityPriorTests(unittest.TestCase):
    def threats(self,raw=None):
        raw=raw or {'name':'Lapras','hp_percent':44}
        own=agent.build_mon({'name':'Dragonite','hp_percent':58.5},True)
        foe=agent.build_mon(raw)
        return agent.enemy_threats(own,foe,'',{'foe':raw}),foe

    def test_includes_priority_even_below_three_largest_damage_moves(self):
        threats,foe=self.threats()
        normal=[m['id'] for m,model,w in threats if model is foe]
        self.assertIn('iceshard',normal)
        self.assertLessEqual(len(normal),7)

    def test_alternate_is_coherent_legal_set_with_fixed_mass(self):
        threats,foe=self.threats()
        alternatives=[(m,model,w) for m,model,w in threats if model is not foe]
        self.assertEqual(len(alternatives),1)
        move,model,mass=alternatives[0]
        self.assertEqual((move['id'],mass),('iceshard',.2))
        self.assertGreater(model['stats']['atk'],foe['stats']['atk'])
        self.assertEqual(len(set(model['moves'])),4)
        self.assertIn('iceshard',model['moves'])
        legal={agent.ident(m) for m in agent.DATA['species']['lapras']['legalMoves']}
        self.assertTrue(set(model['moves'])<=legal)
        self.assertAlmostEqual(sum(w for m,p,w in threats),1)
        self.assertEqual(model['hp'],foe['hp'])
        self.assertEqual(model['boosts'],foe['boosts'])

    def test_explicit_stats_nature_or_evs_disable_alternative_guess(self):
        for raw in ({'stats':{'atk':211}}, {'nature':'Timid'}, {'evs':'252 HP / 252 SpA / 4 SpD'}):
            threats,foe=self.threats(dict(name='Lapras',**raw))
            self.assertTrue(all(p is foe for m,p,w in threats))

    def test_explicit_removed_item_is_preserved(self):
        threats,foe=self.threats({'name':'Lapras','item':''})
        self.assertTrue(all(p['item']=='' for m,p,w in threats))

if __name__=='__main__':unittest.main()
