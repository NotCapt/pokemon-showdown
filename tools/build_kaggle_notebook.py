"""Build a self-contained Kaggle notebook with a checksummed source bundle."""
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
# Preserve the running distributed campaign when the recommended policy changes.
# Every notebook in that campaign must keep compiling the same frozen policy.
CAMPAIGN = ROOT/'archive/v4_3_2'
files = ['agent_core.py', 'team.json', 'package.json', 'package-lock.json',
         'tools/build_agent.py', 'tools/benchmark.js', 'tools/worker.py', 'tools/opponents.js',
         'tools/make_eval_teams.py', 'tools/team_search.py', 'research/options.json',
         'research/battle_data.json', 'research/enemy_sets.json', 'research/SHOWDOWN_LICENSE.txt',
         'archive/v1/agent.py', 'archive/v4_3/agent.py', 'archive/v4_3/team.json']
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in files:
        info = zipfile.ZipInfo(name, date_time=(2026, 10, 16, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        source=CAMPAIGN/Path(name).name if name in ('agent_core.py','team.json') else ROOT/name
        z.writestr(info, source.read_bytes())
payload = buffer.getvalue()
sha = hashlib.sha256(payload).hexdigest()
(ROOT/'dist/REDLINE_Kaggle_Project.zip').write_bytes(payload)
(ROOT/'dist/REDLINE_Kaggle_Project_v4_3_2.zip').write_bytes(payload)
cells = []
def markdown(text): cells.append(dict(cell_type='markdown', metadata={}, source=text.splitlines(True)))
def code(text): cells.append(dict(cell_type='code', metadata={}, execution_count=None, outputs=[], source=text.splitlines(True)))

markdown('''# REDLINE: resumable Pokémon team search

CPU experiment for the current v4.3.2 agent. Enable **Internet**, choose **CPU**, edit the configuration, then Run All.
The source is embedded and checksummed: no GitHub checkout or credentials are required.

**Quick** screens 48 starting teams. **Full** screens all 2,024 species trios with one legal default build per trio, then mutates surviving sets and order. Neither enumerates every possible moveset or proves a globally optimal team. Defaults with non-allowed EV labels/natures are normalized to the contest's allowed choices.

Successive elimination uses adaptive, tactical and frozen v4.3 opponents. Teams are compiled into their own agent before testing. Validation and confirmation use separate seeds and opponent teams; confirmation compares one selected challenger with the incumbent. Low-budget screening can discard good teams, and these opponents are only a proxy for the tournament.

Outputs are experiments, not automatic changes to the recommended submission. The final ZIP contains exactly agent.py and team.txt. Review confirmation results before promoting it. Smoke mode only checks that the pipeline works.
''')
code('''PROFILE = "quick"  # "smoke", "quick", or "full"
MAX_HOURS = 6
MAX_GAMES = 60000
WORKERS = 2  # 1-3 independent CPU battle processes; no GPU needed
SEED = 43179
# To resume a prior session, attach its redline-checkpoint.zip as a Kaggle dataset,
# set this to its /kaggle/input/... path, and keep PROFILE and SEED unchanged.
RESUME_ZIP = ""
''')
code('''import base64, hashlib, io, json, os, pathlib, shutil, subprocess, sys, tarfile, urllib.request, zipfile
WORK = pathlib.Path('/kaggle/working') if pathlib.Path('/kaggle').exists() else pathlib.Path.cwd() / 'redline-working'
WORK.mkdir(parents=True, exist_ok=True)
PROJECT = WORK / 'redline-project'
RESULTS = WORK / 'redline-results'

def extract_zip(data, target):
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(data) as archive:
        for member in archive.infolist():
            destination = (target / member.filename).resolve()
            if target.resolve() not in destination.parents:
                raise ValueError('Unsafe archive member: ' + member.filename)
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(member))
'''+f"\nBUNDLE_SHA256 = {sha!r}\nBUNDLE = {base64.b64encode(payload).decode()!r}\n"+'''
data = base64.b64decode(BUNDLE)
assert hashlib.sha256(data).hexdigest() == BUNDLE_SHA256
extract_zip(io.BytesIO(data), PROJECT)
if RESUME_ZIP:
    if RESULTS.exists() and any(RESULTS.iterdir()):
        raise ValueError('Results already exist: clear RESUME_ZIP to continue this session.')
    extract_zip(RESUME_ZIP, RESULTS)
print('Verified embedded project:', BUNDLE_SHA256)
''')
code('''# Install a pinned official Node runtime only if Node >=20 is unavailable.
import platform
node = shutil.which('node')
major = int(subprocess.check_output([node, '--version'], text=True).strip().lstrip('v').split('.')[0]) if node else 0
if major < 20:
    if platform.system() != 'Linux':
        raise RuntimeError('Install Node.js >=20, then rerun this cell. Kaggle Linux installs automatically.')
    arch = {'x86_64': 'x64', 'aarch64': 'arm64'}[platform.machine()]
    name = f'node-v24.13.0-linux-{arch}'
    base = 'https://nodejs.org/dist/v24.13.0/'
    checksums = urllib.request.urlopen(base+'SHASUMS256.txt', timeout=60).read().decode()
    expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == name+'.tar.xz')
    binary = urllib.request.urlopen(base+name+'.tar.xz', timeout=120).read()
    assert hashlib.sha256(binary).hexdigest() == expected
    # Extract only files/directories from the official verified archive.
    with tarfile.open(fileobj=io.BytesIO(binary), mode='r:xz') as archive:
        for member in archive.getmembers():
            dest = (WORK/member.name).resolve()
            if WORK.resolve() not in dest.parents: raise ValueError('Unsafe Node archive')
            if member.isdir(): dest.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.extractfile(member).read())
                dest.chmod(member.mode)
    # npm is a symlink in the archive; recreate its known official target.
    npm = WORK/name/'bin/npm'
    if not npm.exists(): npm.symlink_to('../lib/node_modules/npm/bin/npm-cli.js')
    os.environ['PATH'] = str(WORK/name/'bin') + os.pathsep + os.environ['PATH']
print(subprocess.check_output(['node', '--version'], text=True).strip())
subprocess.run(['npm', 'ci', '--omit=optional', '--no-audit', '--no-fund'], cwd=PROJECT, check=True)
''')
code('''# Completed jobs are cached atomically. Rerun with identical inputs to resume.
# A budget pause is expected; increase MAX_HOURS/MAX_GAMES to continue.
command = [sys.executable, 'tools/team_search.py', '--profile', PROFILE,
           '--out', str(RESULTS), '--hours', str(MAX_HOURS), '--max-games', str(MAX_GAMES),
           '--workers', str(WORKERS), '--seed', str(SEED)]
try:
    subprocess.run(command, cwd=PROJECT, check=True)
finally:
    if RESULTS.exists():
        shutil.make_archive(str(WORK/'redline-checkpoint'), 'zip', RESULTS)
        print('Checkpoint saved:', WORK/'redline-checkpoint.zip')
''')
code('''from IPython.display import FileLink, display
result = RESULTS/'result.json'
if result.exists():
    summary = json.loads(result.read_text())
    print(summary['warning'])
    print('Selected team:', ', '.join(p['name'] for p in summary['selected']['team']))
    for candidate in summary['confirmation']:
        print('Incumbent' if candidate['incumbent'] else 'Challenger', candidate['rates'], 'games:', candidate['games'])
    display(FileLink(str(RESULTS/'best_candidate.zip')))
elif (RESULTS/'status.json').exists():
    print((RESULTS/'status.json').read_text())
display(FileLink(str(WORK/'redline-checkpoint.zip')))
print('Download files from the Kaggle Output panel after saving a completed version.')
''')
notebook = dict(cells=cells, metadata=dict(kernelspec=dict(display_name='Python 3', language='python', name='python3'),
                                        language_info=dict(name='python', version='3.11.0')), nbformat=4, nbformat_minor=5)
for i, cell in enumerate(cells): cell['id'] = f'redline-{i}'
path = ROOT/'notebooks/REDLINE_Team_Search.ipynb'; path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(notebook, indent=1), encoding='utf-8')
print(json.dumps(dict(notebook=str(path), bytes=path.stat().st_size, bundleSha256=sha)))
