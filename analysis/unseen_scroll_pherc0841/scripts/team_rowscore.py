"""team_rowscore.py [segment ...]: POST-HOC calibration (added 2026-09-24 after the first arm A readouts, not part of
the pre-registered criteria): the survey's row score (fl_survey/rowscore.py) of the TEAM's ink map on our render grid.
If the team's own map scores <= 28.7 on a segment, R1 > 28.7 is not reachable there even with a perfect ink map.
Writes armA/<seg>/team_on_our_grid.tif and team_rowscore.json."""
import glob, json, os, subprocess, sys
import numpy as np, cv2, tifffile, zarr
T = '/media/bullo/Storage/vesuvius_work/unseen_test'; FS = '/media/bullo/Storage/vesuvius_work/fl_survey'; VX = 9.366
segs = sys.argv[1:] or sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(f'{T}/armA/*/') if os.path.exists(f'{d}/sv.zarr/.zattrs'))
out = json.load(open(f'{T}/team_rowscore.json')) if os.path.exists(f'{T}/team_rowscore.json') else {}
for seg in segs:
    sv = f'{T}/armA/{seg}/sv.zarr'; z = zarr.open(sv, mode='r'); z = z['0'] if '0' in z else z; H, W = z.shape[1:]
    tj = cv2.imread(f'{T}/ground_truth/{seg}_team_ink_ds8.jpg', cv2.IMREAD_GRAYSCALE)
    p = f'{T}/armA/{seg}/team_on_our_grid.tif'; tifffile.imwrite(p, cv2.resize(tj, (W, H), interpolation=cv2.INTER_LINEAR))
    o = subprocess.run(['/home/bullo/vesuvius-work/venv/bin/python', f'{FS}/rowscore.py', p, str(VX), sv], capture_output=True, text=True)
    out[seg] = json.loads(o.stdout.strip().splitlines()[-1]) if o.stdout.strip() else {'error': o.stderr[-500:]}
    print(seg, out[seg], flush=True)
json.dump(out, open(f'{T}/team_rowscore.json', 'w'), indent=1)
