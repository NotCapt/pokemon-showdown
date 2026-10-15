"""Run a reproducible evaluation without inheriting stale benchmark settings."""
import argparse
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--agent',default='submission/agent.py');p.add_argument('--team',default='team.json')
p.add_argument('--suite');p.add_argument('--seed',type=int,required=True)
p.add_argument('--games',type=int,default=96);p.add_argument('--report',required=True)
p.add_argument('--policy',choices=['adaptive','tactical','power','stab','random','mixed','v4_1','frozen'],default='adaptive')
p.add_argument('--opponent-team')
p.add_argument('--opponent-agent')
p.add_argument('--stateless',action='store_true')
p.add_argument('--logs',help='Directory for actual simulator replay logs')
p.add_argument('--traces',help='Directory for agent observations and actions; excludes private opponent fields')
a=p.parse_args();assert a.games>0 and a.games%2==0,'Use side-reversed pairs.'
if a.policy=='v4_1' and not a.opponent_team:p.error('Archived policies require their actual --opponent-team configuration.')
if a.policy=='frozen' and not (a.opponent_team and a.opponent_agent):p.error('Frozen opponents require --opponent-agent and --opponent-team.')
env=os.environ.copy()
for k in ('AGENT_FILE','TEAM_FILE','OPP_TEAM_FILE','OPP_AGENT_FILE','OPPONENT','SEED','SPARSE','STATELESS','CUSTOM','MIRROR','SAVE_LOGS','TRACE_DIR','REPORT'):
    env.pop(k,None)
env.update(AGENT_FILE=a.agent,TEAM_FILE=a.team,OPPONENT=a.policy,SEED=str(a.seed),SPARSE='1',REPORT=a.report)
if a.policy=='mixed':env.pop('OPPONENT')
if a.suite:env['CUSTOM']=a.suite
if a.opponent_team:env['OPP_TEAM_FILE']=a.opponent_team
if a.opponent_agent:env['OPP_AGENT_FILE']=a.opponent_agent
if a.stateless:env['STATELESS']='1'
if a.logs:env['SAVE_LOGS']=a.logs
if a.traces:env['TRACE_DIR']=a.traces
subprocess.run(['node','tools/benchmark.js',str(a.games)],cwd=root,env=env,check=True)
