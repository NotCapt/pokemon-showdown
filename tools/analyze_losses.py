"""Summarize actual battle losses; replay events are diagnostics, not causal proof."""
import argparse
from collections import Counter
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--report', required=True)
p.add_argument('--logs', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
report = json.loads(Path(a.report).read_text())
losses = []
killers = Counter()
teams = Counter()
for game in report['results']:
    if game['winner'] != 'baseline':
        continue
    own = 'p' + str(game['side'])
    enemy = 'p' + str(3 - game['side'])
    lines = (Path(a.logs) / f"game-{game['game']}.log").read_text().splitlines()
    turn = 0
    last_move = None
    deaths = []
    resisted = []
    switches = 0
    for line in lines:
        parts = line.split('|')
        if len(parts) < 3:
            continue
        event = parts[1]
        if event == 'turn':
            turn = int(parts[2])
        elif event == 'move':
            last_move = dict(turn=turn, user=parts[2], move=parts[3])
        elif event == 'faint' and parts[2].startswith(own):
            deaths.append(dict(turn=turn, pokemon=parts[2], precedingMove=last_move))
            if last_move and last_move['user'].startswith(enemy):
                killers[last_move['user'].split(': ')[-1]] += 1
        elif event in ('-resisted', '-immune') and parts[2].startswith(enemy):
            if last_move and last_move['user'].startswith(own):
                resisted.append(dict(last_move, result=event))
        # Switch health events appear twice in private/public split logs.
        elif event == 'switch' and parts[2].startswith(own):
            switches += 1
    teams[' / '.join(game['opponent'])] += 1
    losses.append(dict(game=game['game'], turns=game['turns'], opponent=game['opponent'],
                       ownEntries=switches // 2, ownFaints=deaths, resistedAttacks=resisted))
result = dict(source=a.report, games=report['games'], wins=report['wins'],
              lossCount=len(losses), opponentTeams=teams.most_common(),
              precedingEnemyAttackFaints=killers.most_common(), losses=losses,
              caveat='A preceding move is not necessarily the cause of a faint (recoil and residual damage exist). Hidden sets in reports are used only for offline evaluation, never agent decisions.')
Path(a.out).write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != 'losses'}, indent=2))
