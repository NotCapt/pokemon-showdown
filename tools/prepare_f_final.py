"""Extract the tested priority-set prior into a directly testable helper."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'research/f-priority-mix-core.py').read_text()
start=s.index('        # Defaults get most prior mass;')
end=s.index('        actions=[]',start)
block=s[start:end]
weights="        weights=[weight for enemy,model,weight in threats]\n"
assert block.endswith(weights)
body=''.join(line[4:] for line in block[:-len(weights)].splitlines(True))
helper='''def enemy_threats(a,b,weather,o):
    """Bounded priors over legal moves and a coherent alternative priority set.

    The 20% alternative-set mass is fixed before confirmation, not a learned
    posterior. Explicit opposing stats, nature or EVs take precedence.
    """
'''+body+'    return threats\n\n\n'
s=s[:start]+"        threats=enemy_threats(a,b,weather,o)\n"+weights+s[end:]
s=s.replace('class PokemonAgent:',helper+'class PokemonAgent:',1)
(root/'research/f-final-core.py').write_text(s)
