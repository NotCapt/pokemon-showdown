"""Create three disjoint screen notebooks and one common final comparison."""
import copy
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'tools/build_kaggle_notebook.py'))
base=json.loads((ROOT/'notebooks/REDLINE_Team_Search.ipynb').read_text(encoding='utf-8'))
for index in range(4):
    final=index==3
    nb=copy.deepcopy(base)
    def source(cell,text):nb['cells'][cell]['source']=text.splitlines(True)
    title='Final comparison' if final else f'Screen {index+1} of 3'
    source(0,f'''# REDLINE parallel search: {title}

CPU only. Enable Internet, then Save Version > Save & Run All. Each notebook embeds the exact same checksummed source.

'''+('''Run this notebook **after all three screens finish**. Add the three screen notebooks as inputs using Add Input > Notebook, or attach their compact redline-screen-1.zip, redline-screen-2.zip and redline-screen-3.zip files as a dataset. Paths are detected automatically below. All three must use the same profile, seed and source bundle; mismatches and incomplete screens are rejected.

The combined candidates play a common qualification schedule, followed by separate validation and confirmation schedules. The incumbent is included in every comparison. Download best_candidate.zip and the checkpoint for review before changing the competition submission.
''' if final else f'''This notebook owns partition {index+1}: **{675 if index<2 else 674} of the 2,024 default species trios**. Run all three screen notebooks concurrently if your Kaggle account has room. The incumbent is repeated as a control. Each screen eliminates weak teams, mutates survivor moves/items/abilities/EVs/natures/order, and exports six finalists.

The first round uses eight games per candidate (four side-reversed opponent pairs per policy). Ties use remaining HP margin. This costs more than the original four-game screen and still has substantial sampling noise. It does not enumerate all possible sets.

At completion, save the output and add this notebook as an input to the final comparison notebook. Its compact redline-screen-{index+1}.zip contains data only. Downloading and re-uploading this ZIP as a dataset also works.
''')+'''
The search pauses at its time/battle budget with a checkpoint. To resume in another session, attach that checkpoint ZIP and set RESUME_ZIP. Keep profile, seed and shard identity unchanged. Only completed jobs are cached; an interrupted job may need rerunning. No competition entry is submitted.
''')
    source(1,f'''MODE = {('finalize' if final else 'screen')!r}
SHARD_INDEX = {0 if final else index}  # zero-based; do not change between resumes
SHARD_COUNT = 3
PROFILE = "full"  # use "smoke" in ALL FOUR notebooks for a setup check
MAX_HOURS = 6
MAX_GAMES = {10000 if final else 30000}
WORKERS = 2
SEED = 43179
RESUME_ZIP = ""
# Final notebook only: leave empty to detect compact screening ZIPs in /kaggle/input.
SCREENING_ZIPS = []
''')
    bootstrap=''.join(nb['cells'][2]['source'])
    bootstrap=bootstrap.replace("RESULTS = WORK / 'redline-results'", "RESULTS = WORK / ('redline-final-results' if MODE == 'finalize' else f'redline-screen-{SHARD_INDEX+1}-results')")
    source(2,bootstrap)
    source(4,'''# Independent processes inside each notebook handle the three opponent policies.
if MODE == 'finalize':
    if not SCREENING_ZIPS:
        SCREENING_ZIPS = sorted(str(p) for p in pathlib.Path('/kaggle/input').rglob('redline-screen-*.zip'))
    if len(SCREENING_ZIPS) != SHARD_COUNT:
        raise ValueError(f'Attach exactly {SHARD_COUNT} completed compact screening ZIPs; found {len(SCREENING_ZIPS)}. Set SCREENING_ZIPS explicitly if needed.')
    print('Final comparison inputs:', SCREENING_ZIPS)
command = [sys.executable, 'tools/team_search.py', '--profile', PROFILE,
           '--out', str(RESULTS), '--hours', str(MAX_HOURS), '--max-games', str(MAX_GAMES),
           '--workers', str(WORKERS), '--seed', str(SEED), '--mode', MODE,
           '--shard-index', str(SHARD_INDEX), '--shard-count', str(SHARD_COUNT)]
if MODE == 'finalize': command += ['--screening'] + SCREENING_ZIPS
try:
    subprocess.run(command, cwd=PROJECT, check=True)
finally:
    if RESULTS.exists():
        checkpoint = WORK / ('redline-final-checkpoint' if MODE == 'finalize' else f'redline-screen-{SHARD_INDEX+1}-checkpoint')
        shutil.make_archive(str(checkpoint), 'zip', RESULTS)
        print('Checkpoint saved:', str(checkpoint)+'.zip')
''')
    if final:
        # Notebook inputs contain both root output copies and results subfolders.
        # Select exact compact filenames and collapse identical copies; exclude
        # the separately named checkpoint archives entirely.
        text=''.join(nb['cells'][4]['source'])
        text=text.replace("        SCREENING_ZIPS = sorted(str(p) for p in pathlib.Path('/kaggle/input').rglob('redline-screen-*.zip'))",'''        for shard in range(1, SHARD_COUNT+1):
            name = f'redline-screen-{shard}.zip'
            copies = sorted(pathlib.Path('/kaggle/input').rglob(name), key=lambda p: (len(p.parts), str(p)))
            if not copies: continue
            fingerprints = set()
            for path in copies:
                with zipfile.ZipFile(path) as archive:
                    fingerprints.add(hashlib.sha256(archive.read('screening.json')).hexdigest())
            if len(fingerprints) != 1:
                raise ValueError(f'Multiple different copies of {name}; set SCREENING_ZIPS explicitly.')
            SCREENING_ZIPS.append(str(copies[0]))''')
        source(4,text)
    source(5,'''from IPython.display import FileLink, display
if MODE == 'screen' and (RESULTS/'screening.json').exists():
    data = json.loads((RESULTS/'screening.json').read_text())
    print('Screen complete:', data['shardIndex']+1, 'of', data['shardCount'])
    print('Default trios covered:', len(data['populationIndices']), 'completed games:', data['completedGames'])
    compact = RESULTS/f'redline-screen-{SHARD_INDEX+1}.zip'
    # Root output copies are easy to find when adding this notebook as an input.
    shutil.copyfile(compact, WORK/compact.name)
    display(FileLink(str(WORK/compact.name)))
elif (RESULTS/'result.json').exists():
    summary = json.loads((RESULTS/'result.json').read_text())
    print(summary['warning'])
    print('Selected team:', ', '.join(p['name'] for p in summary['selected']['team']))
    print(json.dumps(summary['confirmation'], indent=2))
    display(FileLink(str(RESULTS/'best_candidate.zip')))
elif (RESULTS/'status.json').exists():
    print((RESULTS/'status.json').read_text())
display(FileLink(str(checkpoint)+'.zip'))
print('Save completed output for the final notebook, or download the checkpoint to resume.')
''')
    filename='REDLINE_Final_Comparison.ipynb' if final else f'REDLINE_Screen_{index+1}.ipynb'
    path=ROOT/'notebooks'/filename
    path.write_text(json.dumps(nb,indent=1),encoding='utf-8')
    for cell in nb['cells']:
        if cell['cell_type']=='code':compile(''.join(cell['source']),filename,'exec')
    print(filename)
