"""Correct Sucker Punch forecasts using the pinned official simulator mechanics."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'archive/v4_3_1/agent_core.py').read_text()
s=s.replace("if mid=='suckerpunch' and b.get('using_status'): d=0", "if mid=='suckerpunch' and (b.get('using_status') or b.get('acted')): d=0")
s=s.replace("    a['using_status']=ma.get('category')=='Status'; b['using_status']=mb.get('category')=='Status'", "    a['using_status']=ma.get('category')=='Status'; b['using_status']=mb.get('category')=='Status'\n    a['acted']=b['acted']=False")
s=s.replace("        apply_move(p,q,m,weather,roll)", "        p['acted']=True\n        apply_move(p,q,m,weather,roll)")
s=s.replace("                        x['boosts']={}\n                        enter_intimidate", "                        x['boosts']={}\n                        x['using_status']=True  # Switching is not an attacking move.\n                        enter_intimidate")
(root/'research/e-sucker-core.py').write_text(s)
