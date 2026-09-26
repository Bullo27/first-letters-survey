"""ring_check.py: measure the one ring-shaped mark on PHerc1447 segment 20250702235910 (README, Validation).

Input: the segment directory as our run left it: sv.zarr (the team's published surface volume, 31 layers, fetched
from the open-data bucket), tifxyz/ (the team's mesh), ens/*_forward.tif (the 14 released ink_9um checkpoints,
forward) and ens/ens_mean.tif (their mean), pred_*_reverse.tif (seed42/75k and seed43/20k, reverse).
Output: ring_check.json next to this script and ../../results/figures/pherc1447_ring.jpg.
"""
import sys, os, glob, json, numpy as np, tifffile, zarr, cv2

SEG = sys.argv[1] if len(sys.argv) > 1 else \
    '/media/bullo/Storage/vesuvius_work/fl_survey/published/PHerc1447/20250702235910-auto_grown_20250702235910292'
HERE = os.path.dirname(os.path.abspath(__file__))
R0, C0, W = 1430, 2250, 300     # the mark as first noted by eye (render row, column) and the half-width of the crop
GUESS = (265, 320)              # rough centre of the ring inside the crop (x, y), by eye
VOXEL_UM = 8.64                 # PHerc1447, volume 20250521151220

E = tifffile.imread(f'{SEG}/ens/ens_mean.tif').astype(np.float32)
sv = zarr.open(f'{SEG}/sv.zarr', mode='r')['0']
MID = sv.shape[0] // 2
win = np.s_[R0 - W:R0 + W, C0 - W:C0 + W]
e = E[win]
valid_full = np.asarray(sv[MID]) > 0
valid = valid_full[win]
yy, xx = np.mgrid[:2 * W, :2 * W]

# mesh: render pixel (r, c) = tifxyz grid (r / 20, c / 20); bilinear lookup of the volume coordinates
G = {a: tifffile.imread(f'{SEG}/tifxyz/{a}.tif').astype(np.float64) for a in 'xyz'}
step = round(1 / json.load(open(f'{SEG}/tifxyz/meta.json'))['scale'][0])
def xyz(r, c):
    gr, gc = r / step, c / step; i, j = int(gr), int(gc); fr, fc = gr - i, gc - j
    return np.array([(1 - fr) * (1 - fc) * g[i, j] + (1 - fr) * fc * g[i, j + 1] + fr * (1 - fc) * g[i + 1, j]
                     + fr * fc * g[i + 1, j + 1] for g in (G['x'], G['y'], G['z'])])
gr, gc = round(R0 / step), round(C0 / step)
vox_per_px = [float(np.linalg.norm(xyz((gr + 1) * step, gc * step) - xyz((gr - 1) * step, gc * step)) / (2 * step)),
              float(np.linalg.norm(xyz(gr * step, (gc + 1) * step) - xyz(gr * step, (gc - 1) * step)) / (2 * step))]
um_per_px = VOXEL_UM * float(np.mean(vox_per_px))

# the ring: bright pixels of the smoothed 14-checkpoint mean near the guess, circle fitted by least squares
es = cv2.GaussianBlur(e, (0, 0), 3)
bright = (es > 150) & valid & (np.hypot(xx - GUESS[0], yy - GUESS[1]) < 260)
ys, xs = np.nonzero(bright)
cx, cy, k = np.linalg.lstsq(np.c_[2 * xs, 2 * ys, np.ones(len(xs))], xs ** 2 + ys ** 2, rcond=None)[0]
R = float(np.sqrt(k + cx ** 2 + cy ** 2))
radii = np.hypot(xs - cx, ys - cy)
ang = np.degrees(np.arctan2(ys - cy, xs - cx)) % 360
cover = ''.join('#' if n > 20 else '.' for n in np.histogram(ang, bins=36, range=(0, 360))[0])
centre = (R0 - W + float(cy), C0 - W + float(cx))

# each map: mean on the ring (radius R +- 35 px) minus mean on a surrounding annulus (R + 60 to R + 160 px)
d = np.hypot(xx - cx, yy - cy)
ring, outside = (np.abs(d - R) < 35) & valid, (d > R + 60) & (d < R + 160) & valid
maps = {}
for f in sorted(glob.glob(f'{SEG}/ens/*_forward.tif')) + sorted(glob.glob(f'{SEG}/pred_*_reverse.tif')):
    a = tifffile.imread(f).astype(np.float32)[win]
    name = os.path.basename(f).replace('pred_', '').replace('.tif', '')
    maps[name] = {'ring': round(float(a[ring].mean()), 1), 'outside': round(float(a[outside].mean()), 1),
                  'ring_minus_outside': round(float(a[ring].mean() - a[outside].mean()), 1)}

# distance from the bright ring pixels to the nearest pixel outside the mesh (holes and edges)
dist = cv2.distanceTransform(valid_full.astype(np.uint8), cv2.DIST_L2, 5)[win]

# render brightness on the bright ring pixels vs the surrounding annulus, layer by layer (in SDs of the annulus)
layers = []
for L in range(sv.shape[0]):
    a = np.asarray(sv[L])[win].astype(np.float32)
    layers.append(round(float((a[bright].mean() - a[outside].mean()) / a[outside].std()), 2))

fwd = [v['ring_minus_outside'] for k_, v in maps.items() if k_.endswith('forward')]
rev = [v['ring_minus_outside'] for k_, v in maps.items() if k_.endswith('reverse')]
out = {
    'segment': os.path.basename(SEG), 'surface_volume_layers': int(sv.shape[0]), 'surface_layer': MID,
    'voxels_per_render_px_rows_cols': [round(v, 3) for v in vox_per_px], 'um_per_render_px': round(um_per_px, 2),
    'ring_centre_render_row_col': [round(v) for v in centre],
    'ring_centre_volume_xyz': [round(float(v)) for v in xyz(*centre)],
    'ring_ridge_radius_px': round(R, 1), 'ring_diameter_mm': round(2 * R * um_per_px / 1000, 2),
    'ring_outer_diameter_mm_p95': round(2 * float(np.percentile(radii, 95)) * um_per_px / 1000, 2),
    'bright_px': int(bright.sum()), 'angular_coverage_10deg_0right_90down': cover,
    'maps_grey_levels': maps,
    'forward_ring_minus_outside_range': [min(fwd), max(fwd)], 'reverse_ring_minus_outside': rev,
    'bright_ring_to_mesh_edge_min_mm': round(float(dist[bright].min()) * um_per_px / 1000, 2),
    'render_layer_z_ring_vs_annulus': layers,
}
json.dump(out, open(f'{HERE}/ring_check.json', 'w'), indent=1)
print(json.dumps({k_: v for k_, v in out.items() if k_ != 'maps_grey_levels'}, indent=1))

# figure: render at the surface layer | 14-checkpoint forward mean | mean of the two reverse maps (grey levels as is)
def label(im, text):
    im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(im, (0, 0), (2 * W, 34), (0, 0, 0), -1)
    cv2.putText(im, text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    return im
s = np.asarray(sv[MID])[win].astype(np.float32); lo, hi = np.percentile(s[valid], [1, 99])
render = (np.clip((s - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
revs = np.mean([tifffile.imread(f).astype(np.float32)[win] for f in sorted(glob.glob(f'{SEG}/pred_*_reverse.tif'))], 0)
panels = [label(render, f'render, layer {MID} (surface)'), label(np.clip(e, 0, 255).astype(np.uint8), 'ink, 14 checkpoints, forward'),
          label(np.clip(revs, 0, 255).astype(np.uint8), 'ink, 2 checkpoints, reverse')]
bar = round(1000 / um_per_px)
cv2.rectangle(panels[1], (2 * W - 20 - bar, 2 * W - 30), (2 * W - 20, 2 * W - 22), (255, 255, 255), -1)
cv2.putText(panels[1], '1 mm', (2 * W - 20 - bar, 2 * W - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
sep = np.full((2 * W, 8, 3), 255, np.uint8)
cv2.imwrite(os.path.normpath(f'{HERE}/../../results/figures/pherc1447_ring.jpg'),
            np.hstack([panels[0], sep, panels[1], sep, panels[2]]), [cv2.IMWRITE_JPEG_QUALITY, 90])
