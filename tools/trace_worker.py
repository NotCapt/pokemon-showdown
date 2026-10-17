"""Read-only diagnostics around the unchanged battle worker and agent source."""
from pathlib import Path

path = Path(__file__).with_name('worker.py')
source = path.read_text(encoding='utf-8')
before = "print(json.dumps({'action':action,'ms':(time.perf_counter()-start)*1000}),flush=True)"
after = "print(json.dumps({'action':action,'ms':(time.perf_counter()-start)*1000,'diagnostics':dict(mc=getattr(agents[key],'mc_last',None),ownBoosts=getattr(agents[key],'estimated_boosts',{}),foeBoosts=getattr(agents[key],'foe_boost_est',{}))}),flush=True)"
assert source.count(before) == 1
exec(compile(source.replace(before, after), str(path), 'exec'))
