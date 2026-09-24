"""r3_views.py [--team] [segment ...]: images for readout R3 of PLAN.md (added 2026-09-24 after the freeze; display only).
Step 1 (default): OUR maps alone, armA/<seg>/r3_ours.png: 2-checkpoint mean forward | reverse (and the 14-checkpoint
means when they exist), same contrast as the survey's QA ((m - 0.25) / 0.5), 1500 px tall. Judged before looking at
the team's map.
Step 2 (--team): armA/<seg>/r3_side.png: our forward mean | our reverse mean | the team's map resized to our grid."""
import glob, os, sys
import numpy as np, cv2, tifffile
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
team = '--team' in sys.argv
segs = [a for a in sys.argv[1:] if not a.startswith('--')] or sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(f'{T}/armA/*/'))
def load01(p):
    x = tifffile.imread(p).astype(np.float32); return x / 255.0 if x.max() > 1.5 else x
def show(m): return (np.clip((m - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8)
for seg in segs:
    d = f'{T}/armA/{seg}'
    names = [n for n in ('mean2_forward', 'mean2_reverse', 'mean14_forward', 'mean14_reverse') if os.path.exists(f'{d}/{n}.tif')]
    if not names: print(seg, 'no mean maps yet'); continue
    if team: names = [n for n in names if n.startswith('mean2')]
    panels = [show(load01(f'{d}/{n}.tif')) for n in names]
    H, W = panels[0].shape
    if team:
        tj = cv2.imread(f'{T}/ground_truth/{seg}_team_ink_ds8.jpg', cv2.IMREAD_GRAYSCALE)
        panels.append(cv2.resize(tj, (W, H), interpolation=cv2.INTER_LINEAR)); names.append('team')
    k = 1500 / H
    panels = [cv2.resize(p, (int(W * k), 1500), interpolation=cv2.INTER_AREA) for p in panels]
    out = f'{d}/r3_side.png' if team else f'{d}/r3_ours.png'
    cv2.imwrite(out, np.hstack([np.pad(p, ((0, 0), (0, 16)), constant_values=255) for p in panels]))
    for n, p in zip(names, panels):                    # one file per panel too: easier to inspect at full size
        cv2.imwrite(f'{d}/r3_{"side" if team else "ours"}_{n}.png', p)
    print(seg, out, names)
