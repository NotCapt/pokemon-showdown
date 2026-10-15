import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
digest=hashlib.sha256((root/'submission/agent.py').read_bytes()).hexdigest()
lines=['# Final validation results','',f'Agent SHA-256: `{digest}`','',
       'All rows below use this exact generated file and Pokémon Showdown 0.11.11.',
       '', '| Opponent / observation | Wins | Losses | Draws | Median / p95 decision time |',
       '| --- | ---: | ---: | ---: | --- |']
for filename,label in [('final-tactical.json','Damage-calculating tactical baseline'),('final-search.json','Same search policy on portal-default teams'),('final-sparse.json','Tactical baseline; empty boosts and fresh agent every decision')]:
    d=json.loads((root/'research'/filename).read_text())
    assert d['agentSha256']==digest,filename+' is stale'
    assert all(r['errors']==0 for r in d['results'])
    t=d['latencyMs']
    lines.append(f"| {label} | {d['wins']}/{d['games']} | {d['losses']} | {d['draws']} | {t['median']:.1f} / {t['p95']:.1f} ms |")
portal=json.loads((root/'research/portal-result.json').read_text())
lines+=['',f"Latest normal portal practice: **{portal['winner']} won in {portal['turns']} turns**, battle `{portal['battleId']}`.",
        'Ten unittest tests passed, including 100 generated legality states, forced switches, immunities, priority knockouts, Focus Sash, burns and setup caps.',
        'No illegal actions or decision exceptions occurred in the final 200 local battles.', '',
        '## How to interpret this','',
        'These are wins against specific local opponents, not an estimated probability of winning the tournament. All opposing teams used portal-default sets; no independent top-tier competitive bot was benchmarked. The search opponent is a copy of our own policy, not FoulPlay.',
        'Team-selection runs used 40 battles per candidate. Evaluation uses separate seeds, with the first four opposing team compositions fixed and subsequent teams sampled from the roster. Each pair reverses player position on the same matchup and simulator seed. Evaluation seeds were reused for regression checks after compatibility fixes; this is not an untouched final blind test.',
        'JSON reports include per-game seeds, teams, outcomes and latencies. Their simple Wilson intervals do not adjust for paired/correlated matches or team selection and should be read only as descriptive approximations.',
        'Timing was measured locally while several benchmark processes shared CPU. It does not establish the hosting service deadline.',
        'The harness supplies only documented observable fields: it does not leak the opponent\'s private moves, items, abilities, EVs or bench state. The sparse test additionally removes our own boosts and discards agent-instance memory.', '',
        '## Portal observations','',
        'Normal production tests won in 29, 11, 5 and 8 turns across iterations. These four games are integration smoke tests, not a representative win-rate sample. Replay inspection found excess setup; final safeguards limit it under missing or stateless telemetry.',
        'An approved diagnostic exception returned a service Runtime.ExitError. An approved invalid-action probe was silently replaced by fallback moves and finished a battle; that diagnostic result is excluded from normal test results. It did not reveal the raw observation.',
        'The latest normal replay and result are preserved locally. The remote replay URL may be ephemeral; use the saved response as the durable record.']
(root/'research/RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
h=portal['replayHtml'];start=h.find('|t:|')
(root/'research/portal-replay.html').write_text(h,encoding='utf-8')
(root/'research/portal-battle.log').write_text(h[start:h.find('</script>',start)],encoding='utf-8')
print('Verified report hashes and saved final results/replay.')
