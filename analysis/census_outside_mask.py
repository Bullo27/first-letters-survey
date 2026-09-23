"""census_outside_mask.py: for every First Letters volume, the share of the m7 surface prediction's lit samples
(level 5, i.e. every 32nd voxel) that fall where the masked scan is 0, i.e. outside the papyrus.
Uses the volume catalog of fls.py (in the parent directory). Output: one line per volume, then a JSON summary."""
import concurrent.futures as cf, json, os, sys
import numpy as np, zarr
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fls

def one(scroll):
    r = fls.scroll_info(scroll); so = {'anon': True}
    scan = zarr.open('s3://vesuvius-challenge-open-data/' + r['scan'].rstrip('/'), mode='r', storage_options=so)['5']
    pred = zarr.open_group('s3://vesuvius-challenge-open-data/' + r['prediction'].rstrip('/'), mode='r', storage_options=so)['5']
    s, p = np.asarray(scan[:]), np.asarray(pred[:])
    z, y, x = (min(a, b) for a, b in zip(s.shape, p.shape))
    s, p = s[:z, :y, :x], p[:z, :y, :x]
    lit = p > 127; outside = lit & (s == 0)
    return {'scroll': scroll, 'volume': r['volume'], 'lit': int(lit.sum()), 'outside_mask': int(outside.sum()),
            'share_outside': round(float(outside.sum() / max(1, lit.sum())), 4)}

if __name__ == '__main__':
    fls.scroll_info(next(iter(json.loads(fls.get(fls.ELIGIBILITY))['first-letters-2027']))['scroll'])   # builds the catalog
    scrolls = list(json.load(open(os.path.join(fls.WORK, 'catalog.json'))))
    res = []
    with cf.ThreadPoolExecutor(6) as ex:
        for d in ex.map(one, scrolls):
            res.append(d); print(f"{d['scroll']:11s} lit {d['lit']:>9d}  outside the mask {d['outside_mask']:>9d}  share {d['share_outside']:.3f}", flush=True)
    shares = sorted(d['share_outside'] for d in res)
    print(json.dumps({'volumes': len(res), 'min': shares[0], 'median': shares[len(shares) // 2], 'max': shares[-1]}))
