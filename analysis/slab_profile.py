"""slab_profile.py <sv.zarr> [...]: slab-centring check (idea: bnleft, first-light-pherc0211 `slab_profiles`).
For every 256x256 tile with >= 70 % valid surface, find the render layer with the highest mean intensity; report the
share of tiles whose peak lies in the middle third of the layers, and the median peak layer."""
import sys, json, numpy as np, zarr
T = 256
for p in sys.argv[1:]:
    z = zarr.open(p, mode='r'); a = z['0'] if hasattr(z, 'keys') and '0' in z else z
    L, H, W = a.shape; mid = np.asarray(a[L // 2]) > 0
    peaks = []
    for y in range(0, H - T + 1, T):
        blk = np.asarray(a[:, y:y + T, :]).astype(np.float32)
        for x in range(0, W - T + 1, T):
            v = mid[y:y + T, x:x + T]
            if v.mean() < 0.7: continue
            prof = blk[:, :, x:x + T][:, v].mean(axis=1)
            peaks.append(int(np.argmax(prof)))
    peaks = np.array(peaks)
    lo, hi = L / 3, 2 * L / 3
    share = float(((peaks >= lo) & (peaks < hi)).mean()) if len(peaks) else None
    print(json.dumps({'sv': p.split('fl_survey/')[-1], 'layers': L, 'tiles': len(peaks), 'mid_third_share': None if share is None else round(share, 3),
                      'median_peak_layer': None if not len(peaks) else float(np.median(peaks))}), flush=True)
