"""Regression checks for the actual 100-turn HP objective and search horizon."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate',ROOT/'research/v6-release-candidate/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class EndgameTests(unittest.TestCase):
    def test_last_turn_prefers_larger_hp_gain_over_ko_count(self):
        p=agent.PokemonAgent();p.last_turn=99
        o={'turn':100,'my_active':{'name':'Snorlax','hp_percent':1,'boosts':{'spe':6}},
           'foe':{'name':'Garchomp','hp_percent':1},
           'valid_moves':[dict(agent.DATA['moves'][m],index=i+1) for i,m in enumerate(['bodyslam','rest'])]}
        self.assertEqual(p.decide(o),'move 2')

    def test_rollout_stops_at_turn_cap(self):
        original=agent.turn
        try:
            for turn_no,limit in ((98,3),(99,2),(100,1)):
                depths=[]
                def tracked(a,b,*args,**kwargs):
                    a['_test_depth']=a.get('_test_depth',0)+1
                    depths.append(a['_test_depth'])
                    return original(a,b,*args,**kwargs)
                agent.turn=tracked
                p=agent.PokemonAgent();p.last_turn=turn_no-1
                p.decide({'turn':turn_no,'my_active':{'name':'Corviknight','hp_percent':100},
                          'foe':{'name':'Snorlax','hp_percent':100},
                          'valid_moves':[dict(agent.DATA['moves']['irondefense'],index=1)]})
                self.assertTrue(depths)
                self.assertEqual(max(depths),limit)
        finally:agent.turn=original

    def test_forced_entry_does_not_spend_the_last_turn(self):
        original=agent.turn;depths=[]
        def tracked(a,b,*args,**kwargs):
            a['_test_depth']=a.get('_test_depth',0)+1
            depths.append(a['_test_depth'])
            return original(a,b,*args,**kwargs)
        try:
            agent.turn=tracked
            p=agent.PokemonAgent();p.last_turn=99
            p.decide({'turn':100,'force_switch':True,'my_active':{'name':'Dragonite','hp_percent':0},
                      'foe':{'name':'Snorlax','hp_percent':100},
                      'valid_switches':[{'name':'Corviknight','hp_percent':100,'index':2}]})
            self.assertTrue(depths)
            self.assertEqual(max(depths),1)
        finally:agent.turn=original

if __name__=='__main__':unittest.main()
