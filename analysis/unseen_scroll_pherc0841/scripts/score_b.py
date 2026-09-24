"""score_b.py [job ...] | --geometry-check: arm B readouts of PLAN.md for patches grown by arm_b.py.
  R1 row score of each map (fl_survey/rowscore.py on fls.py's ink_mean_{forward,reverse}.tif and single maps)
  B2 only: (i) distance from our surface to the team mesh of the seed's segment (point-to-surface, the team grid
  densified 10x); on the sheet = median <= 5 voxels over the overlap. (ii) R2: the team's ink map carried onto our
  render grid through the geometry (our pixel -> 3D point -> nearest team surface point -> team map), correlated with
  our map on the overlap (0.5 mm smoothing) against shifted-map nulls, as in arm A.
--geometry-check: runs the distance code on two team meshes (w00 against ag896) to validate it on known surfaces."""
import glob, json, os, subprocess, sys
import numpy as np, tifffile, cv2
from scipy.spatial import cKDTree
T = '/media/bullo/Storage/vesuvius_work/unseen_test'; FS = '/media/bullo/Storage/vesuvius_work/fl_survey'; VX = 9.366
TEAM = {'w00': '20260220213127-w00', 'ag896': '20260220214732-auto_grown_20260220144552896', 'ag405': '20260221022814-auto_grown_20260220174252405'}

def load_mesh(d):
    X, Y, Z = (tifffile.imread(os.path.join(d, f'{c}.tif')).astype(np.float32) for c in 'xyz')
    return np.stack([X, Y, Z], -1), (X > 0) & (Y > 0) & (Z > 0)
def densify(P, valid, f):
    """Bilinear upsampling of the grid by f; points whose 4 neighbours are not all valid are dropped."""
    h, w = valid.shape; H, W = (h - 1) * f + 1, (w - 1) * f + 1
    ys, xs = np.meshgrid(np.linspace(0, h - 1, H), np.linspace(0, w - 1, W), indexing='ij')
    y0, x0 = np.clip(ys.astype(int), 0, h - 2), np.clip(xs.astype(int), 0, w - 2); fy, fx = (ys - y0)[..., None], (xs - x0)[..., None]
    ok = valid[y0, x0] & valid[y0 + 1, x0] & valid[y0, x0 + 1] & valid[y0 + 1, x0 + 1]
    Q = (P[y0, x0] * (1 - fy) * (1 - fx) + P[y0 + 1, x0] * fy * (1 - fx) + P[y0, x0 + 1] * (1 - fy) * fx + P[y0 + 1, x0 + 1] * fy * fx)
    return Q, ok, ys, xs
def team_tree(seg):
    P, v = load_mesh(f'{T}/team_meshes/{seg}/tifxyz'); Q, ok, ys, xs = densify(P, v, 10)
    return cKDTree(Q[ok]), ys[ok], xs[ok], v
def rowscore(tif, sv):
    o = subprocess.run(['/home/bullo/vesuvius-work/venv/bin/python', f'{FS}/rowscore.py', tif, str(VX), sv], capture_output=True, text=True).stdout.strip()
    return json.loads(o.splitlines()[-1]) if o else None

if '--geometry-check' in sys.argv:
    tree, _, _, _ = team_tree(TEAM['w00'])
    P, v = load_mesh(f'{T}/team_meshes/{TEAM["ag896"]}/tifxyz'); d, _ = tree.query(P[v])
    print(f'ag896 grid points -> w00 surface: median {np.median(d):.2f} vox, p10 {np.percentile(d, 10):.2f}, share <= 5 vox {np.mean(d <= 5):.3f}, n {len(d)}')
    P, v = load_mesh(f'{T}/team_meshes/{TEAM["w00"]}/tifxyz'); d, _ = tree.query(P[v])
    print(f'w00 grid points -> w00 surface (self, must be ~0): median {np.median(d):.3f} vox, max {d.max():.3f}')
    sys.exit(0)

res_path = f'{T}/armB_results.json'; res = json.load(open(res_path)) if os.path.exists(res_path) else {}
jobs = [a for a in sys.argv[1:]] or sorted(os.path.basename(p) for p in glob.glob(f'{T}/fls_work/patches/PHerc0841/*'))
for job in jobs:
    out = f'{T}/fls_work/patches/PHerc0841/{job}'; sv = f'{out}/surface_volume.zarr'; R = res.setdefault(job, {})
    segs = sorted(glob.glob(f'{out}/auto_grown_*'))
    if not segs or not os.path.exists(f'{sv}/.zattrs'): print(job, 'not ready'); continue
    maps = sorted(glob.glob(f'{out}/ink_*.tif'))
    R['row'] = {os.path.basename(m): rowscore(m, sv) for m in maps}
    R['area_cm2'] = json.load(open(f'{segs[-1]}/meta.json')).get('area_cm2')
    if job.startswith('B2_'):
        seg = TEAM[job[3:]]; tree, tys, txs, tv = team_tree(seg)
        P, v = load_mesh(segs[-1]); d, _ = tree.query(P[v]); near = d <= 60          # overlap: within 60 vox of the team surface
        R['dist_vox'] = {'median_overlap': float(np.median(d[near])) if near.any() else None, 'share_le5': float(np.mean(d <= 5)),
                         'share_overlap': float(near.mean()), 'n': int(len(d))}
        R['on_sheet'] = bool(near.any() and np.median(d[near]) <= 5)
        # carry the team map onto our render grid (downsampled 2x for speed)
        import zarr
        z = zarr.open(sv, mode='r'); z0 = z['0'] if '0' in z else z; H, W = z0.shape[1:]; mid = np.asarray(z0[z0.shape[0] // 2])[::2, ::2] > 0
        gh, gw = v.shape
        Q, ok, _, _ = densify(P, v, 10)                                   # our grid at 2 vox spacing (render px = grid/20)
        Qs = cv2.resize(Q, (W // 2, H // 2), interpolation=cv2.INTER_LINEAR); oks = cv2.resize(ok.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_NEAREST) > 0
        dd, ii = tree.query(Qs.reshape(-1, 3)); dd = dd.reshape(H // 2, W // 2); ii = ii.reshape(H // 2, W // 2)
        jpg = cv2.imread(f'{T}/ground_truth/{seg}_team_ink_ds8.jpg', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
        sc = 20 * VX / 19.224                                              # team grid index -> jpg pixel
        tmap = cv2.remap(jpg, (txs[ii] * sc).astype(np.float32), (tys[ii] * sc).astype(np.float32), cv2.INTER_LINEAR)
        overlap = oks & mid & (dd <= 5)
        sig = 500 / (2 * VX)
        tms = cv2.GaussianBlur(np.where(overlap, tmap, 0).astype(np.float32), (0, 0), sig)
        shifts = [(int(round(dy * dist / (2 * VX))), int(round(dx * dist / (2 * VX)))) for dist in (10000, 20000) for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        R['r_team'] = {}
        for name in ('ink_mean_forward.tif', 'ink_mean_reverse.tif'):
            if not os.path.exists(f'{out}/{name}'): continue
            m = tifffile.imread(f'{out}/{name}').astype(np.float32); m = m / 255 if m.max() > 1.5 else m
            ms = cv2.GaussianBlur(cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_AREA), (0, 0), sig)
            def r_of(t, k):
                return float(np.corrcoef(ms[k], t[k])[0, 1]) if k.sum() > 1000 else None
            null = [r_of(np.roll(tms, s, axis=(0, 1)), overlap & np.roll(overlap, s, axis=(0, 1))) for s in shifts]
            null = [x for x in null if x is not None]
            R['r_team'][name] = {'r': r_of(tms, overlap), 'r_null_max': max(null) if null else None, 'overlap_px': int(overlap.sum())}
    print(job, json.dumps(R)[:600]); json.dump(res, open(res_path, 'w'), indent=1)
