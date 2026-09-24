# Calibration: does the survey pipeline show text on a scroll the models never saw?

**In one paragraph.** PHerc0841 is not in the `ink_9um` training set (PHerc0139, PHerc1667, PHerc Paris 4, PHerc0814)
and is not First Letters eligible, and the team's 2.4 µm ink predictions show Greek text on three of its traced
segments. We ran the survey pipeline on its 9.366 µm scan, taken like the eligible 9.362 µm volumes (1.2 m, 113 keV). On the team's traced surfaces, rendered exactly as the survey renders, `ink_9um` finds where the ink is: its
maps correlate with the team's predictions (r 0.54–0.61, shifted-map nulls at most 0.13) and reach a pixel AUC of
0.74–0.81 against the team's labels. At letter scale it is blobs: Chris Scheirer's high-pass score is 0.015–0.027 for
a single released checkpoint and 0.046–0.054 for all 14 averaged, rows show on one of the three segments, and no letter
is readable. When `fls.py` grows its own surface from a seed placed on that text, the surface leaves the text-bearing
sheet (0 of 3 patches stay within 5 voxels of it; median distance 20–28 voxels) and its ink maps look like the
survey's speckle. So a survey negative means that the automatic patch showed no text, not that the spot has none.

![PHerc0841: our maps on the team's surfaces next to the team's 2.4 µm predictions, and a patch grown by fls.py from a seed on the text, with its distance to the team's sheet](../../results/figures/calibration_pherc0841.jpg)

## Setup

- **Scan and surfaces.** Volume `20250821151531` (9.366 µm, 113 keV, 1.2 m). The team's three traced segments on it, in
  tifxyz: w00 (`20260220213127-w00`), ag144 (`20260220214732-auto_grown_20260220144552896`) and ag174
  (`20260221022814-auto_grown_20260220174252405`), the names used in [villa #1867](https://github.com/ScrollPrize/villa/issues/1867).
  `PLAN.md` and the scripts call the last two `ag896` and `ag405`.
- **Reference.** The team's ink predictions from the 2.403 µm scan (`ink-detection/*.tif`) and ink labels
  (`ink-labels/2.403um-volume-20260319124803/20260918/`), all from the open-data bucket.
- **Arm A (clean surfaces).** Each team mesh rendered with `fls.py`'s own render step (28 layers, `--flip-normals`,
  scale 1), then `ink_9um` in both directions: A1 with the survey's two checkpoints (seed42/75k, seed43/20k), A2 with
  all 14, a mean map per direction.
- **Arm B (the whole tool, unmodified).** `fls.py run` with 100 generations and the default checkpoints, from a catalog
  row for PHerc0841 (`catalog_PHerc0841.json`). B2: one seed per team segment at its densest text (`informed_seeds.py`,
  team data only). B1: three seeds from the survey's own seed rule.
- **Readouts.** R1 the survey's row score; R2 Pearson r between our map and the team's prediction on the same grid,
  both smoothed at 0.5 mm, against the same r with the team map shifted by 10 and 20 mm in four directions; R3 by eye,
  our maps first and only then the team's; R4 pixel AUC against the labels inside the `supervision` mask.
- **Pre-registration.** `PLAN.md` fixed the arms, readouts and pass/fail criteria before any ink inference on
  PHerc0841 (local commit, 2026-09-24 08:34Z, sha256 `b7f55eabad57da29794313f8865ee5986aad5837b651e7a25c87cca46e772e86`;
  not a public timestamp). Everything added afterwards is marked post-hoc below.

## Verdicts under the pre-registered rules

- **Arm A: inconclusive.** A mean map meets R1 > 28.7 (the survey's highest map when the plan was written; one patch
  finished later scores 33.5) and R2 above its null on 1 of the 3
  segments (ag174: row score 57.8, r 0.602 against a null maximum of 0.099); a pass needed 2 of 3. It is not a fail
  either: R2 is above its null on all three segments. On w00 and ag144 no mean map, 2 or 14 checkpoints, either
  direction, gets above a row score of 15.4.
- **Arm B2: 0 of 3** patches on the team sheet (median distance over the overlap 27.8, 19.9 and 26.9 voxels; the rule
  was at most 5), and 0 of 3 meet the arm A test (best row score 20.9).
- **Arm B1:** reported below; no criterion, since where the text lies at those spots is unknown.
- **A planning miss.** The row-score threshold came from the survey's own maximum and was not checked against the
  reference before the plan was frozen. The team's own prediction scores 34.1 (w00), 28.7 (ag144) and 111.8 (ag174)
  on the same grid, so the threshold was barely reachable on w00 and not reachable on ag144, even for a perfect map.

## Arm A: the team's surfaces

- **Render check.** Our render equals the team's 9.366 µm surface volume of the same mesh: r 0.999998 on all three
  (512 × 512 centre crop, all 28 layers), 99.3–99.4 % of voxels identical, same layer order. Forward is the right
  direction on all three, as #1867's ablation found for the published surface volumes.

| segment | map (forward) | R1 row score | R2 r (null max) | R4 AUC | letter-scale hp r (post-hoc) |
|---|---|---|---|---|---|
| w00 | 2 checkpoints | 13.5 | 0.541 (0.104) | 0.794 | 0.024 |
| w00 | 14 checkpoints | 10.1 | 0.555 (0.126) | 0.813 | 0.046 |
| ag144 | 2 checkpoints | 12.2 | 0.601 (0.126) | 0.743 | 0.029 |
| ag144 | 14 checkpoints | 13.8 | 0.603 (0.121) | 0.756 | 0.053 |
| ag174 | 2 checkpoints | 57.8 | 0.602 (0.099) | 0.757 | 0.027 |
| ag174 | 14 checkpoints | 52.8 | 0.611 (0.112) | 0.761 | 0.054 |

- **Reverse direction.** Mean maps AUC 0.478–0.66, R2 0.092–0.163 (above its null on 3 of 6); forward means AUC
  0.743–0.813, R2 0.541–0.611 (6 of 6).
- **Against #1867.** AndreasHad04's ablation there scores seed42/75k on the team's 9.366 µm surface volumes at 0.7680
  (w00), 0.7599 (ag144) and 0.7614 (ag174), against 0.7740 in distribution. Ours, same checkpoint on identical renders:
  0.748, 0.719 and 0.750, a few hundredths lower. We pool the labels differently (their 9.6 µm level, nearest
  neighbour, full extent onto our grid) and did not look into the difference further.
- **Letter scale (post-hoc, `hp_score_posthoc.py`).** Chris Scheirer's score from
  [vesuvius-reports, report 02](https://github.com/ShribyrLabs/vesuvius-reports/tree/main/02-9um-ink-reader-benchmark),
  with his constants: remove a 48 µm blur from both maps and correlate what is left. The key is the team's 2.403 µm
  prediction area-averaged onto our grid (median tile offset at most 0.07 px). Single released checkpoints score
  0.015–0.027, the reverse means 0.000–0.007, the shifted-key nulls at most 0.007. On his scale (his exams, not these):
  the released model 0.035, blobs 0.04, a read where a person made out four letters 0.076, the best current reads
  0.11–0.14. Averaging the 14 released checkpoints about doubles a single checkpoint's score here and still stays at
  blob level.
- **By eye (`r3_notes.md`).** w00 and ag144: speckle with a few blurry letter-like shapes, which turn out to sit on the
  team's strongest letters; no rows. ag174: letter-like strokes along two or three lines, which turn out to be the
  team's two clearest rows, letter by letter; the survey's visual check would have flagged this map. Nothing readable
  on any of the three.

## Arm B: the whole tool

| patch | area cm² | R1 forward / reverse mean | median distance to the team sheet (vox) | share within 5 vox | R2 on the part within 5 vox (px at 2 vox) |
|---|---|---|---|---|---|
| B2, seed on w00 | 14.30 | 15.7 / 9.4 | 27.8 | 2.8 % | 0.605, null 0.209 (109,460) |
| B2, seed on ag144 | 14.38 | 11.9 / 20.9 | 19.9 | 8.5 % | 0.562, null −0.088* (335,195) |
| B2, seed on ag174 | 14.29 | 9.3 / 7.8 | 26.9 | 4.8 % | 0.100, null 0.389 (184,747) |
| B1, seed 9 (z 0.5, r 0.7) | 15.53 | 10.2 / 17.7 | | | |
| B1, seed 0 (z 0.3, r 0.5) | 17.08 | 11.3 / 6.7 | | | |
| B1, seed 6 (z 0.5, r 0.5) | 13.89 | 13.1 / 11.3 | | | |

\* On small, scattered parts most of the 10–20 mm shifts leave fewer than 1000 overlapping pixels, so these nulls rest
on few shifts.

- **The tracer leaves the sheet as it grows.** For the patch seeded on ag144, the median distance to the team's sheet
  is 5.6 voxels within 100 voxels of the seed, then 7.6, 11.7, 15.2 and 29.7 voxels at 1000–2000 voxels. The ag174
  seed was snapped 7.73 voxels from the team's mesh point and probably started on a neighbouring sheet.
- **Where a patch does lie on the team's sheet** (0.4 and 1.2 cm² for the w00 and ag144 seeds), our map agrees with
  the team's there (r 0.605 and 0.562).
- **By eye.** All six maps look like the survey's speckle: 10–25 % of pixels above 0.5 in the B2 forward means,
  against 5–9 % in arm A's; swirl-like arcs on B1 seed 9, a hole-rim artifact on B1 seed 6; nothing letter-like, not
  even on the patch seeded on ag174's text.
- All six `fls.py` runs finished with exit code 0 (3146–4590 s each, 13.89–17.08 cm² per patch), so the tool runs
  unmodified on a scroll outside its built-in catalog, given a catalog row.

## What it means

- **For the survey:** its negatives say that the automatic patches showed no text. Two reasons, both measured here on
  a scroll with known text: the tracer leaves the text-bearing sheet, and even on a correct surface the 9 µm maps of an
  unseen scroll are faint. This agrees with Chris Scheirer's reports on PHerc0826 and on 9 µm readers
  ([01](https://github.com/ShribyrLabs/vesuvius-reports/tree/main/01-pherc0826-first-letters-null),
  [02](https://github.com/ShribyrLabs/vesuvius-reports/tree/main/02-9um-ink-reader-benchmark)), which reach the same
  conclusion by other routes.
- **For anyone searching the eligible scrolls with `ink_9um`:** a surface that stays on the sheet matters as much as
  the reader, and checking a patch's distance to a known sheet is cheap when one exists (`score_b.py`).

## Deviations and notes

- Arm B ran two jobs at a time, the B2 jobs first; `PLAN.md` fixes neither.
- The A2 notes by eye are not blind: the team's maps had been seen during A1.
- The letter-scale score, the team-map row scores, the figure and the display scripts (`r3_views.py`, `r3_b_views.py`,
  `team_rowscore.py`, `make_results_tables.py`, `hp_score_posthoc.py`, `make_figure.py`) were added after the runs. No
  pre-registered readout was changed.
- The scripts are the copies that ran; their paths are from our machine.

## Files

`PLAN.md` (frozen), `r3_notes.md` (notes by eye, in the order written), `results_tables.md` (every map, generated from
the JSON files by `make_results_tables.py`), `armA_results.json`, `armB_results.json`, `team_rowscore.json`,
`hp_score_posthoc.json`, `seeds_informed.json`, `seeds_blind.txt`, `catalog_PHerc0841.json`, `logs/`, `scripts/`.

## Credits and data

The pixel-AUC comparison on these three segments is AndreasHad04's (villa #1867), with liliandevarieux's observations
on depth order in the same thread; ibara pointed out that the `validation` mask of these label sets lies mostly outside
`supervision` ([ink-disagree](https://github.com/ibarapascal/ink-disagree); we score inside `supervision`). The letter-scale score and its script are Chris Scheirer's (MIT). Scan,
meshes, ink predictions and labels: Vesuvius Challenge open data (CC BY-NC 4.0), and the figure derived from them
carries those terms.
