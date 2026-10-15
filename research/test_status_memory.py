"""Tests for the status-memory experiment; not the recommended release."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate',ROOT/'research/v4_2-status/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)

class StatusTests(unittest.TestCase):
    def test_bench_status_survives_sparse_switch_observations(self):
        p=agent.PokemonAgent()
        p.decide({'turn':1,'my_active':{'name':'Dragonite','condition':'200/323 par','hp_percent':62},'foe':{'name':'Metagross'},'valid_moves':[dict(agent.DATA['moves']['extremespeed'],index=1)]})
        bench=p.switch_mon({'name':'Dragonite','hp_percent':62})
        self.assertEqual(bench['status'],'par')
        fresh=agent.build_mon({'name':'Dragonite','hp_percent':62},True)
        self.assertEqual(agent.stat(bench,'spe'),agent.stat(fresh,'spe')*.5)
        self.assertEqual(p.switch_mon({'name':'Dragonite','status':''})['status'],'')
        self.assertEqual(p.switch_mon({'name':'Dragonite','condition':'200/323'})['status'],'')

    def test_updates_after_cure_and_resets_next_battle(self):
        p=agent.PokemonAgent()
        o={'turn':5,'my_active':{'name':'Arcanine','condition':'300/384 brn'},'foe':{'name':'Metagross'},'valid_moves':[dict(agent.DATA['moves']['flareblitz'],index=1)]}
        p.decide(o);self.assertEqual(p.switch_mon({'name':'Arcanine'})['status'],'brn')
        o['turn']=6;o['my_active']['condition']='300/384';p.decide(o)
        self.assertEqual(p.switch_mon({'name':'Arcanine'})['status'],'')
        p.own_status['Dragonite']='slp';o['turn']=1;p.decide(o)
        self.assertEqual(p.switch_mon({'name':'Dragonite'})['status'],'')

if __name__=='__main__':unittest.main()
