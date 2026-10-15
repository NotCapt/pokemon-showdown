import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('agent',ROOT/'research/v4-map/agent.py')
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
class BeliefExperimentTests(unittest.TestCase):
    def mon(self,name,**kw): return agent.build_mon(dict(name=name,**kw))
    @unittest.skipUnless(hasattr(agent,'profile_mon'),'Experimental belief inference is not selected')
    def test_profile_keeps_coherent_moves_and_known_telemetry(self):
        profiles=agent.DATA['enemy_sets']['dragapult']
        special=next(p for p in profiles if 'Shadow Ball' in p['moves'])
        mon=agent.profile_mon({'name':'Dragapult','hp_percent':41,'item':''},special)
        self.assertEqual(mon['hp'],41);self.assertEqual(mon['item'],'')
        self.assertIn('shadowball',mon['moves']);self.assertLessEqual(len(mon['moves']),4)
    @unittest.skipUnless(hasattr(agent.PokemonAgent,'enemy_models'),'Experimental belief inference is not selected')
    def test_damage_evidence_updates_set_probabilities(self):
        p=agent.PokemonAgent();own=self.mon('Corviknight',hp_percent=100)
        models=p.enemy_models({'name':'Dragapult'},own,'',1)
        profiles=agent.DATA['enemy_sets']['dragapult']
        target=next(i for i,s in enumerate(profiles) if 'Shadow Ball' in s['moves'])
        before=p.beliefs['dragapult'][target]
        p.previous_damage=dict(foe='dragapult',own='corviknight',turn=1,hp=100,
            predictions=[[(50,60,1.)] if i==target else [(10,20,1.)] for i in range(len(models))])
        own['hp']=51.25
        p.enemy_models({'name':'Dragapult'},own,'',2)
        self.assertGreater(p.beliefs['dragapult'][target],before)
        self.assertAlmostEqual(sum(p.beliefs['dragapult']),1.)

if __name__=='__main__': unittest.main()
