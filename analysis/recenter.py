"""recenter.py <dir> [target_layer=12] [tile=64]: slab re-centring test (after bnleft's first-light-pherc0211).
<dir> holds the 28-layer render as sv.zarr. Inputs come from the environment: RC_SEG (tifxyz directory),
RC_VOLUME_PATH (bucket key of the masked scan zarr, e.g. PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/),
RC_VX (voxel size in um); VC_BIN (directory of vc_render_tifxyz, default: PATH), RC_SCRATCH (renderer --volume dir).
1. render a 48-layer slab of the patch's tifxyz (same recipe as the survey, only --num-slices 48) -> sv48.zarr
2. check the layer mapping: sv48[k + 10] must match the survey's 28-layer render sv.zarr[k]
3. per tile, find the brightness-peak layer within +-12 layers of the surface, smooth the peak map (3x3 median over
   tiles), and build a 28-layer volume sv_rc.zarr in which every pixel's peak sits at `target_layer` (the controls'
   median peak layer is 12) -> the ink model's 17-layer window (layers 6-22) is centred on the sheet everywhere."""
import sys, os, json, subprocess, time
import numpy as np, zarr, cv2
from scipy.ndimage import median_filter
import shutil
d = os.path.abspath(sys.argv[1]); target = int(sys.argv[2]) if len(sys.argv) > 2 else 12; T = int(sys.argv[3]) if len(sys.argv) > 3 else 64
seg = os.environ['RC_SEG']; elig = {'volume_path': os.environ['RC_VOLUME_PATH'], 'voxel_um': float(os.environ['RC_VX'])}
BIN = os.path.join(os.environ['VC_BIN'], 'vc_render_tifxyz') if os.environ.get('VC_BIN') else shutil.which('vc_render_tifxyz')
def log(m): print(time.strftime('%H:%M:%SZ ', time.gmtime()) + m, flush=True)
sv48 = f'{d}/sv48.zarr'
if not os.path.exists(f'{sv48}/.zattrs'):
    t = time.time()
    cmd = [BIN, '--volume', os.environ.get('RC_SCRATCH', os.path.join(d, 'render_scratch')),
           '--remote-url', 's3://vesuvius-challenge-open-data/' + elig['volume_path'], '--segmentation', seg, '--zarr-output', sv48,
           '--scale', '1', '--group-idx', '0', '--num-slices', '48', '--cache-gb', '16', '--voxel-size', str(elig['voxel_um']),
           '--voxel-unit', 'micrometer', '--flip-normals', '--prefetch-remote']
    for attempt in range(3):
        rc = subprocess.run(cmd, stdout=open(f'{d}/sv48.log', 'a'), stderr=subprocess.STDOUT).returncode
        if rc == 0: break
        log(f'render48 attempt {attempt + 1} rc={rc}')
    if rc: sys.exit(f'render48 failed rc={rc}')
    log(f'render48 {time.time() - t:.0f}s')
A48 = zarr.open(sv48, mode='r')['0']; A28 = zarr.open(f'{d}/sv.zarr', mode='r')['0']
L48, H, W = A48.shape; assert A28.shape[1:] == (H, W), (A28.shape, A48.shape)
# 2. layer mapping check on a central block
cy, cx = H // 2, W // 2
b28 = np.asarray(A28[:, cy - 256:cy + 256, cx - 256:cx + 256]).astype(np.float32)
b48 = np.asarray(A48[:, cy - 256:cy + 256, cx - 256:cx + 256]).astype(np.float32)
best = max(range(0, L48 - 28 + 1), key=lambda o: np.corrcoef(b28.ravel(), b48[o:o + 28].ravel())[0, 1])
cor = np.corrcoef(b28.ravel(), b48[best:best + 28].ravel())[0, 1]
log(f'layer mapping: sv48[k + {best}] ~ sv28[k], corr {cor:.4f}')
off = best
# 3. per-tile peak within +-12 of the surface (48-layer index 24), smoothed
mid = np.asarray(A48[L48 // 2]) > 0
ny, nx = (H + T - 1) // T, (W + T - 1) // T
peak = np.full((ny, nx), np.nan, np.float32)
lo, hi = L48 // 2 - 12, L48 // 2 + 12
for i in range(ny):
    blk = np.asarray(A48[lo:hi, i * T:(i + 1) * T, :]).astype(np.float32)
    for j in range(nx):
        v = mid[i * T:(i + 1) * T, j * T:(j + 1) * T]
        if v.mean() < 0.3: continue
        prof = blk[:, :, j * T:(j + 1) * T][:, v].mean(axis=1)
        peak[i, j] = lo + int(np.argmax(prof))
fill = np.where(np.isnan(peak), np.nanmedian(peak), peak)
peak_s = median_filter(fill, size=3)
shift_t = peak_s - (off + target)                                   # 48-layer index of the output's layer 0 = off + shift
S = cv2.resize(shift_t.astype(np.float32), (nx * T, ny * T), interpolation=cv2.INTER_LINEAR)[:H, :W]
S = np.rint(S).astype(np.int32)
log(f'tile peaks (48-layer index): median {np.nanmedian(peak):.1f}, p10 {np.nanpercentile(peak, 10):.1f}, p90 {np.nanpercentile(peak, 90):.1f}; '
    f'shift vs survey render: median {np.median(S[mid]):.1f}, |shift|>=4 on {(np.abs(S[mid]) >= 4).mean() * 100:.0f} % of pixels')
out = f'{d}/sv_rc.zarr'
g = zarr.open_group(out, mode='w', zarr_format=2)
attrs = dict(zarr.open(f'{d}/sv.zarr', mode='r').attrs)
if 'multiscales' in attrs: attrs['multiscales'][0]['datasets'] = attrs['multiscales'][0]['datasets'][:1]
g.attrs.update(attrs)
dst = g.create_array('0', shape=(28, H, W), chunks=(28, 128, 128), dtype='uint8') if hasattr(g, 'create_array') else g.create_dataset('0', shape=(28, H, W), chunks=(28, 128, 128), dtype='uint8')
k = np.arange(28, dtype=np.int32)[:, None, None]
for y0 in range(0, H, 512):
    y1 = min(H, y0 + 512)
    blk = np.asarray(A48[:, y0:y1, :])
    idx = np.clip(off + S[None, y0:y1, :] + k, 0, L48 - 1)
    dst[:, y0:y1, :] = np.take_along_axis(blk, idx, axis=0)
log(f'wrote {out}')
