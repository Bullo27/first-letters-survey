#!/usr/bin/env python3
"""fls.py - First Letters survey: from an eligible scroll in the Vesuvius Challenge open-data bucket to 9 um
ink-model predictions on a freshly grown patch, with nothing downloaded up front.

    python fls.py run --scroll PHerc1218                     # seed picked on the surface prediction
    python fls.py run --scroll PHerc1218 --seed 3520 2400 7200 --gens 100
    python fls.py seeds --scroll PHerc1218                   # list candidate seeds only

Steps (each skipped when its output exists):
  seeds    pick seed voxels on the scroll's m7 surface prediction, placed relative to the masked scan (the
           prediction also fires outside the papyrus)
  grids    fetch, in parallel over keep-alive connections, only the normal-grid slices the patch can reach
           (the tracer would fetch them one by one otherwise)
  grow     vc_grow_seg_from_seed with the parameters VC3D's "Create Segment (GrowPatch)" uses
  render   vc_render_tifxyz: 28-layer surface volume at native resolution (the scrollprize.org 9 um recipe)
  infer    vesuvius.ink_detection.inference.infer with the released ink_9um checkpoints, both directions
  report   previews (render middle layer + ink maps) and a text-row periodicity score per prediction

Configuration (environment):
  FLS_WORK   work directory (default ./fls_work): caches, patches, renders, predictions
  VC_BIN     directory holding vc_grow_seg_from_seed and vc_render_tifxyz (default: found on PATH)
  FLS_CKPTS  directory with ink_9um checkpoints (downloaded from huggingface.co/scrollprize/ink_9um if missing)
  FLS_NO_CUDNN=1  run inference with cuDNN disabled (for environments with a cuDNN sub-library mismatch)
"""
import argparse, concurrent.futures as cf, gzip, http.client, json, os, re, shutil, ssl, subprocess, sys, threading, time, urllib.request
BUCKET_HOST = 'vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com'
BUCKET = f'https://{BUCKET_HOST}/'
ELIGIBILITY = 'https://raw.githubusercontent.com/ScrollPrize/villa/main/scrollprize.org/src/data/prizeEligibility.json'
HF = 'https://huggingface.co/scrollprize/ink_9um/resolve/main/'
DEFAULT_CKPTS = ['hybrid_3d2d-seed42/step-075000', 'hybrid_3d2d-seed43/step-020000']
WORK = os.path.abspath(os.environ.get('FLS_WORK', 'fls_work'))

def log(msg): print(time.strftime('%H:%M:%SZ ', time.gmtime()) + msg, flush=True)
def get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': 'fls', 'Accept-Encoding': 'gzip'})
    b = urllib.request.urlopen(req, timeout=timeout).read()
    return gzip.decompress(b) if b[:2] == b'\x1f\x8b' else b
_tls = threading.local()
def bucket_get(key, tries=6):
    """GET a bucket key over this thread's persistent HTTPS connection (one TLS handshake per thread, not per file).
    Returns the bytes, or None for 404."""
    for a in range(tries):
        c = getattr(_tls, 'c', None)
        if c is None:
            c = _tls.c = http.client.HTTPSConnection(BUCKET_HOST, timeout=60, context=ssl.create_default_context())
        try:
            c.request('GET', '/' + key); r = c.getresponse(); b = r.read()
            if r.status == 200: return b
            if r.status == 404: return None
            raise IOError(f'HTTP {r.status}')
        except Exception:
            try: c.close()
            except Exception: pass
            _tls.c = None; time.sleep(0.5 + a)
    raise IOError(f'giving up on {key}')
def write_atomic(path, data):
    tmp = f'{path}.part{os.getpid()}_{threading.get_ident()}'
    with open(tmp, 'wb') as f: f.write(data)
    os.replace(tmp, path)
def tool(name):
    d = os.environ.get('VC_BIN'); p = os.path.join(d, name) if d else shutil.which(name)
    if not p or not os.path.exists(p): sys.exit(f'{name} not found: set VC_BIN to the volume-cartographer bin directory')
    return p

# ---------------------------------------------------------------- catalog
def scroll_info(scroll):
    """Paths of the First Letters volume of `scroll`: scan, m7 surface prediction, normal grids, voxel size."""
    cache = os.path.join(WORK, 'catalog.json')
    if not os.path.exists(cache):
        os.makedirs(WORK, exist_ok=True)
        elig = json.loads(get(ELIGIBILITY))['first-letters-2027']
        cat = json.loads(get(BUCKET + 'metadata.json'))
        rows = {}
        for e in elig:
            v = cat['samples'][e['scroll']]['volumes'][e['volume']]
            paths = {d['type']: (d.get('origins') or [{}])[0].get('path') for d in v.get('data') or []}
            p = v.get('properties') or {}
            rows[e['scroll']] = {'volume': e['volume'], 'voxel_um': p.get('pixel_size_um'), 'shape_zyx': p.get('shape'),
                                 'scan': paths.get('ome-zarr'), 'prediction': paths.get('surface-prediction-zarr'),
                                 'normal_grids': paths.get('normal-grids')}
        write_atomic(cache, json.dumps(rows, indent=1).encode())
    rows = json.load(open(cache))
    if scroll not in rows: sys.exit(f'{scroll} is not in the First Letters eligible list: {", ".join(rows)}')
    return rows[scroll]

# ---------------------------------------------------------------- seeds
def pick_seeds(scroll, zfs=(0.3, 0.5, 0.7), rfs=(0.5, 0.7), angles=(0.8, 3.0, 5.2)):
    """Seeds placed relative to the papyrus itself: at height fraction zf, radius fraction rf of the masked scan's
    radius (level 5) and angle, take the nearest m7 surface pixel (level 4, >127) that lies inside the scan mask,
    refined to an exact level-0 surface voxel. The prediction alone is not a safe guide: on every eligible volume
    34-61 % of its lit samples lie where the masked scan is 0, i.e. outside the scroll."""
    import numpy as np, zarr
    r = scroll_info(scroll); so = {'anon': True}
    m5 = zarr.open('s3://vesuvius-challenge-open-data/' + r['scan'].rstrip('/'), mode='r', storage_options=so)['5']
    g = zarr.open_group('s3://vesuvius-challenge-open-data/' + r['prediction'].rstrip('/'), mode='r', storage_options=so)
    p4, p0 = g['4'], g['0']; out = []
    for zf in zfs:
        z5 = int(m5.shape[0] * zf); mask = np.asarray(m5[max(0, z5 - 1):z5 + 2]).max(axis=0) > 0
        ys, xs = np.nonzero(mask)
        if len(ys) < 30: continue
        cy, cx = ys.mean(), xs.mean(); rmask = np.percentile(np.hypot(ys - cy, xs - cx), 99)
        z4 = z5 * 2; sl = np.asarray(p4[max(0, z4 - 2):z4 + 3]).max(axis=0) > 127
        m4 = np.zeros_like(sl); k = np.kron(mask, np.ones((2, 2), bool))[:sl.shape[0], :sl.shape[1]]; m4[:k.shape[0], :k.shape[1]] = k
        py, px = np.nonzero(sl & m4)
        if not len(py): continue
        for rf in rfs:
            for ang in angles:
                ty, tx = 2 * (cy + rf * rmask * np.sin(ang)), 2 * (cx + rf * rmask * np.cos(ang))
                i = int(np.argmin((py - ty) ** 2 + (px - tx) ** 2))
                if (py[i] - ty) ** 2 + (px[i] - tx) ** 2 > (0.08 * 2 * rmask) ** 2: continue
                Z, Y, X, h = z4 * 16, int(py[i]) * 16, int(px[i]) * 16, 32
                oz, oy, ox = max(0, Z - h), max(0, Y - h), max(0, X - h)
                box = np.asarray(p0[oz:Z + h, oy:Y + h, ox:X + h]); zz, yy, xx = np.nonzero(box > 127)
                if not len(zz): continue
                j = int(np.argmin((zz + oz - Z) ** 2 + (yy + oy - Y) ** 2 + (xx + ox - X) ** 2))
                out.append({'zf': zf, 'rf': rf, 'angle': ang, 'x': int(ox + xx[j]), 'y': int(oy + yy[j]), 'z': int(oz + zz[j])})
    return out

# ---------------------------------------------------------------- normal grids
def grid_dir(scroll):
    r = scroll_info(scroll); d = os.path.join(WORK, 'normal_grids', scroll, r['volume']); os.makedirs(d, exist_ok=True)
    key = r['normal_grids'].rstrip('/'); base = BUCKET + key
    if not os.path.exists(os.path.join(d, 'normal-grids-remote.json')):   # the tracer streams anything we did not fetch
        write_atomic(os.path.join(d, 'normal-grids-remote.json'), json.dumps({'url': base}).encode())
    if not os.path.exists(os.path.join(d, 'metadata.json')):
        b = bucket_get(key + '/metadata.json')                            # read first: a failed read leaves no empty file
        if b is None: sys.exit(f'no normal grids for {scroll} at {base}')
        write_atomic(os.path.join(d, 'metadata.json'), b)
    return d, key
def fetch_grids(scroll, x, y, z, gens, workers=48):
    r = scroll_info(scroll); d, key = grid_dir(scroll)
    sp = max(1, int(json.load(open(os.path.join(d, 'metadata.json'))).get('sparse-volume', 1)))
    R = int(gens * 20 * 1.15); Zs, Ys, Xs = r['shape_zyx']
    def rng(c, n): return range(max(0, (c - R) // sp * sp), min(n - 1, c + R) + 1, sp)
    jobs = [('xy', i) for i in rng(z, Zs)] + [('xz', i) for i in rng(y, Ys)] + [('yz', i) for i in rng(x, Xs)]
    def one(j):
        rel = f'{j[0]}/{j[1]:06d}.grid'; dst = os.path.join(d, rel)
        if os.path.exists(dst) or os.path.exists(dst + '.missing'): return 'have'
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try: b = bucket_get(f'{key}/{rel}')
        except IOError: return 'fail'                                       # the tracer fetches it itself later
        if b is None: open(dst + '.missing', 'w').close(); return '404'
        write_atomic(dst, b); return 'ok'
    t = time.time()
    with cf.ThreadPoolExecutor(workers) as ex: res = list(ex.map(one, jobs))
    log(f'grids: {len(jobs)} slices within +-{R} voxels, {res.count("ok")} fetched, {res.count("have")} cached, '
        f'{res.count("404")} absent, {res.count("fail")} failed, {time.time() - t:.0f}s')

# ---------------------------------------------------------------- grow / render
def grow(scroll, x, y, z, gens, threads, out):
    r = scroll_info(scroll); d, _ = grid_dir(scroll); os.makedirs(out, exist_ok=True)
    params = {'mode': 'seed', 'step_size': 20, 'generations': gens, 'min_area_cm': 0, 'thread_limit': threads,
              'normal_grid_path': d, 'voxelsize': r['voxel_um'], 'cache_size': 4_000_000_000,
              'cache_root': os.path.join(WORK, 'tracer_cache')}
    pj = os.path.join(out, 'params.json'); json.dump(params, open(pj, 'w'), indent=1)
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1')          # keep the OpenBLAS pool from spinning (villa #1316)
    t = time.time()
    with open(os.path.join(out, 'grow.log'), 'w') as f:
        rc = subprocess.run([tool('vc_grow_seg_from_seed'), BUCKET + r['prediction'].rstrip('/'), out, pj, str(x), str(y), str(z)],
                            stdout=f, stderr=subprocess.STDOUT, env=env).returncode
    segs = sorted(d2 for d2 in os.listdir(out) if d2.startswith('auto_grown_'))
    if rc or not segs: sys.exit(f'grow failed (rc={rc}); see {out}/grow.log')
    seg = os.path.join(out, segs[-1]); area = json.load(open(os.path.join(seg, 'meta.json'))).get('area_cm2')
    log(f'grow: {area:.2f} cm2 in {time.time() - t:.0f}s -> {seg}')
    return seg
def render(scroll, seg, out_zarr):
    r = scroll_info(scroll); t = time.time()
    cmd = [tool('vc_render_tifxyz'), '--volume', os.path.join(WORK, 'render_scratch'),
           '--remote-url', 's3://vesuvius-challenge-open-data/' + r['scan'], '--segmentation', seg, '--zarr-output', out_zarr,
           '--scale', '1', '--group-idx', '0', '--num-slices', '28', '--cache-gb', '16',
           '--voxel-size', str(r['voxel_um']), '--voxel-unit', 'micrometer', '--flip-normals', '--prefetch-remote']
    for attempt in range(1, 4):          # a dropped connection aborts the renderer (villa #1809); chunks already fetched are cached
        with open(out_zarr + '.log', 'a') as f:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
        if rc == 0: break
        log(f'render attempt {attempt} failed (rc={rc}); see {out_zarr}.log')
    if rc: sys.exit(f'render failed (rc={rc}); see {out_zarr}.log')
    log(f'render: {time.time() - t:.0f}s -> {out_zarr}')

# ---------------------------------------------------------------- inference / report
def ckpt_path(name):
    d = os.environ.get('FLS_CKPTS', os.path.join(WORK, 'checkpoints')); p = os.path.join(d, name + '.pth')
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True); log(f'downloading {name} from huggingface.co/scrollprize/ink_9um')
        urllib.request.urlretrieve(HF + name + '.pth', p + '.part'); os.replace(p + '.part', p)
    return p
def infer(sv, ckpt, direction, out_tif, batch):
    code = ('import sys, runpy, os\n'
            'if os.environ.get("FLS_NO_CUDNN") == "1":\n import torch; torch.backends.cudnn.enabled = False\n'
            'sys.argv = ["infer"] + sys.argv[1:]\n'
            'runpy.run_module("vesuvius.ink_detection.inference.infer", run_name="__main__", alter_sys=True)\n')
    t = time.time()
    with open(out_tif + '.log', 'w') as f:
        rc = subprocess.run([sys.executable, '-c', code, sv, ckpt_path(ckpt), out_tif, '--overlap', '0.5', '--blend-mode', 'hann',
                             '--batch-size', str(batch), '--no-compile', '--direction', direction], stdout=f, stderr=subprocess.STDOUT).returncode
    if rc: sys.exit(f'inference failed (rc={rc}); see {out_tif}.log')
    log(f'infer {os.path.basename(out_tif)}: {time.time() - t:.0f}s')
def row_score(pred, vx_um, valid=None):
    """Text rows are a few mm apart: peak/median FFT power in the 2.5-8 mm period band of the ink map (angle-agnostic)."""
    import numpy as np, cv2
    v = np.clip((pred - 0.25) / 0.5, 0, 1); k = 4
    ds = cv2.resize(v, (v.shape[1] // k, v.shape[0] // k), interpolation=cv2.INTER_AREA)
    vm = (cv2.resize((pred > 0.01 if valid is None else valid).astype(np.uint8), (ds.shape[1], ds.shape[0]), interpolation=cv2.INTER_NEAREST))
    vm = cv2.erode(vm, np.ones((31, 31), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(vm, connectivity=8)
    if n > 1:                                   # largest surface piece only: thin strips and islands fake periods
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); x0, y0, bw, bh = st[big, :4]
        vm = (lab == big)[y0:y0 + bh, x0:x0 + bw]; ds = ds[y0:y0 + bh, x0:x0 + bw]
    vm = vm.astype(bool)
    if vm.sum() < 5000: return None
    x = ds.copy(); x[~vm] = ds[vm].mean(); x -= x.mean(); h, w = x.shape
    P = np.abs(np.fft.fftshift(np.fft.fft2(x * np.outer(np.hanning(h), np.hanning(w))))) ** 2
    fy, fx = np.meshgrid(np.fft.fftshift(np.fft.fftfreq(h)), np.fft.fftshift(np.fft.fftfreq(w)), indexing='ij'); fr = np.hypot(fy, fx)
    mm = k * vx_um * 1e-3; band = (fr > mm / 8.0) & (fr < mm / 2.5)
    if band.sum() < 20: return None
    i = np.unravel_index(np.argmax(np.where(band, P, 0)), P.shape)
    return {'row_score': round(float(P[band].max() / np.median(P[band])), 1), 'period_mm': round(float(mm / fr[i]), 2),
            'angle_deg': round(float(np.degrees(np.arctan2(fy[i], fx[i]))), 1), 'mean_ink': round(float(v.mean()), 4)}
def report(scroll, sv, preds, outdir):
    import numpy as np, cv2, tifffile, zarr
    r = scroll_info(scroll); z = zarr.open(sv, mode='r'); a = z['0'] if hasattr(z, 'keys') and '0' in z else z
    mid = np.asarray(a[a.shape[0] // 2]); valid = mid > 0; res = {}
    def save(img, name, norm):
        h, w = img.shape; s = min(1.0, 1400 / max(h, w)); img = cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(outdir, name), cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX) if norm else img)
    save(mid, 'render_mid.png', True)
    sums = {}
    for p in preds:
        q = np.asarray(tifffile.imread(p)).astype(np.float32); q = q[..., 0] if q.ndim == 3 else q
        if q.max() > 1.5: q /= 255.0 if q.max() <= 255 else 65535.0
        save((np.clip((q - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8), os.path.basename(p).replace('.tif', '.png'), False)
        res[os.path.basename(p)] = row_score(q, r['voxel_um'], valid)
        dr = 'reverse' if p.endswith('_reverse.tif') else 'forward'
        n, acc = sums.get(dr, (0, 0)); sums[dr] = (n + 1, acc + q)
    # Averaging checkpoints per direction lifts real text: on held-out PHerc0139 w045 the two default checkpoints
    # score 84 and 111 alone and 125 averaged (all 14 checkpoints: 148).
    for dr, (n, acc) in sums.items():
        if n < 2: continue
        m = acc / n; name = f'ink_mean_{dr}'
        tifffile.imwrite(os.path.join(outdir, name + '.tif'), (np.clip(m, 0, 1) * 255).astype(np.uint8))
        save((np.clip((m - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8), name + '.png', False)
        res[name + '.tif'] = row_score(m, r['voxel_um'], valid)
    json.dump(res, open(os.path.join(outdir, 'scores.json'), 'w'), indent=1)
    for k, v in res.items(): log(f'{k}: {v or "no row score (the patch is too small to measure a 2.5-8 mm period)"}')

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('seeds'); s.add_argument('--scroll', required=True)
    r = sub.add_parser('run'); r.add_argument('--scroll', required=True); r.add_argument('--seed', type=int, nargs=3, metavar=('X', 'Y', 'Z'))
    r.add_argument('--seed-index', type=int, help='index into the "seeds" list (default: first seed at mid height, half radius)')
    r.add_argument('--gens', type=int, default=100); r.add_argument('--threads', type=int, default=8)
    r.add_argument('--ckpts', nargs='+', default=DEFAULT_CKPTS, help='checkpoint names, or "all" for the 14 released ones')
    r.add_argument('--batch', type=int, default=4); r.add_argument('--name')
    a = ap.parse_args()
    if a.cmd == 'run' and a.ckpts == ['all']:
        a.ckpts = [f'hybrid_3d2d-seed{s}/step-{k:06d}' for s in (42, 43) for k in (10000, 20000, 30000, 40000, 50000, 60000, 75000)]
    if a.cmd == 'seeds':
        for i, sd in enumerate(pick_seeds(a.scroll)): print(i, json.dumps(sd))
        return
    if a.seed: x, y, z = a.seed
    else:
        seeds = pick_seeds(a.scroll)
        if not seeds: sys.exit(f'no seed found on {a.scroll}; pass --seed X Y Z')
        i = a.seed_index if a.seed_index is not None else next((k for k, s in enumerate(seeds) if s['zf'] == 0.5 and s['rf'] == 0.5), 0)
        sd = seeds[i]; x, y, z = sd['x'], sd['y'], sd['z']; log(f'seed {i}: {sd}')
    out = os.path.join(WORK, 'patches', a.scroll, a.name or f'{x}_{y}_{z}_g{a.gens}'); os.makedirs(out, exist_ok=True)
    segs = sorted(d for d in os.listdir(out) if d.startswith('auto_grown_'))
    if segs: seg = os.path.join(out, segs[-1]); log(f'grow: reusing {seg}')
    else: fetch_grids(a.scroll, x, y, z, a.gens); seg = grow(a.scroll, x, y, z, a.gens, a.threads, out)
    sv = os.path.join(out, 'surface_volume.zarr')
    if not os.path.exists(os.path.join(sv, '.zattrs')): render(a.scroll, seg, sv)
    preds = []
    for ck in a.ckpts:
        for dr in ('forward', 'reverse'):
            p = os.path.join(out, f"ink_{ck.replace('/', '_')}_{dr}.tif"); preds.append(p)
            if not os.path.exists(p): infer(sv, ck, dr, p, a.batch)
    report(a.scroll, sv, preds, out)
    log(f'done: {out}')
if __name__ == '__main__': main()
