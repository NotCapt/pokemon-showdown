"""Turn-cap decisions and compatibility with the v4.1 policy before the cap."""
import importlib.util
import os
import random
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('search_agent',ROOT/os.environ.get('AGENT_FILE','submission/agent.py'))
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class SearchTests(unittest.TestCase):
    def test_last_turn_rewards_hp_over_ko_count(self):
        p=agent.PokemonAgent();p.last_turn=99
        o={'turn':100,'weather':'sandstorm','my_active':{'name':'Corviknight','hp_percent':1},
           'foe':{'name':'Tyranitar','hp_percent':1},
           'valid_moves':[dict(agent.DATA['moves'][m],index=i+1) for i,m in enumerate(['bodypress','roost'])]}
        self.assertEqual(p.decide(o),'move 2')

    def test_rollout_stops_at_turn_cap(self):
        original=agent.turn
        try:
            for turn_no,limit in ((98,3),(99,2),(100,1)):
                depths=[]
                def tracked(a,b,*args,**kwargs):
                    a['_test_depth']=a.get('_test_depth',0)+1;depths.append(a['_test_depth'])
                    return original(a,b,*args,**kwargs)
                agent.turn=tracked
                p=agent.PokemonAgent();p.last_turn=turn_no-1
                p.decide({'turn':turn_no,'my_active':{'name':'Corviknight','hp_percent':100},
                          'foe':{'name':'Snorlax','hp_percent':100},
                          'valid_moves':[dict(agent.DATA['moves']['irondefense'],index=1)]})
                self.assertTrue(depths);self.assertEqual(max(depths),limit)
        finally:agent.turn=original

    def test_forced_entry_does_not_spend_last_turn(self):
        original=agent.turn;depths=[]
        def tracked(a,b,*args,**kwargs):
            a['_test_depth']=a.get('_test_depth',0)+1;depths.append(a['_test_depth'])
            return original(a,b,*args,**kwargs)
        try:
            agent.turn=tracked;p=agent.PokemonAgent();p.last_turn=99
            p.decide({'turn':100,'force_switch':True,'my_active':{'name':'Dragonite','hp_percent':0},
                      'foe':{'name':'Snorlax','hp_percent':100},
                      'valid_switches':[{'name':'Corviknight','hp_percent':100,'index':2}]})
            self.assertTrue(depths);self.assertEqual(max(depths),1)
        finally:agent.turn=original

    def test_decisions_match_v4_1_before_turn_98(self):
        spec=importlib.util.spec_from_file_location('reference',ROOT/'archive/v4_1/agent.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        rng=random.Random(5611);names=[p['name'] for p in agent.DATA['species'].values()]
        own=list(agent.OWN.values())
        for i in range(36):
            p=own[i%3]
            moves=[dict(agent.DATA['moves'][agent.ident(m)],index=j+1) for j,m in enumerate(p['moves'])]
            o={'turn':rng.choice([1,2,40,97]),'my_active':{'name':p['name'],'hp_percent':rng.randrange(1,101)},
               'foe':{'name':rng.choice(names),'hp_percent':rng.randrange(1,101)},'valid_moves':moves,
               'valid_switches':[{'name':q['name'],'hp_percent':rng.randrange(1,101),'index':j+1} for j,q in enumerate(own) if q!=p]}
            self.assertEqual(agent.PokemonAgent().decide(o),old.PokemonAgent().decide(o),msg=str(o))

if __name__=='__main__':unittest.main()
