"""blur_matched.py: POST-HOC (2026-09-27). Chris Scheirer's caveat in our #robots thread (2026-09-26 19:05Z): hp r rises
when a read is blurrier, so part of the 14-checkpoint mean's lift may be smoothing. His control: blur both reads by the
same Gaussian (2 and 4 px), leave the key as is, score them on the same pixels. Same key, masks and hp() as
hp_score_posthoc.py; one common pixel set for every map of a segment; blur = masked (normalised) Gaussian inside the
maps' support, so no zeros from outside the mesh are mixed in. Sigma 0 must reproduce hp_score_posthoc.json.
Writes blur_matched.json."""
import glob, io, json, os
import numpy as np, cv2, tifffile, zarr, s3fs
from scipy.ndimage import gaussian_filter
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
SIG, SMO = 20 / 3.9, 40 / 3.9              # as in hp_score.py / hp_score_posthoc.py
BLURS = [0, 1, 2, 3, 4, 6, 8]              # px (9.366 um); 2 and 4 = his protocol, the rest to locate each map's optimum
def r(a, b): return float(np.corrcoef(a, b)[0, 1])
fs = s3fs.S3FileSystem(anon=True)
out = {}
for seg in sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(f'{T}/armA/*/')):
    d = f'{T}/armA/{seg}'
    z = zarr.open(f'{d}/sv.zarr', mode='r'); z = z['0'] if '0' in z else z; H, W = z.shape[1:]
    valid = np.asarray(z[z.shape[0] // 2]) > 0
    key = cv2.resize(tifffile.imread(f'{d}/team_ink_2403um.tif'), (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
    tx = tifffile.imread(io.BytesIO(fs.cat(f'vesuvius-challenge-open-data/PHerc0841/segments/{seg}/mesh/'
                                           f'{seg.split("-", 1)[0]}-on-20260319124803-2.403um.tifxyz/x.tif')))
    valid &= cv2.resize((tx > 0).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    core = valid & (gaussian_filter(valid.astype(np.float32), 2 * SIG) > 0.999)
    kw = gaussian_filter(valid.astype(np.float32), SIG)
    kh = key - gaussian_filter(key * valid, SIG) / np.maximum(kw, 1e-3)          # hp(key, valid)
    files = sorted(glob.glob(f'{d}/ink_hybrid_3d2d-*_forward.tif')) + [f'{d}/mean2_forward.tif', f'{d}/mean14_forward.tif']
    maps = {os.path.basename(f).replace('ink_hybrid_3d2d-', '').replace('_forward.tif', ''): tifffile.imread(f).astype(np.float32)[:H, :W] for f in files}
    supp = valid.copy()
    for p in maps.values(): supp &= p > 0
    M = core & supp                                                               # the same pixels for every map
    Mf, Sf = M.astype(np.float32), supp.astype(np.float32)
    mw = np.maximum(gaussian_filter(Mf, SIG), 1e-3)
    R = out.setdefault(seg, {'grid': [H, W], 'core_px': int(core.sum()), 'common_px': int(M.sum()), 'hp_r': {}, 'null_max_abs': {}})
    sw = {s: np.maximum(gaussian_filter(Sf, s), 1e-3) for s in BLURS if s}
    for tag, p in maps.items():
        R['hp_r'][tag] = {}
        for s in BLURS:
            pb = p if s == 0 else np.where(supp, gaussian_filter(p * Sf, s) / sw[s], 0)
            ph = pb - gaussian_filter(pb * Mf, SIG) / mw                           # hp(pb, M)
            R['hp_r'][tag][s] = round(r(ph[M], kh[M]), 4)
            if tag in ('seed42_step-075000', 'seed43_step-020000', 'mean2', 'mean14') and s in (0, 2, 4):
                R['null_max_abs'].setdefault(tag, {})[s] = round(max(abs(r(ph[M & np.roll(M, k, 0)], np.roll(kh, k, 0)[M & np.roll(M, k, 0)])) for k in (150, 300, -300)), 4)
        print(seg[-12:], tag, R['hp_r'][tag], flush=True)
    json.dump(out, open(f'{T}/blur_matched.json', 'w'), indent=1)
print('done', flush=True)
