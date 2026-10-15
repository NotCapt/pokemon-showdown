"""Evaluate a declared 20% off-role priority-set prior, independent of defaults."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'research/f-priority-alt-core.py').read_text()
s=s.replace("            threats.append((priority,alternate,.6))", """            total=sum(weight for enemy,model,weight in threats)
            threats=[(enemy,model,.8*weight/total) for enemy,model,weight in threats]
            threats.append((priority,alternate,.2))""")
(root/'research/f-priority-mix-core.py').write_text(s)
