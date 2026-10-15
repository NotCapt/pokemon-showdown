"""Scoring and paired-schedule checks for the broader opponent league."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import evaluate_diverse_league as league


class DiverseLeagueTests(unittest.TestCase):
    def reports(self):
        control=[];challenger=[]
        for category in league.WEIGHTS:
            for index in range(12 if category=='league' else 1):
                job=dict(category=category,opponentId=str(index) if category=='league' else None)
                rows=[dict(winner='baseline',seed=[1,2,1,19],side=i+1,
                           opponentSets=[dict(name='fixed')],baseline=category) for i in range(2)]
                report=dict(games=2,wins=0,draws=0,results=rows)
                control.append((job,report));challenger.append((copy.deepcopy(job),copy.deepcopy(report)))
        return control,challenger

    def test_one_fixed_opponent_has_only_one_thirtieth_weight(self):
        control,challenger=self.reports()
        job,report=challenger[2]
        self.assertEqual(job['category'],'league')
        report['wins']=2
        for row in report['results']:row['winner']='agent'
        result=league.compare(control,challenger)
        self.assertAlmostEqual(result['weightedGainPP'],100/30)
        self.assertEqual(result['clusterCounts']['league'],12)

    def test_identical_results_have_zero_gain_and_interval(self):
        result=league.compare(*self.reports())
        self.assertEqual(result['weightedGainPP'],0)
        self.assertEqual(result['pairedInterval95'],[0,0])

    def test_mismatched_seed_cannot_be_a_paired_comparison(self):
        control,challenger=self.reports()
        challenger[0][1]['results'][0]['seed'][-1]+=1
        with self.assertRaises(AssertionError):league.compare(control,challenger)


if __name__=='__main__':unittest.main()
