"""Paired public-observation equivalence and timing; no hidden battle state."""
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__ == '__main__':
    modules = [load('archive/v4_3/agent.py', 'original'), load('research/d-fast/agent.py', 'fast')]
    elapsed = [0., 0.]
    count = 0
    for index, path in enumerate(sorted((ROOT/'research/c-control-traces').glob('game-*.json'))):
        agents = [m.PokemonAgent() for m in modules]
        for decision in json.loads(path.read_text())['decisions']:
            actions = [None, None]
            for i in ([0, 1] if count % 2 else [1, 0]):
                obs = json.loads(json.dumps(decision['observation']))
                start = time.perf_counter()
                actions[i] = agents[i].decide(obs)
                elapsed[i] += time.perf_counter() - start
            assert actions[0] == actions[1], (path, count, actions)
            assert agents[0].__dict__ == agents[1].__dict__, (path, count, 'memory differs')
            count += 1
    result = dict(decisions=count, originalSeconds=elapsed[0], fastSeconds=elapsed[1],
                  speedup=elapsed[0]/elapsed[1], identicalActionsAndMemory=True)
    (ROOT/'research/d-fast-equivalence.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
