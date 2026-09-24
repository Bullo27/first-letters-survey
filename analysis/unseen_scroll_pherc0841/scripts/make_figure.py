"""make_figure.py: the calibration figure for the survey README (display only, added 2026-09-24 after the runs).
Row 1-2 (arm A): our 2-checkpoint forward mean on the team's surface (survey contrast) | the team's 2.403 um ink
prediction on the same grid. Row 3 (arm B2): the survey tool's own patch grown from a seed on ag144's text: our forward
mean | distance from our surface to the team's traced sheet (white = on it, black = 30 voxels or more away)."""
import os
import numpy as np, cv2, tifffile
T = '/media/bullo/Storage/vesuvius_work/unseen_test'; H = 520
def show(p):
    m = tifffile.imread(p).astype(np.float32); m = m / 255 if m.max() > 1.5 else m
    return (np.clip((m - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8)
def fit(img, h=H): return cv2.resize(img, (int(img.shape[1] * h / img.shape[0]), h), interpolation=cv2.INTER_AREA)
def label(img, text):
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img
    cv2.rectangle(img, (0, 0), (img.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(img, text, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA); return img
rows = []
for seg, name in (('20260221022814-auto_grown_20260220174252405', 'ag174'), ('20260220213127-w00', 'w00')):
    d = f'{T}/armA/{seg}'
    ours = fit(show(f'{d}/mean2_forward.tif'))
    team = tifffile.imread(f'{d}/team_ink_2403um.tif'); team = cv2.resize(team, (ours.shape[1], ours.shape[0]), interpolation=cv2.INTER_AREA)
    rows.append([label(ours, f'PHerc0841 {name}, team surface: ours (ink_9um, 9.4 um, 2 ckpts)'),
                 label(team, f'PHerc0841 {name}: team 2.4 um ink prediction (same grid)')])
b = f'{T}/fls_work/patches/PHerc0841/B2_ag896'
rows.append([label(fit(cv2.imread(f'{b}/r3b_ours_fwd.png', 0)), 'fls.py patch from a seed on ag144 text: ours'),
             label(fit(cv2.imread(f'{b}/r3b_dist.png', 0)), 'distance to the team sheet (white 0, black >=30 vox)')])
W = max(sum(p.shape[1] for p in r) + 12 for r in rows)
out = []
for r in rows:
    line = np.hstack([r[0], np.full((H, 12, 3), 255, np.uint8), r[1]])
    out += [np.pad(line, ((0, 12), (0, W - line.shape[1]), (0, 0)), constant_values=255)]
os.makedirs(f'{T}/figures', exist_ok=True)
fig = np.vstack(out)[:-12]
cv2.imwrite(f'{T}/figures/calibration_pherc0841.jpg', fig, [cv2.IMWRITE_JPEG_QUALITY, 85])
print(fig.shape, os.path.getsize(f'{T}/figures/calibration_pherc0841.jpg'))
