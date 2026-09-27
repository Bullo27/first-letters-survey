# On-prediction support of the survey patches (villa #1906)

villa PR [#1906](https://github.com/ScrollPrize/villa/pull/1906) makes `vc_grow_seg_from_seed` report, after growth,
the share of the surface's valid vertices whose rounded position lands on a nonzero voxel of level 0 of the prediction
it was grown from, and warn below 50 % ([#1675](https://github.com/ScrollPrize/villa/issues/1675): surfaces that cut
across the windings of an L2 prediction scored 6–10 %). Its description says the default was tested on point sets,
not on real meshes. Our 65 survey patches are real meshes, grown by `vc_grow_seg_from_seed` from the published L0 m7 surface
predictions of 21 scrolls (`predictions.json`) with the GrowPatch parameters, each with our by-eye verdict on its render
(`results/results.json`).

- `support_check.py`: #1906's rule (`SurfaceSupport.hpp` at 562105e8a) on every patch in `results/segments/`, plus
  the same hit rate 1–8 voxels either side of the surface along its normal, and the share of nonzero voxels at random
  positions in the chunks the patch crosses (background). Output `support_check.json`.
- `cross_check.py`: regrows a patch from one survey seed with `fls.py`'s `grow()` and the tracer built from #1906, and
  compares the support the tracer prints with `support_check.py`'s count on the saved surface. Output `cross_check.json`.

| by-eye verdict on the render | patches | on-prediction support | below 50 % | at the surface minus 5–8 voxels off (points) | background |
|---|---|---|---|---|---|
| follows the sheet throughout | 5 | 44.8–62.7 % | 2 | +24.8 to +49.2 | 24.8–26.7 % |
| partly on the sheet | 36 | 29.2–55.5 % | 34 | +3.0 to +41.2 | 19.9–29.1 % |
| swirls, no on-sheet part | 21 | 25.9–34.8 % | 21 | +0.3 to +10.6 | 17.5–31.1 % |
| escapes the papyrus | 3 | 28.4–65.0 % | 2 | +20.8 to +61.1 | 10.9–15.5 % |

"At the surface minus 5–8 voxels off" is the hit rate at the surface minus the mean hit rate 5, 6, 7 and 8 voxels either
side along the normal. The groups come from the verdicts (`category()` in `support_check.py`).

**Cross-check.** The tracer built from #1906's `vc_grow_seg_from_seed.cpp` and `SurfaceSupport.hpp` (head 562105e8a;
the rest of the tree at villa main 33b0b91b7) regrew 30 generations (1.14–1.15 cm²) from the seed of v3/PHerc0211/s0
("follows the sheet throughout (diagonal crosshatch)") 5 times with the same parameters. It printed supports of 43.7–50.9 %
and the warning in 4 of the 5 runs; in every run `support_check.py` counts the same vertices as the tracer. The surfaces
lie on the predicted sheet: 43.3–50.6 % at the surface, 15.1–18.7 % 5–6 voxels either side. Each survey patch in the
table is a single run.

**Reading.** On these predictions, patches whose renders show layer-crossing swirls and no on-sheet part score
25.9–34.8 %, not 6–10 %: 17.5–31.1 % of the voxels around them are nonzero, and their hit rate at the
surface stays close to the rate a few voxels away (+0.3 to +10.6 points). With the 50 % default the check flags all
21 of them, and 2 of the 5 patches that follow the sheet throughout (44.8 % and 49.3 %). The highest support, 65.0 %,
belongs to v3/PHerc0211/s9, whose render shows uniform material over most of its area: it follows the prediction
(+61.1 points), so the check cannot tell it from a sheet.
