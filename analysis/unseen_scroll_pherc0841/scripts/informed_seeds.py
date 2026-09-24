"""informed_seeds.py: one seed per PHerc0841 team segment, at the centre of its densest text, for arm B (informed).
Inputs are the team's own data only (no model output of ours): the 9.366 um tifxyz mesh and the team's 2.403 um ink
map (ds8 jpg). The jpg is exactly 2.5x the 2.403 um mesh grid, and the 9.366 um mesh grid is that grid scaled by
2.403/9.366, so a jpg pixel maps onto the 9.366 um mesh by a plain rescale; the orientation is checked by matching
the outline of the segment in both. The seed is snapped to the nearest level-0 m7 surface voxel (>127) inside a 64^3
box, the same rule as fls.py pick_seeds. Output: seeds_informed.json."""
import json, glob, os, sys
import numpy as np, tifffile, cv2, zarr
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
row = json.load(open(f'{T}/fls_work/catalog.json'))['PHerc0841']
p0 = zarr.open_group('s3://vesuvius-challenge-open-data/' + row['prediction'].rstrip('/'), mode='r', storage_options={'anon': True})['0']
out = []
for segdir in sorted(glob.glob(f'{T}/team_meshes/*/')):
    seg = os.path.basename(segdir.rstrip('/'))
    X, Y, Z = (tifffile.imread(f'{segdir}tifxyz/{c}.tif') for c in 'xyz')
    valid = (X > 0) & (Y > 0) & (Z > 0); gr, gc = X.shape
    jpg = cv2.imread(f'{T}/ground_truth/{seg}_team_ink_ds8.jpg', cv2.IMREAD_GRAYSCALE)
    H, W = jpg.shape
    # orientation: the segment's outline in the jpg (anything not pure black) against the mesh's valid grid points
    jv = cv2.resize((jpg > 6).astype(np.float32), (gc, gr), interpolation=cv2.INTER_AREA) > 0.5
    flips = {'none': lambda a: a, 'flipud': np.flipud, 'fliplr': np.fliplr, 'both': lambda a: a[::-1, ::-1]}
    ious = {name: float((f(jv) & valid).sum() / max(1, (f(jv) | valid).sum())) for name, f in flips.items()}
    best = max(ious, key=ious.get)
    if ious[best] < 0.8: sys.exit(f'{seg}: jpg and mesh outlines do not match (IoU {ious})')
    # densest text: bright strokes (>128) smoothed at ~3 mm (the jpg is 8 x 2.403 um = 19.2 um per pixel),
    # only where the mesh exists (its valid mask brought into the jpg's orientation; the flips are self-inverse)
    dens = cv2.GaussianBlur((jpg > 128).astype(np.float32), (0, 0), 3000 / 19.224)
    dens[cv2.resize(flips[best](valid).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) == 0] = 0
    r, c = np.unravel_index(int(np.argmax(dens)), dens.shape)
    gi, gj = int(round(r * gr / H)), int(round(c * gc / W))
    if best in ('flipud', 'both'): gi = gr - 1 - gi
    if best in ('fliplr', 'both'): gj = gc - 1 - gj
    vi, vj = np.nonzero(valid); k = int(np.argmin((vi - gi) ** 2 + (vj - gj) ** 2)); gi, gj = int(vi[k]), int(vj[k])
    mx, my, mz = float(X[gi, gj]), float(Y[gi, gj]), float(Z[gi, gj])
    # snap to the surface prediction exactly as fls.py does (nearest voxel >127 in a 64^3 box)
    h = 32; Zc, Yc, Xc = int(round(mz)), int(round(my)), int(round(mx))
    oz, oy, ox = Zc - h, Yc - h, Xc - h
    box = np.asarray(p0[oz:Zc + h, oy:Yc + h, ox:Xc + h]); zz, yy, xx = np.nonzero(box > 127)
    if not len(zz): print(seg, 'no surface voxel near the mesh point'); continue
    j = int(np.argmin((zz + oz - mz) ** 2 + (yy + oy - my) ** 2 + (xx + ox - mx) ** 2))
    sd = {'segment': seg, 'x': int(ox + xx[j]), 'y': int(oy + yy[j]), 'z': int(oz + zz[j]),
          'mesh_point': [round(mx, 1), round(my, 1), round(mz, 1)], 'grid_ij': [gi, gj], 'jpg_rc': [int(r), int(c)],
          'snap_distance_vox': round(float(np.sqrt((zz[j] + oz - mz) ** 2 + (yy[j] + oy - my) ** 2 + (xx[j] + ox - mx) ** 2)), 2),
          'orientation': best, 'orientation_iou': {k2: round(v, 3) for k2, v in ious.items()}, 'text_density_peak': round(float(dens.max()), 3)}
    print(json.dumps(sd)); out.append(sd)
json.dump(out, open(f'{T}/seeds_informed.json', 'w'), indent=1)
