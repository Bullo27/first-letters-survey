"""rowscore.py <pred.tif> <voxel_um> [sv.zarr] : text-row periodicity score for an ink prediction.
Writing sits in rows a few mm apart, so a real ink response carries a spectral peak at a 2.5-8 mm period
in one direction. Score = peak power in that band / median power in the same band (angle-agnostic)."""
import sys, json, numpy as np, tifffile, cv2
src, vx = sys.argv[1], float(sys.argv[2])
a = np.asarray(tifffile.imread(src)).astype(np.float32)
if a.ndim == 3: a = a[..., 0] if a.shape[-1] < 5 else a[0]
if a.max() > 1.5: a = a / (255.0 if a.max() <= 255 else 65535.0)
v = np.clip((a - 0.25) / 0.5, 0, 1)
valid = a > 0.01
if len(sys.argv) > 3:
    import zarr
    z = zarr.open(sys.argv[3], mode='r'); z0 = z['0'] if hasattr(z, 'keys') and '0' in z else z
    mid = np.asarray(z0[z0.shape[0] // 2]); valid = mid > 0
k = 4                                                      # work at 1/4 resolution
ds = cv2.resize(v, (v.shape[1] // k, v.shape[0] // k), interpolation=cv2.INTER_AREA)
vm = cv2.resize(valid.astype(np.uint8), (ds.shape[1], ds.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
vm = cv2.erode(vm.astype(np.uint8), np.ones((31, 31), np.uint8))   # drop the border frame artifact
n, lab, st, _ = cv2.connectedComponentsWithStats(vm, connectivity=8)
if n > 1:                                                            # keep only the largest surface piece (thin strips fake periods)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); vm = lab == big
    x0, y0, bw, bh = st[big, :4]; ds = ds[y0:y0 + bh, x0:x0 + bw]; vm = vm[y0:y0 + bh, x0:x0 + bw]
vm = vm.astype(bool)
if vm.sum() < 5000:
    print(json.dumps({'score': None, 'reason': 'too small'})); sys.exit()
x = ds.copy(); x[~vm] = ds[vm].mean(); x = x - x.mean()
h, w = x.shape; win = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
P = np.abs(np.fft.fftshift(np.fft.fft2(x * win))) ** 2
fy = np.fft.fftshift(np.fft.fftfreq(h)); fx = np.fft.fftshift(np.fft.fftfreq(w))
FY, FX = np.meshgrid(fy, fx, indexing='ij'); fr = np.hypot(FY, FX)       # cycles per downsampled px
px_mm = k * vx * 1e-3                                                    # mm per downsampled px
band = (fr > px_mm / 8.0) & (fr < px_mm / 2.5)
if band.sum() < 20:
    print(json.dumps({'score': None, 'reason': 'band empty'})); sys.exit()
bp = P[band]; peak = bp.max(); med = np.median(bp)
iy, ix = np.unravel_index(np.argmax(np.where(band, P, 0)), P.shape)
period_mm = px_mm / fr[iy, ix]; ang = float(np.degrees(np.arctan2(FY[iy, ix], FX[iy, ix])))
res = {'score': round(float(peak / med), 1), 'period_mm': round(float(period_mm), 2), 'angle_deg': round(ang, 1),
       'mean_ink': round(float(v[valid].mean()), 4), 'p99': round(float(np.percentile(v[valid], 99)), 3),
       'frac_gt_0.5': round(float((v[valid] > 0.5).mean()), 4), 'valid_px': int(valid.sum())}
print(json.dumps(res))
