"""sharpen_exp.py: PLAN_sharpen.md. Depth-sharpened inputs (villa #1898's tool, unmodified) for the three PHerc0841
arm A surfaces, inferred exactly as arm A (fls.infer, cuDNN off, forward), scored with arm A's pixel AUC and
hp_score_posthoc.py's letter-scale score. Baseline = arm A's own maps (same 17 layers, see the plan); S0 checks that."""
import glob, io, json, math, os, subprocess, sys, time
T = '/media/bullo/Storage/vesuvius_work/unseen_test'; FS = '/media/bullo/Storage/vesuvius_work/fl_survey'; X = f'{T}/sharpen'
os.environ.update(FLS_WORK=f'{T}/fls_work', VC_BIN='/home/bullo/vesuvius-work/villa/build/rt/bin', FLS_CKPTS=f'{FS}/checkpoints/ink_9um',
                  VC3D_CONFIG_DIR=f'{T}/vc3d_cfg', FLS_NO_CUDNN='1')
sys.path.insert(0, f'{FS}/repo'); import fls
sys.path.insert(0, X); import depth_sharpen_9um as DS
import numpy as np, tifffile, cv2, zarr, s3fs
from scipy.ndimage import gaussian_filter
CK = ['hybrid_3d2d-seed42/step-075000', 'hybrid_3d2d-seed43/step-020000']
S3 = {'anon': True}; fs = s3fs.S3FileSystem(anon=True)
SIG, SMO, LUM = 20 / 3.9, 40 / 3.9, 9.366
W00 = '20260220213127-w00'

def log(m): print(time.strftime('%H:%M:%SZ ', time.gmtime()) + m, flush=True)
def gpu_free():
    while subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip():
        time.sleep(10)
def load01(p):
    x = tifffile.imread(p).astype(np.float32); return x / 255.0 if x.max() > 1.5 else x
def hp(img, m):                            # hp_score.py (Scheirer), as in hp_score_posthoc.py
    w = gaussian_filter(m.astype(np.float32), SIG)
    return img - gaussian_filter(img * m, SIG) / np.maximum(w, 1e-3)
def r(a, b): return float(np.corrcoef(a, b)[0, 1])
def centered_slice(length, requested):     # villa prepare_9um_isotropic_input.centered_slice
    s = math.ceil((length - requested) / 2); return s, s + requested
def tifname(v, ck): return f"ink_{v}_{ck.replace('/', '_')}_forward.tif"

segs = sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(f'{T}/armA/*/'))
log(f'segments {segs}; tool {DS.P["what"][:60]}...')

# 1. inputs: centred 21 layers (S0), sharpened with the map (S1) and without (S2), 256-row strips
for seg in segs:
    sv = zarr.open(f'{T}/armA/{seg}/sv.zarr', mode='r'); sv = sv['0'] if '0' in sv else sv
    D, H, W = sv.shape; a, b = centered_slice(D, 21)
    os.makedirs(f'{X}/{seg}', exist_ok=True)
    for v, use_map in (('S0', None), ('S1', True), ('S2', False)):
        p = f'{X}/{seg}/{v}.zarr'
        if os.path.exists(f'{p}/.zarray'): continue
        t = time.time(); z = zarr.open_array(p + '.part', mode='w', shape=(21, H, W), chunks=(21, 128, 128), dtype=np.uint8, zarr_format=2)
        for y in range(0, H, 256):
            blk = np.asarray(sv[a:b, y:y + 256, :])
            z[:, y:y + 256, :] = blk if use_map is None else DS.sharpen(blk, LUM, use_map=use_map)
        os.replace(p + '.part', p); log(f'{seg} {v}: layers {a}..{b - 1} of {D}, {H}x{W}, {time.time() - t:.0f}s')

# 2. inference: S0 sanity (w00, seed42/75k) first, then S1 and S2 x 2 checkpoints x 3 segments
jobs = [(W00, 'S0', CK[0])] + [(s, v, c) for v in ('S1', 'S2') for s in segs for c in CK]
for seg, v, ck in jobs:
    p = f'{X}/{seg}/{tifname(v, ck)}'
    if not os.path.exists(p): gpu_free(); fls.infer(f'{X}/{seg}/{v}.zarr', ck, 'forward', p, 4)
    if v == 'S0':
        A = tifffile.imread(f'{T}/armA/{seg}/{tifname("", ck).replace("ink__", "ink_")}'); B = tifffile.imread(p)
        log(f'S0 sanity {seg}: shapes {A.shape} {B.shape}, identical {float((A == B).mean()):.6f}, max|diff| {int(np.abs(A.astype(int) - B.astype(int)).max())}')

# 3. scoring
res = {}
for seg in segs:
    d = f'{T}/armA/{seg}'; z = zarr.open(f'{d}/sv.zarr', mode='r'); z = z['0'] if '0' in z else z; H, W = z.shape[1:]
    valid0 = np.asarray(z[z.shape[0] // 2]) > 0
    # letter-scale key and core mask, as hp_score_posthoc.py
    key = cv2.resize(tifffile.imread(f'{d}/team_ink_2403um.tif'), (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
    tx = tifffile.imread(io.BytesIO(fs.cat(f'vesuvius-challenge-open-data/PHerc0841/segments/{seg}/mesh/'
                                           f'{seg.split("-", 1)[0]}-on-20260319124803-2.403um.tifxyz/x.tif')))
    valid = valid0 & (cv2.resize((tx > 0).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0)
    core = valid & (gaussian_filter(valid.astype(np.float32), 2 * SIG) > 0.999); kh = hp(key, valid)
    # AUC labels, as arm_a.py
    lab = zarr.open_group(f's3://vesuvius-challenge-open-data/PHerc0841/segments/{seg}/ink-labels/2.403um-volume-20260319124803/20260918/inklabels.zarr', mode='r', storage_options=S3)['2']
    sup = zarr.open_group(f's3://vesuvius-challenge-open-data/PHerc0841/segments/{seg}/ink-labels/2.403um-volume-20260319124803/20260918/supervision.zarr', mode='r', storage_options=S3)['2']
    labs = cv2.resize(np.asarray(lab[:]), (W, H), interpolation=cv2.INTER_NEAREST); sups = cv2.resize(np.asarray(sup[:]), (W, H), interpolation=cv2.INTER_NEAREST)
    maps = {'base_s42': f'{d}/ink_hybrid_3d2d-seed42_step-075000_forward.tif', 'base_s43': f'{d}/ink_hybrid_3d2d-seed43_step-020000_forward.tif',
            'base_mean2': f'{d}/mean2_forward.tif'}
    for v in ('S1', 'S2'):
        maps[f'{v}_s42'] = f'{X}/{seg}/{tifname(v, CK[0])}'; maps[f'{v}_s43'] = f'{X}/{seg}/{tifname(v, CK[1])}'
        mp = f'{X}/{seg}/{v}_mean2_forward.tif'
        tifffile.imwrite(mp, (np.mean([load01(maps[f'{v}_s42']), load01(maps[f'{v}_s43'])], 0) * 255).astype(np.uint8)); maps[f'{v}_mean2'] = mp
    R = res.setdefault(seg, {'core_px': int(core.sum())})
    for name, p in maps.items():
        m01 = load01(p)[:H, :W]; raw = tifffile.imread(p).astype(np.float32)[:H, :W]
        m = core & (raw > 0); ph = hp(raw, m)
        null = max(abs(r(ph[m & np.roll(m, s, 0)], np.roll(kh, s, 0)[m & np.roll(m, s, 0)])) for s in (150, 300, -300))
        pos, neg = m01[(sups > 0) & (labs > 0) & valid0], m01[(sups > 0) & (labs == 0) & valid0]
        hpp = np.histogram(pos, 256, (0, 1))[0].astype(np.float64); hn = np.histogram(neg, 256, (0, 1))[0].astype(np.float64)
        auc = float((np.cumsum(hn) - hn / 2) @ hpp / (hpp.sum() * hn.sum()))
        R[name] = {'hp_r': round(r(ph[m], kh[m]), 4), 'hp_null_max_abs': round(null, 4), 'raw_r': round(r(raw[m], key[m]), 4), 'auc': round(auc, 4)}
        log(f'{seg[-12:]} {name}: {R[name]}')
    # side-by-side for the by-eye check: base mean2 | S1 mean2 | S2 mean2 | team key (same display as r3 views)
    def disp(p): return (np.clip((load01(p)[:H, :W] - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8)
    panels = [disp(maps['base_mean2']), disp(maps['S1_mean2']), disp(maps['S2_mean2']), np.clip(key, 0, 255).astype(np.uint8)]
    k = 1100 / H; panels = [cv2.resize(x, (int(W * k), 1100), interpolation=cv2.INTER_AREA) for x in panels]
    cv2.imwrite(f'{X}/{seg}/compare_base_S1_S2_team.png', np.hstack([np.pad(x, ((0, 0), (0, 12)), constant_values=255) for x in panels]))
    json.dump(res, open(f'{X}/sharpen_results.json', 'w'), indent=1)
log('DONE')
