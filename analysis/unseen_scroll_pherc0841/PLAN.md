# Unseen-scroll test (PHerc0841): would the survey pipeline show text on a scroll the ink models never saw?

Written 2026-09-24, before any ink inference of ours on PHerc0841. Criteria below are fixed now; anything decided
later is marked as an amendment with its time.

## Question
The First Letters survey (github.com/Bullo27/first-letters-survey) found no letters on 46 automatic patches of the 21
unsegmented eligible scrolls. Its positive controls (PHerc0139 w033, w045) are held-out *segments* of a scroll the
ink_9um models were trained on. This test asks whether the same pipeline shows text on a scroll the models never saw,
where text is known to be: PHerc0841.

## Prior work (credit; do not claim what it already shows)
- villa #1867 (AndreasHad04) and its thread (liliandevarieux): pixel AUC of ink_9um against the team's labels on the
  same three PHerc0841 segments. Primary checkpoint seed42/75k, median of the three: 0.7614 on the team's 9.366 um
  surface volumes (the eligible grid), 0.8294 on the 2.403 um volumes pooled, 0.6931 on the 4.681 um label-bucket
  renders (which need reversing). In distribution (PHerc0139 w016): 0.7740 (primary), up to 0.9365 (14 checkpoints).
- New here: (1) surfaces rendered by us from the 9.366 um scan exactly as the survey does; (2) the survey's readouts
  (row score, rows/letters by eye), i.e. detectability, not pixel AUC; (3) arm B runs the full survey tool, automatic
  tracing included, on this scroll.

## Data
- Scan: PHerc0841 volume 20250821151531, 9.366 um, 113 keV, 1.2 m (same campaign as the 9.362 um / 113 keV eligible scans).
- Team meshes on that scan (tifxyz, scale 0.05): 20260220213127-w00, 20260220214732-auto_grown_20260220144552896 (ag896),
  20260221022814-auto_grown_20260220174252405 (ag405).
- Ground truth: the team's ink detection from the 2.403 um scan (ink-detection/*.tif, ds8 jpg) and labels
  (ink-labels/2.403um-volume-20260319124803/20260918/inklabels.zarr). All three show rows of Greek letters.
- PHerc0841 is not in the ink_9um training set (PHerc0139, PHerc1667, PHerc Paris 4, PHerc0814) and is not First
  Letters eligible (23 eligible scrolls, checked 2026-09-24).

## Arms
- **A (clean surfaces):** each team mesh -> our render (vc_render_tifxyz, 28 layers, --flip-normals, --scale 1, native
  9.366 um; fls.py's render(), identical to the survey) -> ink_9um:
  - A1: survey default, seed42/75k + seed43/20k, both directions, 2-checkpoint mean per direction;
  - A2: all 14 checkpoints, both directions, 14-checkpoint mean per direction.
  - Render check: our render against the team's 9.366 um surface volume of the same mesh (correlation on the shared layers).
- **B (full tool, unmodified):** fls.py run, 100 generations, default checkpoints, both directions, FLS_WORK=unseen_test/fls_work
  (catalog.json holds the PHerc0841 row built from the bucket catalog the way fls.py builds eligible rows):
  - B1 blind: the survey's seed rule on this scroll: seed 9 (zf .5, rf .7) and seed 0 (zf .3, rf .5), as in survey v3,
    plus seed 6 (zf .5, rf .5, the fls.py default). Seeds in seeds_blind.txt.
  - B2 informed: one seed per team segment at its densest text (seeds_informed.json, informed_seeds.py: team ink map
    + team mesh only, snapped to the m7 surface with the fls.py rule): w00 (4171, 4200, 13415), ag896 (3893, 3690, 14682),
    ag405 (3818, 3425, 14789).
- C (optional, not pre-registered): PHerc0172 (Scroll 5), a 7.91 um / 53 keV scan, i.e. a different scan type.

## Readouts, per ink map
- R1 row score (the survey's: FFT peak/median power in the 2.5-8 mm period band on the largest eroded surface piece,
  valid region from the render's middle layer), with period and angle.
- R2 agreement with the team's map: Pearson r between our map and the team's ink map resampled onto our grid (both
  smoothed at 0.5 mm, inside the shared valid region), against a null of the same r with the team map shifted by
  10-20 mm (circular shifts in 8 directions). Arm A only; for B2 on the part of the patch that lies on the team sheet.
- R3 visual: first our map alone (rows of strokes? letter shapes?), then side by side with the team's map.
- R4 (A, secondary): pixel AUC against the team's labels pooled to our grid, to tie our renders to #1867's numbers.
- References: PHerc0139 held-out w033 / w045, 2-checkpoint forward mean 71.4 / 125.1, 14-checkpoint 73.3 / 147.7;
  every survey map <= 28.7.

## Pre-registered criteria
- **Arm A PASS:** on at least 2 of the 3 segments, a mean map (A1 or A2, either direction) has R1 > 28.7 (above every
  survey map) AND R2 above the maximum of its shift null. **FAIL:** on all 3 segments every mean map has R1 <= 28.7 and
  R2 within its null. Otherwise **INCONCLUSIVE**, reported with what disagrees.
- **Arm B2:** per patch, (i) on the team sheet: median distance from our surface to the team mesh <= 5 voxels over their
  overlap, and (ii) the arm A PASS test applied to the patch (R1 > 28.7 and R2 above its null on the overlap).
  Reported as k of 3.
- **Arm B1:** R1 and R3 reported; no pass/fail (where the text is on those spots is unknown).
- **Reading, fixed now:** A PASS and B2 (ii) true where (i) holds -> the survey method shows text on a new scroll when the
  patch is on the sheet, so the survey's negatives mean "no text in those spots, or surfaces off the sheet".
  A PASS but B2 off the sheet -> tracing is the bottleneck. A FAIL -> at 9 um with these checkpoints, text on an unseen
  scroll does not show through this pipeline, and the survey's negatives say little about the eligible scrolls.

## Amendment 1 (2026-09-24 ~08:40Z, before any arm A or arm B data on PHerc0841)
- Geometry check of score_b.py on the team's own meshes: w00 against itself, median 0.000 voxels (the code works; its
  max of 23.7 is the trimmed edge of the densified surface). ag896 against w00, which cover the same area: median
  8.45 voxels, p10 3.20, 20.5 % of points within 5 voxels. The two team traces therefore lie on neighbouring sheets
  over most of the area, and neighbouring sheets can be under 10 voxels (94 um) apart here. The 5-voxel "same sheet"
  rule stays.
- Consequence: a B2 patch that leaves the team sheet may sit on a neighbouring sheet that carries text of its own.
  So for every B2 patch, R1 and R3 (does it show text at all) are reported whether or not it is on the team sheet;
  R2 against the team map is only meaningful on the on-sheet overlap and is reported with its overlap size.

## Practicalities
- GPU shared with the running survey: inference waits until no other run_infer.py is running (arm A), fls.py
  inference as is (arm B, batch 4, rerun resumes if a step fails).
- Nothing here is letter-like material from an eligible scroll (secrecy rule does not apply); publishing any of it
  needs the user's OK and the public-action gate.
