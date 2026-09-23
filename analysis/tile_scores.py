"""tile_scores.py <pred.tif> <voxel_um> [area_cm2=6] [sv.zarr]: row scores of non-overlapping square tiles of equal
physical area (tiles need >= 70 % valid surface), so patches of different size compare fairly."""
import sys, json, os, subprocess, tempfile, numpy as np, tifffile
HERE = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
src, vx = sys.argv[1], float(sys.argv[2]); area = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
a = np.asarray(tifffile.imread(src)); a = a[..., 0] if a.ndim == 3 else a
valid = a > (2 if a.dtype == np.uint8 else 0.01)
if len(sys.argv) > 4:
    import zarr
    z = zarr.open(sys.argv[4], mode='r'); z0 = z['0'] if hasattr(z, 'keys') and '0' in z else z
    valid = np.asarray(z0[z0.shape[0] // 2]) > 0
side = int(round((area ** 0.5) / (vx * 1e-4)))
out = []
with tempfile.TemporaryDirectory() as td:
    for y in range(0, a.shape[0] - side + 1, side):
        for x in range(0, a.shape[1] - side + 1, side):
            if valid[y:y + side, x:x + side].mean() < 0.7: continue
            t_ = a[y:y + side, x:x + side].copy(); t_[~valid[y:y + side, x:x + side]] = 0
            f = os.path.join(td, 't.tif'); tifffile.imwrite(f, t_)
            o = subprocess.run([PY, os.path.join(HERE, 'rowscore.py'), f, str(vx)], capture_output=True, text=True).stdout.strip().splitlines()
            r = json.loads(o[-1]) if o else {}
            if r.get('score') is not None: out.append({'y': y, 'x': x, 'score': r['score'], 'period_mm': r['period_mm'], 'angle': r['angle_deg']})
print(json.dumps({'src': src, 'tile_px': side, 'area_cm2': area, 'n': len(out), 'scores': sorted([t['score'] for t in out], reverse=True), 'tiles': out}))
