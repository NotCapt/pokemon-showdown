"""Infer entry hazards only from clean forced-entry HP observations."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'archive/v4_3_2/agent_core.py').read_text()
helper='''def entry_damage(mon,state):
    """Exact floor damage for one plausible (Stealth Rock, Spikes) state."""
    if mon['item']=='heavydutyboots' or mon['ability']=='magicguard': return 0.
    rock,layers=state
    hp=max(1,mon['stats']['hp'])
    loss=max(1,math.floor(hp*effectiveness('Rock',mon['types'])/8)) if rock else 0
    if layers and 'Flying' not in mon['types'] and mon['ability']!='levitate':
        loss+=max(1,math.floor(hp/(8 if layers==1 else 6 if layers==2 else 4)))
    return 100*loss/hp


'''
s=s.replace('class PokemonAgent:',helper+'class PokemonAgent:',1)
s=s.replace('        self.entry_boosts={}\n', '        self.entry_boosts={}\n        self.hazard_states=None\n        self.forced_entry=None\n',1)
methods='''    def observe_entry(self,mon,turn_no):
        pending=self.forced_entry
        self.forced_entry=None
        if not pending or mon['key']!=pending[0] or turn_no not in (pending[2],pending[2]+1): return
        lost=max(0,pending[1]-mon['hp'])
        tolerance=105/max(1,mon['stats']['hp'])
        possible=[]
        for rock in (False,True):
            for layers in range(4):
                state=(rock,layers);damage=entry_damage(mon,state)
                if (damage>=lost-tolerance if mon['hp']<=0 else abs(damage-lost)<=tolerance):
                    possible.append(state)
        if not possible:
            self.hazard_states=None
            return
        prior=set(self.hazard_states or [])
        narrowed=[state for state in possible if state in prior]
        # A changed field can invalidate earlier observations. Restart from the
        # newly compatible states rather than retaining a contradicted estimate.
        self.hazard_states=narrowed or possible

    def entry_loss(self,mon):
        # Infer only damage shared by every compatible field state. A Flying
        # entry cannot establish that Spikes exist beneath it.
        return min((entry_damage(mon,state) for state in self.hazard_states),default=0.) if self.hazard_states else 0.

'''
s=s.replace('    def decide(self, observation):',methods+'    def decide(self, observation):',1)
s=s.replace("        b=build_mon(o.get('foe') or {})", "        b=build_mon(o.get('foe') or {})\n        if 'hp_percent' in (o.get('my_active') or {}): self.observe_entry(a,turn_no)\n        else: self.forced_entry=None",1)
old="""                        enter_intimidate(x,y)
                        if not o.get('force_switch'): apply_move(y,x,enemy_move,weather,roll); end_turn(x,y,weather)"""
new="""                        x['hp']=max(0,x['hp']-self.entry_loss(x))
                        if x['hp']>0:
                            enter_intimidate(x,y)
                        if not o.get('force_switch'):
                            if x['hp']>0: apply_move(y,x,enemy_move,weather,roll)
                            end_turn(x,y,weather)"""
assert old in s;s=s.replace(old,new)
s=s.replace("            entering=build_mon(target,True)\n            defender=clone_mon(b)","""            entering=build_mon(target,True)
            # A pivot can leave attacks queued for the entering Pokemon; only
            # a faint replacement gives a clean before/after entry observation.
            if o.get('force_switch') and a['hp']<=0 and target.get('hp_percent') is not None: self.forced_entry=(entering['key'],entering['hp'],turn_no)
            entering['hp']=max(0,entering['hp']-self.entry_loss(entering))
            defender=clone_mon(b)""")
s=s.replace("            enter_intimidate(entering,defender)","            if entering['hp']>0: enter_intimidate(entering,defender)")
(root/'research/f-hazards-core.py').write_text(s)
