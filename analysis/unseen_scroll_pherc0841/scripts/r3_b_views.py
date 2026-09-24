"""r3_b_views.py B2_<seg> ...: display-only companion of score_b.py for R3 step 2 on arm B2 patches (added 2026-09-24
after the freeze). Uses score_b.py's own functions to carry the team's ink map onto our render grid (2x downsampled) and
writes, in the patch folder: r3b_team_carried.png (team map where our surface lies within 5 vox of the team sheet,
dimmed elsewhere), r3b_ours_fwd.png (our forward mean, same grid and contrast as the survey QA), r3b_dist.png (distance
to the team sheet, 0 vox white -> 30+ vox black)."""
import glob, os, sys
import numpy as np, cv2, tifffile, zarr
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
src = open(f'{T}/score_b.py').read().split("if '--geometry-check' in sys.argv:")[0]
ns = {}; exec(compile(src, 'score_b_defs', 'exec'), ns)
VX = ns['VX']
for job in sys.argv[1:]:
    out = f'{T}/fls_work/patches/PHerc0841/{job}'; seg = ns['TEAM'][job[3:]]
    tree, tys, txs, tv = ns['team_tree'](seg)
    P, v = ns['load_mesh'](sorted(glob.glob(f'{out}/auto_grown_*'))[-1])
    z = zarr.open(f'{out}/surface_volume.zarr', mode='r'); z0 = z['0'] if '0' in z else z; H, W = z0.shape[1:]
    mid = np.asarray(z0[z0.shape[0] // 2])[::2, ::2] > 0
    Q, ok, _, _ = ns['densify'](P, v, 10)
    Qs = cv2.resize(Q, (W // 2, H // 2), interpolation=cv2.INTER_LINEAR)
    oks = cv2.resize(ok.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_NEAREST) > 0
    dd, ii = tree.query(Qs.reshape(-1, 3)); dd = dd.reshape(H // 2, W // 2); ii = ii.reshape(H // 2, W // 2)
    jpg = cv2.imread(f'{T}/ground_truth/{seg}_team_ink_ds8.jpg', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    sc = 20 * VX / 19.224
    tmap = cv2.remap(jpg, (txs[ii] * sc).astype(np.float32), (tys[ii] * sc).astype(np.float32), cv2.INTER_LINEAR)
    overlap = oks & mid & (dd <= 5)
    m = tifffile.imread(f'{out}/ink_mean_forward.tif').astype(np.float32); m = m / 255 if m.max() > 1.5 else m
    ms = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    k = 1400 / max(H // 2, W // 2)
    def save(img, name):
        cv2.imwrite(f'{out}/{name}', cv2.resize(img, (int(W // 2 * k), int(H // 2 * k)), interpolation=cv2.INTER_AREA))
    save((np.where(overlap, tmap, tmap * 0.25) * 255).astype(np.uint8), 'r3b_team_carried.png')
    save((np.clip((ms - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8), 'r3b_ours_fwd.png')
    save((np.clip(1 - dd / 30, 0, 1) * 255 * oks).astype(np.uint8), 'r3b_dist.png')
    ys, xs = np.nonzero(overlap)
    print(job, 'overlap px', int(overlap.sum()), 'bbox (display px) x', int(xs.min() * k), int(xs.max() * k), 'y', int(ys.min() * k), int(ys.max() * k))
