import importlib.util
import itertools
from pathlib import Path
import random
import unittest

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
