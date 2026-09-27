"""blur_views.py: by-eye check for blur_matched.py. For each segment, the 700 px window (>= 97 % inside both meshes) where the team's key has the most
48 um high-pass energy: 14-checkpoint mean as is | 14-checkpoint mean blurred 4 px | best single checkpoint (at 4 px)
blurred 4 px | the team's key. Same display stretch as the r3 views."""
import glob, json, os
import io
import numpy as np, cv2, tifffile, zarr, s3fs
from scipy.ndimage import gaussian_filter
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
SIG = 20 / 3.9
d = json.load(open(f'{T}/blur_matched.json'))
fs = s3fs.S3FileSystem(anon=True)
for seg in sorted(d):
    D = f'{T}/armA/{seg}'
    z = zarr.open(f'{D}/sv.zarr', mode='r'); z = z['0'] if '0' in z else z; H, W = z.shape[1:]
    key = cv2.resize(tifffile.imread(f'{D}/team_ink_2403um.tif'), (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
    valid = np.asarray(z[z.shape[0] // 2]) > 0                       # as blur_matched.py: our mesh & the team's mesh
    tx = tifffile.imread(io.BytesIO(fs.cat(f'vesuvius-challenge-open-data/PHerc0841/segments/{seg}/mesh/'
                                           f'{seg.split("-", 1)[0]}-on-20260319124803-2.403um.tifxyz/x.tif')))
    valid &= cv2.resize((tx > 0).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    inside = cv2.blur(valid.astype(np.float32), (700, 700)) > 0.97     # window (almost) fully inside both meshes
    kh = key - gaussian_filter(key, SIG)
    e = np.where(inside, gaussian_filter(kh ** 2, 150), -1)
    y, x = np.unravel_index(np.argmax(e), e.shape)
    sl = np.s_[y - 350:y + 350, x - 350:x + 350]
    singles = {k: v['4'] for k, v in d[seg]['hp_r'].items() if k.startswith('seed')}
    best = max(singles, key=singles.get)
    m14 = tifffile.imread(f'{D}/mean14_forward.tif').astype(np.float32)[:H, :W]
    b1 = tifffile.imread(f'{D}/ink_hybrid_3d2d-{best}_forward.tif').astype(np.float32)[:H, :W]
    supp = (m14 > 0) & (b1 > 0); S = supp.astype(np.float32); sw = np.maximum(gaussian_filter(S, 4), 1e-3)
    blur = lambda p: np.where(supp, gaussian_filter(p * S, 4) / sw, 0)
    disp = lambda p: (np.clip((p / 255 - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8)
    panels = [disp(m14[sl]), disp(blur(m14)[sl]), disp(blur(b1)[sl]), np.clip(key[sl], 0, 255).astype(np.uint8)]
    out = np.hstack([np.pad(p, ((0, 0), (0, 10)), constant_values=255) for p in panels])
    name = {'20260220213127-w00': 'w00', '20260220214732-auto_grown_20260220144552896': 'ag144',
            '20260221022814-auto_grown_20260220174252405': 'ag174'}[seg]
    fn = f'{T}/blur_view_{name}.jpg'; cv2.imwrite(fn, out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(seg, 'window centre (y,x)', (int(y), int(x)), 'best single at 4 px:', best, singles[best], '->', fn)
