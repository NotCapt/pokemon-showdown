import importlib.util
from pathlib import Path
import random
import os
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('agent',ROOT/os.environ.get('AGENT_FILE','submission/agent.py'))
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class AgentTests(unittest.TestCase):
    def mon(self,name,**kw): return agent.build_mon(dict(name=name,**kw))
    def test_ground_immunities(self):
        attack=self.mon('Garchomp'); foe=self.mon('Hydreigon'); move=agent.DATA['moves']['earthquake']
        self.assertEqual(agent.damage(attack,foe,move),0)
        attack['ability']='moldbreaker'
        self.assertGreater(agent.damage(attack,foe,move),0)
        self.assertEqual(agent.damage(attack,self.mon('Dragonite'),move),0)
    def test_freeze_dry(self):
        self.assertEqual(agent.effectiveness('Ice',['Water','Flying'],'freezedry'),4)
    def test_multiscale(self):
        a=self.mon('Garchomp'); b=self.mon('Dragonite'); m=agent.DATA['moves']['dragonclaw']
        reduced=agent.damage(a,b,m); b['hp']=99
        self.assertAlmostEqual(agent.damage(a,b,m),reduced*2,delta=100/b['stats']['hp']+1e-10)
    def test_boost_and_burn(self):
        a=self.mon('Garchomp');b=self.mon('Metagross');m=agent.DATA['moves']['earthquake']
        d=agent.damage(a,b,m);a['status']='brn'
        self.assertAlmostEqual(agent.damage(a,b,m),d/2,delta=100/b['stats']['hp'])
        a['boosts']['atk']=2
        self.assertGreater(agent.damage(a,b,m),d*.95)
    def test_preview_and_forced_switch(self):
        p=agent.PokemonAgent()
        self.assertEqual(p.decide({'team_preview':True}),'team 123')
        self.assertEqual(p.decide({'force_switch':True,'valid_moves':[{'index':1}], 'valid_switches':[{'index':1,'name':'Dragonite','hp_percent':50}]}),'switch 1')
    def test_priority_finish(self):
        p=agent.PokemonAgent()
        moves=[dict(agent.DATA['moves'][m],index=i+1) for i,m in enumerate(['extremespeed','earthquake'])]
        o={'my_active':{'name':'Dragonite','hp_percent':5},'foe':{'name':'Alakazam','hp_percent':5},'valid_moves':moves}
        self.assertEqual(p.decide(o),'move 1')
    def test_sash(self):
        a=self.mon('Garchomp');b=self.mon('Excadrill',hp_percent=100)
        a['boosts']['atk']=6
        agent.apply_move(a,b,agent.DATA['moves']['earthquake'],'',1)
        self.assertGreater(b['hp'],0); self.assertEqual(b['item'],'')
    def test_no_capped_setup(self):
        moves=[dict(agent.DATA['moves'][m],index=i+1) for i,m in enumerate(['bodypress','irondefense','roost','bravebird'])]
        o={'turn':7,'my_active':{'name':'Corviknight','hp_percent':100,'boosts':{'def':6}},'foe':{'name':'Metagross','hp_percent':15},'valid_moves':moves}
        self.assertNotEqual(agent.PokemonAgent().decide(o),'move 2')
        o['my_active']['boosts']={}; o['turn']=20
        self.assertNotEqual(agent.PokemonAgent().decide(o),'move 2')
    def test_bodypress_burn(self):
        a=self.mon('Corviknight');b=self.mon('Snorlax');m=agent.DATA['moves']['bodypress']
        d=agent.damage(a,b,m);a['status']='brn'
        self.assertAlmostEqual(agent.damage(a,b,m),d/2,delta=100/b['stats']['hp'])
    def test_miss_is_zero_damage(self):
        a=self.mon('Dragapult');b=self.mon('Volcarona');before=b['hp']
        m=dict(agent.DATA['moves']['dracometeor'],_hit=False)
        agent.apply_move(a,b,m,'',1)
        self.assertEqual(before,b['hp']);self.assertEqual(a['boosts'],{})
    def test_multihit_breaks_sash(self):
        a=self.mon('Dragapult'); a['boosts']['atk']=6
        b=self.mon('Alakazam',item='Focus Sash')
        agent.apply_move(a,b,dict(agent.DATA['moves']['dragondarts'],_hit=True),'',1)
        self.assertEqual(b['hp'],0)
    def test_multiscale_only_first_hit(self):
        a=self.mon('Dragapult');b=self.mon('Dragonite');m=agent.DATA['moves']['dragondarts']
        d=agent.damage(a,b,m);b['hp']=99
        self.assertAlmostEqual(d/agent.damage(a,b,m),.75,delta=.01)
    def test_setup_memory_and_switch_reset(self):
        p=agent.PokemonAgent();p.active_key='corviknight';p.last_turn=4
        p.pending=(4,agent.DATA['moves']['irondefense'])
        o={'turn':5,'my_active':{'name':'Corviknight','hp_percent':100},'foe':{'name':'Metagross','hp_percent':20},'valid_moves':[dict(agent.DATA['moves']['bodypress'],index=1)]}
        p.decide(o);self.assertEqual(p.estimated_boosts.get('def'),2)
        o['my_active']['name']='Dragonite';o['turn']=6
        p.decide(o);self.assertEqual(p.estimated_boosts,{})
    def test_speed_tie_both_orders(self):
        move=agent.DATA['moves']['icepunch']
        for first in (True,False):
            a=self.mon('Dragonite',hp_percent=1);b=self.mon('Dragonite',hp_percent=1)
            agent.turn(a,b,move,move,'',1,tie_first=first)
            self.assertEqual(a['hp']>0,first)
            self.assertEqual(b['hp']>0,not first)
    def test_search_clone_does_not_mutate_original(self):
        a=self.mon('Dragonite');b=agent.clone_mon(a)
        b['boosts']['atk']=6;b['hp']=0
        self.assertEqual(a['boosts'],{});self.assertEqual(a['hp'],100)
    def test_flinch_prevents_status_and_recoil_actions(self):
        a=self.mon('Togekiss');b=self.mon('Corviknight',hp_percent=40)
        move=dict(agent.DATA['moves']['airslash'],_hit=True,_flinch=True)
        agent.turn(a,b,move,agent.DATA['moves']['roost'],'',.925)
        self.assertLess(b['hp'],40)
        a=self.mon('Togekiss');b=self.mon('Corviknight',hp_percent=100)
        agent.turn(a,b,move,agent.DATA['moves']['bravebird'],'',.925)
        self.assertEqual(a['hp'],100)
    def test_inner_focus_and_miss_prevent_flinch(self):
        a=self.mon('Togekiss');b=self.mon('Lucario',ability='Inner Focus')
        self.assertEqual(agent.flinch_chance(a,agent.DATA['moves']['airslash'],b),0.)
        b=self.mon('Corviknight',hp_percent=40)
        agent.turn(a,b,dict(agent.DATA['moves']['airslash'],_hit=False,_flinch=True),agent.DATA['moves']['roost'],'',.925)
        self.assertGreater(b['hp'],40)
    def test_intimidate_immunities_and_reflection(self):
        for target,ability,expected in [('Garchomp','Rough Skin',-1),('Metagross','Clear Body',0),('Dragonite','Inner Focus',0)]:
            a=self.mon('Arcanine');b=self.mon(target,ability=ability)
            agent.enter_intimidate(a,b)
            self.assertEqual(b['boosts'].get('atk',0),expected)
        a=self.mon('Arcanine');b=self.mon('Corviknight')
        agent.enter_intimidate(a,b)
        self.assertEqual(a['boosts']['atk'],-1);self.assertEqual(b['boosts'].get('atk',0),0)
    def test_entry_boost_memory(self):
        p=agent.PokemonAgent()
        o={'turn':4,'force_switch':True,'my_active':{'name':'Dragonite','hp_percent':0},'foe':{'name':'Corviknight','hp_percent':100},'valid_switches':[{'name':'Arcanine','index':3,'hp_percent':100}]}
        self.assertEqual(p.decide(o),'switch 3')
        o={'turn':4,'my_active':{'name':'Arcanine','hp_percent':100,'boosts':{}},'foe':{'name':'Corviknight','hp_percent':100},'valid_moves':[dict(agent.DATA['moves']['flareblitz'],index=1)]}
        p.decide(o);self.assertEqual(p.estimated_boosts.get('atk'),-1)
    def test_protean_only_changes_type_once(self):
        a=self.mon('Greninja');b=self.mon('Snorlax')
        agent.apply_move(a,b,dict(agent.DATA['moves']['icebeam'],_hit=True),'',1)
        self.assertEqual(a['types'],['Ice'])
        agent.apply_move(a,b,dict(agent.DATA['moves']['darkpulse'],_hit=True),'',1)
        self.assertEqual(a['types'],['Ice'])
        observed=self.mon('Greninja',types=['Ice'])
        self.assertTrue(observed['protean_used'])
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
    def test_legality_random_states(self):
        rng=random.Random(43); names=list(agent.DATA['species']);p=agent.PokemonAgent()
        for i in range(100):
            name=rng.choice(names);foe=rng.choice(names)
            moves=[dict(agent.DATA['moves'][agent.ident(m)],index=j+1,disabled=rng.random()<.25) for j,m in enumerate(agent.DATA['species'][name]['defaultMoves'])]
            switches=[{'name':rng.choice(names),'index':3,'hp_percent':rng.randrange(1,101)}]
            o={'turn':i+1,'my_active':{'name':name,'hp_percent':rng.randrange(1,101)},'foe':{'name':foe,'hp_percent':rng.randrange(1,101)},'valid_moves':moves,'valid_switches':switches,'force_switch':rng.random()<.1}
            allowed={'switch 3'}|({f"move {m['index']}" for m in moves if not m['disabled']} if not o['force_switch'] else set())
            self.assertIn(p.decide(o),allowed)

if __name__=='__main__': unittest.main()
