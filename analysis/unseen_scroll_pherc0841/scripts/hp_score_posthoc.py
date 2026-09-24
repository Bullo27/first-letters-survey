"""hp_score_posthoc.py: POST-HOC (2026-09-24, after the Discord survey; not in PLAN.md). Chris Scheirer's letter-scale
score (github.com/ShribyrLabs/vesuvius-reports, 02-9um-ink-reader-benchmark/scripts/hp_score.py, MIT; same constants
and functions) applied to our arm A maps of the three PHerc0841 team segments. Plain correlation cannot tell letters
from smudge; the score removes a 48 um blur from both maps and correlates what is left.
Key: the team's 2.403 um ink prediction (ink-detection/*.tif, 16460 x 18560 for w00), area-averaged onto our 9.366 um
render grid (both tifxyz meshes are 20 px per grid cell over the same surface, so full extent maps to full extent).
Alignment is checked before scoring: phase correlation of 100 um-smoothed maps in 512 px tiles.
Writes hp_score_posthoc.json."""
import glob, io, json, os
import numpy as np, cv2, tifffile, zarr, s3fs
from scipy.ndimage import gaussian_filter
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
SIG, SMO = 20 / 3.9, 40 / 3.9              # as in hp_score.py: 48 um high-pass, 100 um "inked" smoothing (9.36 um px)
def hp(img, m):                            # hp_score.py, verbatim
    w = gaussian_filter(m.astype(np.float32), SIG)
    return img - gaussian_filter(img * m, SIG) / np.maximum(w, 1e-3)
def r(a, b): return float(np.corrcoef(a, b)[0, 1])
fs = s3fs.S3FileSystem(anon=True)
out = {}
for seg in sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(f'{T}/armA/*/')):
    d = f'{T}/armA/{seg}'; loc = f'{d}/team_ink_2403um.tif'
    if not os.path.exists(loc):
        src = [q for q in fs.ls(f'vesuvius-challenge-open-data/PHerc0841/segments/{seg}/ink-detection') if q.endswith('.tif')][0]
        fs.get(src, loc)
    z = zarr.open(f'{d}/sv.zarr', mode='r'); z = z['0'] if '0' in z else z; H, W = z.shape[1:]
    valid = np.asarray(z[z.shape[0] // 2]) > 0
    team = tifffile.imread(loc)
    key = cv2.resize(team, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
    # team coverage: its 2.403 um mesh validity, brought to our grid (20 px per grid cell there as here)
    tx = tifffile.imread(io.BytesIO(fs.cat(f'vesuvius-challenge-open-data/PHerc0841/segments/{seg}/mesh/'
                                           f'{seg.split("-", 1)[0]}-on-20260319124803-2.403um.tifxyz/x.tif')))
    tvalid = cv2.resize((tx > 0).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    valid &= tvalid
    core = valid & (gaussian_filter(valid.astype(np.float32), 2 * SIG) > 0.999)
    kh, inked = hp(key, valid), gaussian_filter(key, SMO) > 60
    # alignment check on the 14-checkpoint forward mean
    ref = tifffile.imread(f'{d}/mean14_forward.tif').astype(np.float32)
    a, b = gaussian_filter(ref, SMO), gaussian_filter(key, SMO); shifts = []
    for y in range(0, H - 512, 512):
        for x in range(0, W - 512, 512):
            if core[y:y + 512, x:x + 512].mean() < 0.9: continue
            (dx, dy), resp = cv2.phaseCorrelate(a[y:y + 512, x:x + 512].astype(np.float64), b[y:y + 512, x:x + 512].astype(np.float64))
            if resp > 0.05: shifts.append((dy, dx, resp))
    sh = np.array(shifts) if shifts else np.zeros((0, 3))
    R = out.setdefault(seg, {'grid': [H, W], 'team_tif': list(team.shape), 'core_px': int(core.sum()), 'inked_px': int((core & inked).sum()),
                             'align_tiles': len(sh), 'align_median_dy_dx_px': [round(float(np.median(sh[:, 0])), 2), round(float(np.median(sh[:, 1])), 2)] if len(sh) else None,
                             'align_p90_abs_px': round(float(np.percentile(np.abs(sh[:, :2]), 90)), 2) if len(sh) else None, 'maps': {}})
    names = {'s42_75k_fwd': 'ink_hybrid_3d2d-seed42_step-075000_forward.tif', 's43_20k_fwd': 'ink_hybrid_3d2d-seed43_step-020000_forward.tif',
             'mean2_fwd': 'mean2_forward.tif', 'mean14_fwd': 'mean14_forward.tif', 'mean2_rev': 'mean2_reverse.tif', 'mean14_rev': 'mean14_reverse.tif'}
    for tag, fn in names.items():
        p = tifffile.imread(f'{d}/{fn}').astype(np.float32)[:H, :W]
        m = core & (p > 0); ph = hp(p, m)
        null = max(abs(r(ph[m & np.roll(m, s, 0)], np.roll(kh, s, 0)[m & np.roll(m, s, 0)])) for s in (150, 300, -300))
        R['maps'][tag] = {'raw_r': round(r(p[m], key[m]), 3), 'hp_r': round(r(ph[m], kh[m]), 3),
                          'inked_hp_r': round(r(ph[m & inked], kh[m & inked]), 3), 'null_max_abs': round(null, 3)}
        print(seg[-12:], tag, R['maps'][tag], flush=True)
    print(seg[-12:], {k: v for k, v in R.items() if k != 'maps'}, flush=True)
    json.dump(out, open(f'{T}/hp_score_posthoc.json', 'w'), indent=1)
