# On-prediction support of the survey patches (villa #1906)

villa PR [#1906](https://github.com/ScrollPrize/villa/pull/1906) makes `vc_grow_seg_from_seed` report, after growth,
the share of the surface's valid vertices whose rounded position lands on a nonzero voxel of level 0 of the prediction
it was grown from, and warn below 50 % ([#1675](https://github.com/ScrollPrize/villa/issues/1675): surfaces that cut
across the windings of an L2 prediction scored 6–10 %). From head 3787b68f1 it also warns when that share is at or
below a background rate: the same share at 2000 uniform random points in the bounding box of the surface, dilated by
64 voxels. Its description says the 50 % default was tested on point sets, not on real meshes. Our 65 survey patches
are real meshes, grown by `vc_grow_seg_from_seed` from the published L0 m7 surface predictions of 21 scrolls
(`predictions.json`) with the GrowPatch parameters, each with our by-eye verdict on its render (`results/results.json`).

- `support_check.py`: #1906's rule (`SurfaceSupport.hpp`) on every patch in `results/segments/`, plus the same hit rate
  1–8 voxels either side of the surface along its normal, and the share of nonzero voxels at random positions in the
  chunks the patch crosses. Output `support_check.json`.
- `background_check.py`: #1906's background box for the sheet-following, swirl-only and escaping patches: the background rate
  estimated from 500 uniform points (the tracer draws 2000 with its own generator), and how many chunks 2000 points
  fall in. Output `background_check.json`.
- `cross_check.py`: regrows a patch from one survey seed with `fls.py`'s `grow()` and the tracer built from #1906, and
  compares what the tracer prints with `support_check.py` on the saved surface. Outputs `cross_check_<build>.json`.

| by-eye verdict on the render | patches | on-prediction support | below 50 % | at the surface minus 5–8 voxels off (points) | background in the crossed chunks |
|---|---|---|---|---|---|
| follows the sheet throughout | 5 | 44.8–62.7 % | 2 | +24.8 to +49.2 | 24.8–26.7 % |
| partly on the sheet | 36 | 29.2–55.5 % | 34 | +3.0 to +41.2 | 19.9–29.1 % |
| swirls, no on-sheet part | 21 | 25.9–34.8 % | 21 | +0.3 to +10.6 | 17.5–31.1 % |
| escapes the papyrus | 3 | 28.4–65.0 % | 2 | +20.8 to +61.1 | 10.9–15.5 % |

"At the surface minus 5–8 voxels off" is the hit rate at the surface minus the mean hit rate 5, 6, 7 and 8 voxels either
side along the normal: the layer-profile idea of [#1777](https://github.com/ScrollPrize/villa/issues/1777), applied to the prediction.
The groups come from the verdicts (`category()` in `support_check.py`). Each patch is a single run.

**Background check (3787b68f1).** In the box #1906 samples, the background is 20.2–24.8 % around the
5 sheet-following patches and 17.6–33.2 % around the 21 swirl-only ones. Support minus background is
+22.6 to +42.5 points for the sheet-following patches and −2.7 to +10.9 for the swirl-only ones, so "at or below
background" flags 3 of 21 swirl-only patches (5 more are within 3 points of it) and none of the sheet-following ones.
With 500 points the estimate is good to about ±2 points.

**Cross-check.** The tracer built from #1906's `vc_grow_seg_from_seed.cpp` and `SurfaceSupport.hpp` (the rest of the tree
at villa main 33b0b91b7) regrew 30 generations (1.14–1.15 cm²) from the seed of v3/PHerc0211/s0
("follows the sheet throughout (diagonal crosshatch)"), 5 times at head 562105e8a and 5 times at 3787b68f1, same parameters. Support
43.7–50.9 % and 44.8–51.2 %; the 50 % warning in 4 of 5 and 4 of 5 runs; at 3787b68f1 a printed
background of 20.3–22.3 % and the relative warning in none of the 5 runs. In every run `support_check.py` counts the same
vertices as the tracer. The surfaces lie on the predicted sheet: 43.3–51.1 % at the surface, 15.0–18.7 % 5–6
voxels either side.

**Reading.** On these predictions the 50 % check flags all 21 swirl-only patches, and also 2 of the 5 that follow
the sheet throughout and most regrowths of a sheet-following seed; the relative check flags none of the sheet-following
patches and 3 of the 21 swirl-only ones. In these data, support minus background splits the two groups for any margin
between +10.9 and +22.6 points, and so does the hit rate at the surface minus the rate a few voxels along the normal.
The highest support, 65.0 %, belongs to a patch whose render shows uniform material over most of its area
(v3/PHerc0211/s9): it follows the prediction (+61.1 points at the surface, box background about 17.6 %),
so neither check can tell it from a sheet.
