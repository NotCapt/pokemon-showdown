"""Summarize audited league evidence, including each frozen opponent separately."""
import argparse
import json
from pathlib import Path

import evaluate_diverse_league as league

p=argparse.ArgumentParser();p.add_argument('--out',default='research/diverse-league-v1');args=p.parse_args()
ROOT=league.ROOT;OUT=(ROOT/args.out).resolve()
manifest=json.loads((OUT/'manifest.json').read_text());result=json.loads((OUT/'result.json').read_text())
audit=json.loads((OUT/'audit.json').read_text())
assert audit['allSchedulesAndCompiledTeamsVerified'] and audit['checkedGames']==result['completedGames']==8856
assert audit['manifestSha256']==result['manifestSha256']==league.sha(OUT/'manifest.json')
control=result['incumbent'];challenger=result['challenger'];selected=result['selected'];comparison=result['comparison']
names=lambda t:'/'.join(p['name'] for p in t)
lines=['# Diverse league results','',f"Recommended by the frozen selection rule: **{names(selected['team'])}**.",
    '',f"Promotion gate passed: **{result['promote']}**. All {audit['checkedGames']:,} scheduled games and {audit['checkedReports']:,} reports passed the schedule/source audit. The source engine is unchanged v4.5; this campaign compares team builds, not newly trained decision models.",
    '', '## Independent confirmation','',
    f"The challenger **{names(challenger['team'])}** was selected on validation before confirmation. Each final build played {control['games']} fresh confirmation games. Qualification and validation games are excluded from the confirmation comparison.",
    '', '| Opponent category | Weight | Incumbent wins | Challenger wins | Score gain |',
    '| --- | ---: | ---: | ---: | ---: |']
for category,row in comparison['categories'].items():
    lines.append(f"| {category} | {100*manifest['weights'][category]:.0f}% | {row['controlWins']}/{row['games']} | {row['challengerWins']}/{row['games']} | {row['scoreGainPP']:+.2f} pp |")
lo,hi=comparison['pairedInterval95']
lines+=['',f"Weighted score: incumbent {100*control['score']:.2f}%, challenger {100*challenger['score']:.2f}%. Weighted gain {comparison['weightedGainPP']:+.3f} points; descriptive paired 95% interval [{lo:+.2f}, {hi:+.2f}]. Improved game outcomes: {comparison['improvedGames']}; regressed outcomes: {comparison['regressedGames']}.",
    '', 'The score is the weighted mean above, with no weakest-category term. Each of the twelve fixed teams contributes only 3.33% of the total score. The incumbent and earlier 188–4 challenger are both in that roster.',
    '', '## Fixed opponents, all three lead choices','',
    '| Opponent team | Incumbent wins | Challenger wins | Games each |', '| --- | ---: | ---: | ---: |']
for team in manifest['opponents']:
    identifier=league.team_id(team);rs={}
    for label,record in [('incumbent',control),('challenger',challenger)]:
        reports=[json.loads((OUT/'jobs'/f'confirmation-{record["id"]}-{j["key"]}.json').read_text())
                 for j in manifest['jobs']['confirmation'] if j['opponentId']==identifier]
        rs[label]=dict(wins=sum(r['wins'] for r in reports),games=sum(r['games'] for r in reports))
    lines.append(f"| {names(team)} | {rs['incumbent']['wins']} | {rs['challenger']['wins']} | {rs['incumbent']['games']} |")
lines+=['', '## Selection path','', '| Validation team | Weighted score | Wins / games |', '| --- | ---: | ---: |']
for row in json.loads((OUT/'validation-ranking.json').read_text()):
    lines.append(f"| {names(row['team'])} | {100*row['score']:.2f}% | {row['wins']}/{row['games']} |")
lines+=['', 'Twenty-five candidates played qualification, then three non-incumbents plus the incumbent played validation. One challenger was chosen there. Confirmation used separate generated opposing teams and random seeds. The fixed roster identities remain shared and known.',
    '', '## Selected configuration','']
for pokemon in selected['team']:
    lines.append(f"- {pokemon['name']}: {pokemon['item']} / {pokemon['ability']}, {pokemon['nature']}, {pokemon['evs']}. Moves: {', '.join(pokemon['moves'])}.")
lines+=['',f"Selected source SHA256: `{result['sourceSha256']}`.",f"Export ZIP SHA256: `{audit['selectedZipSha256']}`.",
    '', '## Rules, evidence and limits','',
    'Promotion required a higher confirmation score, a positive lower paired interval, and no category regression above five percentage points. The rule, weights, all candidates and all opponent schedules were recorded before this campaign. A failed gate retains the incumbent.',
    '', result['bootstrap'],
    '', 'The twelve frozen teams cover all 24 allowed species. Opponents use the same restricted public enemy observations; generated sets and the enemy bench remain hidden. All compiled team configurations, hashes, simulator seeds, player sides, opposing sets, score calculations, selection path and exported bytes were verified. There were zero reported action errors or worker exceptions.',
    '', 'The fixed team population and candidate pool were informed by earlier results. Fresh seeds measure repeated-match robustness, while the varied generated suites add new sets. This does not establish superiority against an unknown tournament field. The league still contains only three policy families; stronger independent policies and further untouched tests remain useful.',
    '', 'Four diagnostic games outside this league reproduced a prior losing pair and tested a forced alternate opening. They are excluded from scores and independent strength evidence. The alternative still lost; see diagnostics/REPORT.md.',
    '', 'To reproduce, extract `dist/REDLINE_Diverse_League_Project_v1.zip` into a separate Windows directory; the promoted working tree no longer has the original v4.5 control inputs. In that directory, run `python tools/run_diverse_league.py --workers 6`, then `python tools/audit_diverse_league.py` and `python tools/summarize_diverse_league.py`. The manifest rejects changed policy or schedule inputs. An output-only Windows file-lock retry adapter is separately hashed and audited.']
if (OUT/'execution-modes/summary.json').exists():
    modes=json.loads((OUT/'execution-modes/summary.json').read_text())
    assert modes['manifestSha256']==result['manifestSha256']
    lines+=['', '## Execution persistence diagnostic','',
            'The first four confirmation adaptive chunks were replayed with a fresh agent instance on every request. Opposing sets, seeds and sides were paired to the existing stateful cohorts. These 192 extra mode-check games do not change the frozen league score or selection.',
            '', '| Build | Stateful wins | Fresh instance wins | Games per mode |', '| --- | ---: | ---: | ---: |']
    for row in (control,challenger):
        mode=modes['results'][row['id']]
        assert mode['sourceSha256']==manifest['candidateSha256'][row['id']]
        lines.append(f"| {names(row['team'])} | {mode['statefulWins']} | {mode['statelessWins']} | {mode['gamesPerMode']} |")
if (OUT/'verification.json').exists():
    verification=json.loads((OUT/'verification.json').read_text())
    if verification['agentSha256']==result['sourceSha256']:
        assert verification['pythonTestsPassed'] and verification['jsTestsPassed'] and verification['teamTextMatches']
        lines+=['',f"Exact selected source checks passed: {verification['pythonTests']} Python tests, {verification['jsTests']} JavaScript checks, and exported team-text consistency."]
if (OUT/'release.json').exists():
    release=json.loads((OUT/'release.json').read_text());assert release['agentSha256']==result['sourceSha256']
    lines+=['', '## Release','',f"Promoted as {release['version']}; recommended artifact: dist/REDLINE_Search.zip. Versioned artifact: {release['versionedZip']}."]
if (OUT/'portal-result.json').exists():
    portal=json.loads((OUT/'portal-result.json').read_text())
    tested=json.loads((OUT/'portal-result.tested.json').read_text())
    release=json.loads((OUT/'release.json').read_text())
    assert tested['agentSha256']==release['agentSha256']==result['sourceSha256']
    assert tested['teamSha256']==release['teamSha256'] and tested['probe'] is False
    assert portal['success'] and portal['winnerSlot']=='p1'
    replay=portal['replayHtml']
    assert '|win|REDLINE Search' in replay
    smoke={key:portal[key] for key in ('success','battleId','winner','winnerSlot','turns')}
    smoke.update(tested)
    smoke['purpose']='Single authorized practice compatibility test against Sample Baseline; excluded from league strength estimates.'
    (OUT/'portal-summary.json').write_text(json.dumps(smoke,indent=2)+'\n',encoding='utf-8')
    lines+=['', '## Practice compatibility check','',
            f"The exact release source and team won one authorized practice battle against Sample Baseline in {portal['turns']} turns (battle `{portal['battleId']}`). The recorded upload hashes match this release. The replay shows one Iron Defense followed by Body Press, plus switches back to Dragapult. This checks service compatibility; a single sample-baseline win adds no reliable tournament-strength estimate and is excluded from the league score."]
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
summary=dict(status='complete',manifestSha256=result['manifestSha256'],promote=result['promote'],
    candidateCount=25,fixedRosters=12,coveredSpecies=24,distinctGeneratedOpponents=504,completedGames=8856,
    selectedNames=[p['name'] for p in selected['team']],comparison=comparison,sourceSha256=result['sourceSha256'])
(OUT/'campaign-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
