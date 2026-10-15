"""Expand damage quantiles independently for each side of the forecast."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
frozen=root/'archive/v4_3_2';frozen.mkdir(exist_ok=True)
for src,dst in [('submission/agent.py','agent.py'),('submission/team.txt','team.txt'),('agent_core.py','agent_core.py'),('team.json','team.json')]:
    if not (frozen/dst).exists():shutil.copyfile(root/src,frozen/dst)
s=(frozen/'agent_core.py').read_text()
s=s.replace('def turn(a,b,ma,mb,weather,roll,tie_first=True):','def turn(a,b,ma,mb,weather,roll,tie_first=True,enemy_roll=None):')
s=s.replace('        apply_move(p,q,m,weather,roll)','        apply_move(p,q,m,weather,roll if p is a or enemy_roll is None else enemy_roll)')
s=s.replace('                for sample in range(12*order_count*flinch_count):\n                    roll=(.85,.925,1.0)[sample%3]\n                    branch=(sample//3)%4',
'''                for sample in range(36*order_count*flinch_count):
                    roll=(.85,.925,1.0)[sample%3]
                    enemy_roll=(.85,.925,1.0)[(sample//3)%3]
                    branch=(sample//9)%4''')
s=s.replace('(sample//12)%order_count','(sample//36)%order_count').replace('sample//(12*order_count)','sample//(36*order_count)')
s=s.replace('apply_move(y,x,enemy_move,weather,roll);','apply_move(y,x,enemy_move,weather,enemy_roll);')
s=s.replace('roll,tie_first=tie_first)','roll,tie_first=tie_first,enemy_roll=enemy_roll)')
s=s.replace('best_attack(y,x,weather),weather,roll)','best_attack(y,x,weather),weather,roll,enemy_roll=enemy_roll)')
s=s.replace('outcomes.append(sum(vals)/3)','outcomes.append(sum(vals)/9)')
(root/'research/f-independent-core.py').write_text(s)
