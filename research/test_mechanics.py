"""Regression checks for the experimental mechanics candidate, not the v4 release."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate',ROOT/'research/v5-mechanics/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class MechanicsTests(unittest.TestCase):
    def test_single_hit_showdown_fixtures(self):
        for f in json.loads((ROOT/'research/damage-oracle.json').read_text()):
            a,b=agent.build_mon(f['source']),agent.build_mon(f['target'])
            predicted=agent.damage(a,b,agent.DATA['moves'][f['move']],f['weather'],f['roll'])*f['maxhp']/100
            self.assertAlmostEqual(predicted,f['damage'],places=6,msg=str((a['name'],b['name'],f['move'],f['roll'])))

    def test_protean_only_changes_type_once(self):
        a=agent.build_mon({'name':'Greninja'});b=agent.build_mon({'name':'Snorlax'})
        agent.apply_move(a,b,dict(agent.DATA['moves']['icebeam'],_hit=True),'',1)
        self.assertEqual(a['types'],['Ice'])
        agent.apply_move(a,b,dict(agent.DATA['moves']['darkpulse'],_hit=True),'',1)
        self.assertEqual(a['types'],['Ice'])

    def test_opposing_intimidate_is_not_reapplied(self):
        p=agent.PokemonAgent()
        o={'turn':1,'my_active':{'name':'Dragonite'},'foe':{'name':'Gyarados'},'valid_moves':[dict(agent.DATA['moves']['extremespeed'],index=1)]}
        p.decide(o);self.assertEqual(p.estimated_boosts.get('atk'),-1)
        o['turn']=2;p.decide(o)
        self.assertEqual(p.estimated_boosts.get('atk'),-1)
        o['turn']=3;o['foe']['name']='Salamence';p.decide(o)
        self.assertEqual(p.estimated_boosts.get('atk'),-2)

    def test_reported_intimidate_is_not_double_counted(self):
        p=agent.PokemonAgent()
        p.decide({'turn':1,'my_active':{'name':'Dragonite','boosts':{'atk':-1}},'foe':{'name':'Gyarados'},'valid_moves':[dict(agent.DATA['moves']['extremespeed'],index=1)]})
        self.assertEqual(p.estimated_boosts.get('atk'),-1)

if __name__=='__main__': unittest.main()
