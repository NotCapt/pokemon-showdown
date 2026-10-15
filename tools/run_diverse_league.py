"""Resume the frozen campaign with retries for Windows output-file locks."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import evaluate_diverse_league as league


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='research/diverse-league-v1')
    parser.add_argument('--workers',type=int,default=6);args=parser.parse_args()
    out=(league.ROOT/args.out).resolve()
    original_write=league.write
    def retry_write(path,value):
        for attempt in range(40):
            try:return original_write(path,value)
            except PermissionError:
                if attempt==39:raise
                time.sleep(min(.025*(attempt+1),.25))
    league.write=retry_write
    source=Path(__file__).read_bytes()
    metadata=dict(reason='Retry transient Windows PermissionError while recording progress and job stamps.',
        adapterSha256=hashlib.sha256(source).hexdigest(),
        evaluationScriptSha256=league.sha(league.ROOT/'tools/evaluate_diverse_league.py'),
        manifestSha256=league.sha(out/'manifest.json'),
        effect='Output I/O only; candidate/opponent sources, schedules, scores and promotion criteria unchanged. Cached complete jobs are reused.')
    (out/'reference/writer-adapter.py').write_bytes(source)
    retry_write(out/'execution-adapter.json',metadata)
    league.run(out,args.workers)


if __name__=='__main__':main()
