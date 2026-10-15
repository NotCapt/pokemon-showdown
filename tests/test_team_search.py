import importlib.util
import itertools
from pathlib import Path
import random
import unittest
import tempfile
import zipfile
import json

spec = importlib.util.spec_from_file_location('team_search', Path(__file__).resolve().parents[1]/'tools/team_search.py')
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)

class SearchLegality(unittest.TestCase):
    def test_all_species_trios_and_mutations_are_legal(self):
        count = 0
        rng = random.Random(11)
        for trio in itertools.combinations(search.OPTIONS['pokemon'], 3):
            team = [search.default(n) for n in trio]
            search.validate(team)
            search.validate(search.mutate(team, rng))
            count += 1
        self.assertEqual(count, 2024)

    def test_mutation_does_not_change_parent(self):
        import copy
        original = copy.deepcopy(search.INCUMBENT)
        for seed in range(100):
            search.mutate(search.INCUMBENT, random.Random(seed))
        self.assertEqual(search.INCUMBENT, original)

    def test_three_shards_cover_every_trio_once(self):
        pool=search.population('full',43179)
        pieces=[set(search.shard_indices(len(pool),i,3)) for i in range(3)]
        self.assertEqual([len(p) for p in pieces],[675,675,674])
        self.assertEqual(set.union(*pieces),set(range(2024)))
        self.assertFalse(pieces[0]&pieces[1] or pieces[0]&pieces[2] or pieces[1]&pieces[2])

    def test_merge_requires_matching_complete_distinct_shards(self):
        pool=search.population('smoke',43179)
        campaign={'seed':43179,'hashes':{'core':'abc'}}
        with tempfile.TemporaryDirectory() as tmp:
            paths=[]
            for i in range(3):
                path=Path(tmp)/f'{i}.zip';paths.append(path)
                payload=dict(status='complete',campaign=campaign,shardIndex=i,shardCount=3,
                             populationIndices=search.shard_indices(len(pool),i,3),populationSha256=search.digest(pool),
                             finalists=[pool[i]])
                with zipfile.ZipFile(path,'w') as z:z.writestr('screening.json',json.dumps(payload))
            self.assertEqual(len(search.read_screenings(paths,campaign,pool,3)),4)
            for bad in (paths[:2], [paths[0],paths[0],paths[2]]):
                with self.assertRaises(AssertionError):search.read_screenings(bad,campaign,pool,3)
            with self.assertRaises(AssertionError):search.read_screenings(paths,{'seed':99},pool,3)

    def test_hp_margin_breaks_screening_ties(self):
        a=dict(score=.8,hpMargin=5,incumbent=False,id='a')
        b=dict(score=.8,hpMargin=15,incumbent=False,id='b')
        self.assertGreater(search.ranking_key(b),search.ranking_key(a))

    def test_paired_comparison_counts_draws_and_checks_schedule(self):
        import copy
        reports=[]
        for policy in search.POLICIES:
            rows=[dict(seed=[1,2,i//2,31],side=i%2+1,opponentSets=[{'name':'Garchomp'}],baseline=policy,
                       winner='agent' if i==0 else 'baseline') for i in range(2)]
            reports.append(dict(games=2,team=search.INCUMBENT,wins=1,results=rows))
        challenger=copy.deepcopy(reports)
        for report in challenger:
            report['results'][1]['winner']=None
        result=search.compare_confirmation(reports,challenger)
        self.assertEqual(result['meanScoreGainPP'],25)
        self.assertEqual(result['improvedGames'],3)
        self.assertEqual(result['regressedGames'],0)
        challenger[0]['results'][0]['seed']=[1,2,3,4]
        with self.assertRaises(AssertionError):search.compare_confirmation(reports,challenger)
