"""Compare matched schedules, bootstrapping whole opposing-team clusters."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import random

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--candidate',required=True);parser.add_argument('--control',required=True)
parser.add_argument('--candidate-file');parser.add_argument('--control-file')
parser.add_argument('--out',required=True)
args=parser.parse_args()
a,b=[json.loads((root/name).read_text()) for name in (args.candidate,args.control)]
for report,path in ((a,args.candidate_file),(b,args.control_file)):
    if path: assert hashlib.sha256((root/path).read_bytes()).hexdigest()==report['agentSha256'], 'stale source: '+path
for k in ('games','simulatorVersion','sparseBoosts','stateless'):
    assert a[k]==b[k], 'unmatched '+k
if 'opponentPolicySha256' in a and 'opponentPolicySha256' in b:
    assert a['opponentPolicySha256']==b['opponentPolicySha256']
assert len(a['results'])==len(b['results'])==a['games']
clusters=collections.defaultdict(list);improved=regressed=0
for x,y in zip(a['results'],b['results']):
    for k in ('game','seed','side','opponentSets','baseline'):assert x[k]==y[k], 'unmatched schedule: '+k
    assert x['errors']==y['errors']==0
    delta=int(x['winner']=='agent')-int(y['winner']=='agent')
    improved+=delta>0;regressed+=delta<0
    clusters[json.dumps(x['opponentSets'],sort_keys=True)].append(delta)
rng=random.Random(9187);groups=list(clusters.values());boot=[]
for _ in range(5000):
    sampled=[rng.choice(groups) for _ in groups]
    boot.append(100*sum(sum(g) for g in sampled)/sum(len(g) for g in sampled))
boot.sort()
result=dict(candidate=args.candidate,control=args.control,candidateSha256=a['agentSha256'],controlSha256=b['agentSha256'],
    games=a['games'],opposingTeamClusters=len(groups),candidateWins=a['wins'],controlWins=b['wins'],
    gainPP=100*(a['wins']-b['wins'])/a['games'],improvedGames=improved,regressedGames=regressed,
    clusterBootstrap95GainPP=[boot[125],boot[4874]],
    method='5000 replicates, seed 9187; resample entire ordered opposing-team/set clusters to retain repeated-team and side-pair dependence. Descriptive, no adjustment for candidate selection.')
(root/args.out).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
