"""background_check.py: the relative check of villa PR #1906 (head 3787b68f1) on the survey patches.

At 3787b68f1 the tracer also warns when a surface's on-prediction support is at or below a background rate: the same
fraction over 2000 uniform random points in the bounding box of the valid vertices, dilated by 64 voxels and clamped to
the volume (vc_grow_seg_from_seed.cpp, noBetterThanChance() in SurfaceSupport.hpp). For every patch in
results/segments/ this counts (a) how many distinct level-0 chunks 2000 such points fall in, and how many of those
contain a vertex of the surface (geometry only, nothing fetched), and (b) the background rate itself, estimated from
N_SAMPLE uniform points in the same box (fetched from the bucket like support_check.py), compared with the support
in support_check.json. Uniform points come from numpy's generator, not the tracer's std::mt19937(42), so (b) is an
estimate of the tracer's number, not a copy of it.
Output: background_check.json next to this script.
"""
import json, os, sys, time
import numpy as np, tifffile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import support_check as SC

N_TRACER, DILATE = 2000, 64.0
N_SAMPLE = int(os.environ.get('N_SAMPLE', 500))


def box(P, valid, shape_zyx):
    """The tracer's neighbourhood: bounds of the valid vertices (x, y, z), dilated and clamped to the volume."""
    q = P[valid]
    lo = np.maximum(0.0, q.min(0) - DILATE)
    hi = np.minimum(np.array(shape_zyx[::-1], float), q.max(0) + DILATE)
    return lo, hi


if __name__ == '__main__':
    R = json.load(open(os.path.join(SC.REPO, 'results', 'results.json')))
    S = json.load(open(os.path.join(HERE, 'support_check.json')))['patches']
    want = set(sys.argv[1:])
    out_path = os.path.join(HERE, 'background_check.json')
    res = json.load(open(out_path)) if os.path.exists(out_path) else {'n_sample': N_SAMPLE, 'patches': {}}
    for p in R['patches']:
        k = SC.key_of(p)
        if (want and S[k]['group'] not in want) or k in res['patches']:
            continue
        t = time.time()
        vol = SC.Level0(SC.PRED[p['volume']]['surface_prediction'])
        P = np.stack([tifffile.imread(os.path.join(SC.REPO, p['tifxyz'], f'{c}.tif')).astype(np.float64) for c in 'xyz'], -1)
        valid = ~(P == -1).any(-1) & np.isfinite(P).all(-1)
        lo, hi = box(P, valid, vol.shape)
        ch = np.array(vol.ch)
        surface_chunks = {tuple(c) for c in np.unique(SC.lround(P[valid][:, ::-1]) // ch, axis=0)}
        rng = np.random.default_rng(0)
        pts = rng.uniform(lo, hi, size=(N_TRACER, 3))                   # x, y, z like the tracer
        tracer_chunks = {tuple(c) for c in np.unique(SC.lround(pts[:, ::-1]) // ch, axis=0)}
        sample = rng.uniform(lo, hi, size=(N_SAMPLE, 3))
        v, _ = vol.sample(SC.lround(sample[:, ::-1]))
        bg = 100 * float((v != 0).mean())
        r = {'group': S[k]['group'], 'support_pct': S[k]['support_pct'], 'box_voxels_xyz': (hi - lo).round().tolist(),
             'chunks_hit_by_2000_points': len(tracer_chunks),
             'of_which_contain_a_surface_vertex': len(tracer_chunks & surface_chunks),
             'surface_chunks': len(surface_chunks), 'box_background_pct_est': round(bg, 1),
             'support_at_or_below_box_background': S[k]['support_pct'] <= bg}
        res['patches'][k] = r
        json.dump(res, open(out_path, 'w'), indent=1)
        print(f"{k}: support {r['support_pct']} % vs box background ~{r['box_background_pct_est']} % | 2000 points -> "
              f"{r['chunks_hit_by_2000_points']} chunks, {r['of_which_contain_a_surface_vertex']} with a surface vertex "
              f"(surface crosses {r['surface_chunks']}) | {time.time() - t:.0f}s | {r['group']}", flush=True)
