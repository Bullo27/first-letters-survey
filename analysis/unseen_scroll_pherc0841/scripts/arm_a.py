"""arm_a.py [--smoke] [--ckpts default|all] [segment ...]: arm A of PLAN.md. Each PHerc0841 team mesh is rendered and
inferred with fls.py's own render() and infer() (the survey tool's code path), then scored:
  R1 row score (fl_survey/rowscore.py, the survey's scorer), R2 correlation with the team's ink map against a shifted-map
  null, R4 pixel AUC against the team's labels, plus a render check against the team's own 9.366 um surface volume and
  a QA sheet (render middle layer | 2-ckpt mean forward | reverse | team map).
--smoke: plumbing check on the PHerc0139 w045 control instead (1 checkpoint, forward); its known row score is 83.9."""
import argparse, glob, json, os, subprocess, sys, time
T = '/media/bullo/Storage/vesuvius_work/unseen_test'; FS = '/media/bullo/Storage/vesuvius_work/fl_survey'
ap = argparse.ArgumentParser(); ap.add_argument('--smoke', action='store_true'); ap.add_argument('--ckpts', default='default')
ap.add_argument('segments', nargs='*'); a = ap.parse_args()
WORKDIR = f'{T}/smoke_work' if a.smoke else f'{T}/fls_work'
os.environ.update(FLS_WORK=WORKDIR, VC_BIN='/home/bullo/vesuvius-work/villa/build/rt/bin', FLS_CKPTS=f'{FS}/checkpoints/ink_9um',
                  VC3D_CONFIG_DIR=f'{T}/vc3d_cfg', FLS_NO_CUDNN='1')   # = fl_survey/run_infer.py (cuDNN off)
os.makedirs(f'{T}/vc3d_cfg', exist_ok=True)
sys.path.insert(0, f'{FS}/repo'); import fls                                   # WORK is read from FLS_WORK at import
import numpy as np, tifffile, cv2, zarr
ALL = [f'hybrid_3d2d-seed{s}/step-{k:06d}' for s in (42, 43) for k in (10000, 20000, 30000, 40000, 50000, 60000, 75000)]
DEF = fls.DEFAULT_CKPTS
S3 = {'anon': True}

def log(m): print(time.strftime('%H:%M:%SZ ', time.gmtime()) + m, flush=True)
def gpu_free():                          # never share the GPU with another inference (survey or anything else)
    while subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip():
        time.sleep(10)
def rowscore(tif, vx, sv):
    o = subprocess.run(['/home/bullo/vesuvius-work/venv/bin/python', f'{FS}/rowscore.py', tif, str(vx), sv], capture_output=True, text=True).stdout.strip()
    return json.loads(o.splitlines()[-1]) if o else None
def load01(p):
    x = tifffile.imread(p).astype(np.float32); return x / 255.0 if x.max() > 1.5 else x
def mean_map(paths, out):
    tifffile.imwrite(out, (np.mean([load01(p) for p in paths], 0) * 255).astype(np.uint8)); return out

if a.smoke:
    # PHerc0139 w045 (held-out segment of a training scroll): rendered and inferred through the same functions
    os.makedirs(WORKDIR, exist_ok=True)
    json.dump({'PHerc0139': {'volume': '20250728140407', 'voxel_um': 9.362, 'shape_zyx': None,
               'scan': 'PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/', 'prediction': '', 'normal_grids': ''}},
              open(f'{WORKDIR}/catalog.json', 'w'))
    seg = f'{FS}/heldout/PHerc0139/20260126000000-w045_2026012619/tifxyz'
    out = f'{T}/smoke'; os.makedirs(out, exist_ok=True); sv = f'{out}/sv.zarr'
    if not os.path.exists(f'{sv}/.zattrs'): fls.render('PHerc0139', seg, sv)
    p = f'{out}/pred_s42_75k_forward.tif'
    if not os.path.exists(p): gpu_free(); fls.infer(sv, 'hybrid_3d2d-seed42/step-075000', 'forward', p, 4)
    log(f'SMOKE row score {rowscore(p, 9.362, sv)}  (known: 83.9 from the survey control run)')
    sys.exit(0)

VX = 9.366
segs = a.segments or sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(f'{T}/team_meshes/*/'))
ckpts = ALL if a.ckpts == 'all' else DEF
res_path = f'{T}/armA_results.json'
res = json.load(open(res_path)) if os.path.exists(res_path) else {}
for seg in segs:
    out = f'{T}/armA/{seg}'; os.makedirs(out, exist_ok=True); sv = f'{out}/sv.zarr'; R = res.setdefault(seg, {})
    if not os.path.exists(f'{sv}/.zattrs'): fls.render('PHerc0841', f'{T}/team_meshes/{seg}/tifxyz', sv)
    ours = zarr.open(sv, mode='r'); ours = ours['0'] if '0' in ours else ours
    # render check: our 28 layers against the team's 28-layer surface volume of the same mesh, centre crop
    if 'render_check' not in R:
        team = zarr.open_group(f's3://vesuvius-challenge-open-data/PHerc0841/segments/{seg}/surface-volumes/9.366um-1.2m-113keV-volume-20250821151531.zarr',
                               mode='r', storage_options=S3)['0']
        h, w = ours.shape[1:]; y0, x0 = h // 2 - 256, w // 2 - 256
        A = np.asarray(ours[:, y0:y0 + 512, x0:x0 + 512]).astype(np.float32); B = np.asarray(team[:, y0:y0 + 512, x0:x0 + 512]).astype(np.float32)
        def corr(u, v):
            m = (u > 0) & (v > 0); return float(np.corrcoef(u[m], v[m])[0, 1]) if m.sum() > 1000 else None
        R['render_check'] = {'shape_ours': list(ours.shape), 'shape_team': list(team.shape),
                             'corr_same_order': corr(A, B), 'corr_reversed_order': corr(A, B[::-1]),
                             'identical_fraction': float((A == B).mean())}
        log(f'{seg} render check {R["render_check"]}')
    # inference (fls.py's own call), both directions
    preds = {}
    for ck in ckpts:
        for dr in ('forward', 'reverse'):
            p = f"{out}/ink_{ck.replace('/', '_')}_{dr}.tif"; preds[(ck, dr)] = p
            if not os.path.exists(p): gpu_free(); fls.infer(sv, ck, dr, p, 4)
    maps = {}
    for dr in ('forward', 'reverse'):
        maps[f'mean2_{dr}'] = mean_map([preds[(c, dr)] for c in DEF], f'{out}/mean2_{dr}.tif')
        if ckpts == ALL: maps[f'mean14_{dr}'] = mean_map([preds[(c, dr)] for c in ALL], f'{out}/mean14_{dr}.tif')
    for (ck, dr), p in preds.items(): maps[f"{ck.replace('/', '_')}_{dr}"] = p
    # team map on our grid: the ds8 jpg (19.224 um/px) resized to the render grid (orientation checked: none)
    H, W = ours.shape[1:]
    tj = cv2.imread(f'{T}/ground_truth/{seg}_team_ink_ds8.jpg', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    tm = cv2.resize(tj, (W, H), interpolation=cv2.INTER_LINEAR)
    valid = np.asarray(ours[ours.shape[0] // 2]) > 0
    sig = 500 / VX                                                             # 0.5 mm
    tms = cv2.GaussianBlur(tm, (0, 0), sig)
    lab = zarr.open_group(f's3://vesuvius-challenge-open-data/PHerc0841/segments/{seg}/ink-labels/2.403um-volume-20260319124803/20260918/inklabels.zarr', mode='r', storage_options=S3)['2']
    sup = zarr.open_group(f's3://vesuvius-challenge-open-data/PHerc0841/segments/{seg}/ink-labels/2.403um-volume-20260319124803/20260918/supervision.zarr', mode='r', storage_options=S3)['2']
    labs = cv2.resize(np.asarray(lab[:]), (W, H), interpolation=cv2.INTER_NEAREST); sups = cv2.resize(np.asarray(sup[:]), (W, H), interpolation=cv2.INTER_NEAREST)
    shifts = [(int(round(dy * d / VX)), int(round(dx * d / VX))) for d in (10000, 20000) for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1))]
    scores = R.setdefault('maps', {})
    for name, p in maps.items():
        if name in scores: continue
        m = load01(p); ms = cv2.GaussianBlur(m, (0, 0), sig)
        def r_of(t):
            k = valid & (t > 0); return float(np.corrcoef(ms[k], t[k])[0, 1]) if k.sum() > 1000 else None
        r = r_of(tms); null = [r_of(np.roll(tms, s, axis=(0, 1))) for s in shifts]
        pos, neg = m[(sups > 0) & (labs > 0) & valid], m[(sups > 0) & (labs == 0) & valid]
        auc = None
        if len(pos) and len(neg):
            hp = np.histogram(pos, 256, (0, 1))[0].astype(np.float64); hn = np.histogram(neg, 256, (0, 1))[0].astype(np.float64)
            auc = float((np.cumsum(hn) - hn / 2) @ hp / (hp.sum() * hn.sum()))       # P(score_pos > score_neg), ties half
        scores[name] = {'row': rowscore(p, VX, sv), 'r_team': r, 'r_null_max': max(x for x in null if x is not None) if any(x is not None for x in null) else None,
                        'auc_labels': auc, 'n_pos': int(len(pos)), 'n_neg': int(len(neg))}
        log(f'{seg} {name}: {scores[name]}')
    # QA sheet
    def u8(x): return (np.clip(x, 0, 1) * 255).astype(np.uint8)
    mid = np.asarray(ours[ours.shape[0] // 2])
    panels = [mid, u8(np.clip((load01(maps['mean2_forward']) - 0.25) / 0.5, 0, 1)), u8(np.clip((load01(maps['mean2_reverse']) - 0.25) / 0.5, 0, 1)), u8(tm)]
    k = 900 / H; panels = [cv2.resize(x, (int(W * k), 900), interpolation=cv2.INTER_AREA) for x in panels]
    cv2.imwrite(f'{out}/qa_sheet.png', np.hstack([np.pad(x, ((0, 0), (0, 12)), constant_values=255) for x in panels]))
    json.dump(res, open(res_path, 'w'), indent=1)
log('arm A done')
