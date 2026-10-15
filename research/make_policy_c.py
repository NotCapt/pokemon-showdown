"""Construct scoped policy candidates without touching the recommended release."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
base=(root/'archive/v4_2/agent_core.py').read_text()
old="if a.get('locked'): choices=[m for m in choices if m['id']==a['locked']] or choices"
new="if a.get('locked') in DATA['moves']: choices=[dict(DATA['moves'][a['locked']])]"
assert base.count(old)==1
(root/'research/c-lock-core.py').write_text(base.replace(old,new))

helper='''def replacement_pressure(mon, defeated_key, weather, cache):
    """One public-prior exchange after a KO, never a peek at the enemy bench.

    All other curated species have equal prior mass. This is deliberately a
    weak continuation prior, not a claim about the actual unseen team.
    """
    key=(mon['key'], round(mon['hp']/5)*5, tuple(sorted(mon['boosts'].items())),
         mon['status'], mon['item'], mon.get('locked'), tuple(mon['moves']),
         tuple(mon['types']), mon.get('protean_used'), defeated_key, weather)
    if key in cache: return cache[key]
    outcomes=[]
    for species in DATA['species']:
        if species==defeated_key: continue
        x=clone_mon(mon)
        x['hp']=max(1,min(100,key[1]))
        y=build_mon({'name':species})
        enter_intimidate(y,x)
        enter_intimidate(x,y)
        before=value(x,y)
        turn(x,y,best_attack(x,y,weather),best_attack(y,x,weather),weather,.925)
        outcomes.append(value(x,y)-before)
    outcomes.sort()
    result=sum(outcomes)/max(1,len(outcomes))
    cache[key]=result
    return result


'''
# The incumbent remains unchanged on turns 98-100, whose objective is summed HP.
core=base.replace('class PokemonAgent:',helper+'class PokemonAgent:')
core=core.replace('        scored=[]','        scored=[]\n        replacement_cache={}')
core=core.replace('                    first=value(x,y)',
    "                    first=value(x,y)\n                    root_ko=y['hp']<=0 and x['hp']>0\n                    post_ko=.65*replacement_pressure(x,b['key'],weather,replacement_cache) if root_ko and turn_no<98 else 0.")
core=core.replace('                    second=value(x,y)',
    "                    second=value(x,y)\n                    if not root_ko and y['hp']<=0 and x['hp']>0 and turn_no<98:\n                        post_ko=.40*replacement_pressure(x,b['key'],weather,replacement_cache)")
core=core.replace("                    if s and not o.get('force_switch'):\n                        score-=", "                    score+=post_ko\n                    if s and not o.get('force_switch'):\n                        score-=")
(root/'research/c-replacement-core.py').write_text(core)
# Only the incoming opponent's entry ability activates after an enemy KO.
# Keep the first prototype immutable, so its running report retains provenance.
(root/'research/c-replacement-entry-core.py').write_text(core.replace('        enter_intimidate(x,y)\n        before=value(x,y)','        before=value(x,y)'))

core=base.replace('                    first=value(x,y)',
    "                    first=value(x,y)\n                    switch_faint=bool(s) and not o.get('force_switch') and x['hp']<=0")
core=core.replace("                    if s and not o.get('force_switch'):\n                        score-=", "                    if switch_faint and turn_no<98: score-=50\n                    if s and not o.get('force_switch'):\n                        score-=")
(root/'research/c-switch-core.py').write_text(core)
(root/'research/c-switch-scaled-core.py').write_text(core.replace("if switch_faint and turn_no<98: score-=50", "if switch_faint and turn_no<98: score-=.5*starting_hp"))
final=core.replace(old,new).replace("if switch_faint and turn_no<98: score-=50",
    "# Losing a reserve before it acts also loses its future options.\n                    # Scale that cost with HP so a weak sacrifice stays possible.\n                    if switch_faint and turn_no<98: score-=.5*starting_hp")
(root/'research/c-final-core.py').write_text(final)
