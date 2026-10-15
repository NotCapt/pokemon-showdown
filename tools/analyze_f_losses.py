"""Summarize saved real battles and public traces for candidate development."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
report=json.loads((root/'research/f-control-dev.json').read_text())
for row in report['results']:
    if row['winner']=='agent':continue
    trace=json.loads((root/f'research/f-control-traces/game-{row["game"]}.json').read_text())
    decisions=trace['decisions']
    print('\nGAME',row['game'],row['opponent'],row['winner'],'turns',row['turns'])
    for d in decisions:
        o=d['observation'];a=o.get('my_active',{});b=o.get('foe',{})
        print(o.get('turn'),a.get('name'),round(a.get('hp_percent',0)),b.get('name'),b.get('hp_percent'),d['action'],
              'forced' if o.get('force_switch') else '')
