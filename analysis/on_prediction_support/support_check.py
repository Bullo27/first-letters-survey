"""support_check.py: on-prediction support of the survey patches, the check villa PR #1906 adds to the tracer.

villa #1906 (head 562105e8a) makes vc_grow_seg_from_seed report, after growth, the fraction of valid vertices (no
coordinate == -1) whose rounded (z, y, x) lands on a nonzero voxel of level 0 of the prediction the surface was grown
from, and warn below 0.5 (SurfaceSupport.hpp). This applies the same rule to our 65 patches (results/segments/,
grown from the published L0 m7 surface predictions listed in predictions.json) and adds what the rule does not look
at: the same hit rate 1-8 voxels either side of the surface along its normal, and the rate at random voxels of the
chunks the patch crosses (background). Each patch keeps its by-eye surface verdict from results.json.
Chunks come from the open-data bucket and are kept under $FLS_WORK/prediction_chunks (default ./fls_work).
Output: support_check.json next to this script.
"""
import json, os, statistics, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np, numcodecs, tifffile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BUCKET = 'https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/'
CHUNKS = os.path.join(os.path.abspath(os.environ.get('FLS_WORK', 'fls_work')), 'prediction_chunks')
PRED = json.load(open(os.path.join(HERE, 'predictions.json')))
OFFSETS = range(-8, 9)                 # voxels along the surface normal
N_BACKGROUND = 200_000


def fetch(url, tries=5):
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None                                  # no such chunk in the bucket: fill value
            err = e
        except Exception as e:
            err = e
        time.sleep(2 * (t + 1))
    raise RuntimeError(f'{url}: {err}')


def lround(a):
    """C's lround: halves away from zero."""
    return (np.sign(a) * np.floor(np.abs(a) + 0.5)).astype(np.int64)


class Level0:
    """Level 0 of a prediction zarr, read chunk by chunk."""
    def __init__(self, pred):
        self.pred = pred
        za = json.loads(self.raw('.zarray'))
        assert za['dtype'] == '|u1' and za['filters'] is None and za.get('dimension_separator') == '/', za
        self.shape, self.ch, self.fill = za['shape'], za['chunks'], za['fill_value']
        self.codec = numcodecs.get_codec(za['compressor'])

    def raw(self, key):
        f = os.path.join(CHUNKS, self.pred, '0', *key.split('/'))
        if not os.path.exists(f):
            b = fetch(BUCKET + self.pred + '/0/' + key)
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, 'wb').write(b if b is not None else b'')  # empty file = absent from the bucket
        b = open(f, 'rb').read()
        return b if b else None

    def sample(self, zyx):
        """Values at integer (z, y, x) rows; 0 outside the volume, like the bounds check in #1906."""
        out = np.zeros(len(zyx), np.uint8)
        inb = np.all((zyx >= 0) & (zyx < np.array(self.shape)), axis=1)
        idx = np.nonzero(inb)[0]
        ck = zyx[idx] // np.array(self.ch)
        order = np.lexsort((ck[:, 2], ck[:, 1], ck[:, 0]))
        idx, ck = idx[order], ck[order]
        cuts = np.nonzero(np.any(np.diff(ck, axis=0) != 0, axis=1))[0] + 1
        groups = np.split(np.arange(len(idx)), cuts)
        keys = [tuple(ck[g[0]]) for g in groups if len(g)]
        with ThreadPoolExecutor(16) as ex:                   # fetch in parallel, decode one chunk at a time
            raws = ex.map(lambda k: self.raw('/'.join(map(str, k))), keys)
            for k, g, b in zip(keys, [g for g in groups if len(g)], raws):
                ii = idx[g]
                if b is None:
                    out[ii] = self.fill
                    continue
                a = np.frombuffer(self.codec.decode(b), np.uint8).reshape(self.ch)
                loc = zyx[ii] - np.array(k) * np.array(self.ch)
                out[ii] = a[loc[:, 0], loc[:, 1], loc[:, 2]]
        return out, keys


def check(tifxyz, pred, seed=0):
    P = np.stack([tifffile.imread(f'{tifxyz}/{c}.tif').astype(np.float64) for c in 'xyz'], -1)   # (rows, cols, x y z)
    valid = ~(P == -1).any(-1)
    vol = Level0(pred)
    # 1. the rule of #1906: every valid vertex, rounded, nonzero at level 0
    zyx = lround(P[valid][:, ::-1])
    inb = np.all((zyx >= 0) & (zyx < np.array(vol.shape)), axis=1)
    keys = np.unique(zyx[inb] // np.array(vol.ch), axis=0)
    # 2. the same along the normal (central differences; interior vertices whose four neighbours are valid)
    inner = np.zeros_like(valid)
    inner[1:-1, 1:-1] = valid[1:-1, 1:-1] & valid[:-2, 1:-1] & valid[2:, 1:-1] & valid[1:-1, :-2] & valid[1:-1, 2:]
    du = P[1:-1, 2:] - P[1:-1, :-2]
    dv = P[2:, 1:-1] - P[:-2, 1:-1]
    n = np.zeros_like(P)
    n[1:-1, 1:-1] = np.cross(du, dv)
    norm = np.linalg.norm(n, axis=-1)
    ok = inner & (norm > 0)
    q, nq = P[ok], n[ok] / norm[ok][:, None]
    # 3. background: uniform random voxels inside the chunks the valid vertices fall in
    rng = np.random.default_rng(seed)
    kk = keys[rng.integers(0, len(keys), N_BACKGROUND)]
    bg = kk * np.array(vol.ch) + np.stack([rng.integers(0, c, N_BACKGROUND) for c in vol.ch], 1)
    parts = [zyx] + [lround((q + k * nq)[:, ::-1]) for k in OFFSETS] + [bg]
    vals, _ = vol.sample(np.concatenate(parts))              # one pass: every chunk decoded once
    vals = np.split(vals != 0, np.cumsum([len(a) for a in parts])[:-1])
    on, total = int(vals[0].sum()), int(valid.sum())
    profile = {k: round(100 * float(v.mean()), 1) for k, v in zip(OFFSETS, vals[1:-1])}
    vb = vals[-1]
    off = [profile[k] for k in (-8, -7, -6, -5, 5, 6, 7, 8)]
    return {'on': on, 'total': total, 'support_pct': round(100 * on / total, 1) if total else 100.0,
            'n_profile_vertices': int(ok.sum()), 'profile_pct_by_normal_offset': profile,
            'surface_minus_5_to_8_voxels_off': round(profile[0] - sum(off) / len(off), 1),
            'background_pct': round(100 * float(vb.mean()), 1), 'chunks': len(keys)}


def category(label):
    """Our by-eye verdict on the render, in four groups."""
    l = label.lower()
    if l.startswith('escapes'):
        return 'escapes the papyrus'
    if l.startswith('follows the sheet throughout'):
        return 'follows the sheet throughout'
    on_sheet = any(s in l for s in ('on the sheet', 'on-sheet', 'follows the sheet', 'crosshatch', 'arcs along the layers'))
    return 'partly on the sheet' if on_sheet else 'swirls, no on-sheet part'


def key_of(p):
    return f"{p['pass']}/{p['scroll']}/{os.path.basename(p['tifxyz']).split('_')[-1].replace('.tifxyz', '')}"


if __name__ == '__main__':
    R = json.load(open(os.path.join(REPO, 'results', 'results.json')))
    out_path = os.path.join(HERE, 'support_check.json')
    res = json.load(open(out_path)) if os.path.exists(out_path) else {'patches': {}}
    for p in R['patches']:
        k = key_of(p)
        if k in res['patches']:
            continue
        t = time.time()
        r = check(os.path.join(REPO, p['tifxyz']), PRED[p['volume']]['surface_prediction'])
        r.update(scroll=p['scroll'], surface=p['visual_qa']['surface'], group=category(p['visual_qa']['surface']))
        res['patches'][k] = r
        json.dump(res, open(out_path, 'w'), indent=1)
        print(f"{k}: {r['support_pct']}% ({r['on']}/{r['total']}), off-surface contrast {r['surface_minus_5_to_8_voxels_off']}, "
              f"background {r['background_pct']}%, {time.time() - t:.0f}s | {r['surface']}", flush=True)
    groups = {}
    for r in res['patches'].values():
        groups.setdefault(r['group'], []).append(r)
    res['groups'] = {}
    for g, rs in sorted(groups.items()):
        s = [r['support_pct'] for r in rs]
        c = [r['surface_minus_5_to_8_voxels_off'] for r in rs]
        b = [r['background_pct'] for r in rs]
        res['groups'][g] = {'n': len(rs), 'support_pct_min_median_max': [min(s), statistics.median(s), max(s)],
                            'n_below_50': sum(x < 50 for x in s),
                            'contrast_min_median_max': [min(c), statistics.median(c), max(c)],
                            'background_pct_min_max': [min(b), max(b)]}
        print(g, res['groups'][g])
    json.dump(res, open(out_path, 'w'), indent=1)
