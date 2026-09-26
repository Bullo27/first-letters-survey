# Post-hoc: does depth sharpening make the PHerc0841 maps more letter-like?

Added 2026-09-25, after the calibration above was published. [villa #1898](https://github.com/ScrollPrize/villa/issues/1898)
(AndreasHad04) reports that a fixed depth filter on the 21-layer input window raises `ink_9um`'s pixel AUC on
PHerc0841's native 9.366 µm surfaces (median +0.0291 for seed42/75k). We checked whether it also raises the
letter-scale score (Chris Scheirer's high-pass score, as in `../scripts/hp_score_posthoc.py`), on the same three
segments and our renders of them.

- **Plan** (`PLAN_sharpen.md`) written before any inference; local commit, not a public timestamp.
- **Tool**: `bench/depth_sharpen_9um.py` and `.json` from
  [AndreasHad04/villa-apple-silicon at c47b0a33](https://github.com/AndreasHad04/villa-apple-silicon/tree/c47b0a3365bad3ebbd51da583c573f311433ed64/bench),
  run unmodified through its `sharpen()` (layer spacing 9.366 µm); not copied here.
- **Inputs**: the centred 21 of our 28 render layers. The model then reads the same 17 layers as our unsharpened
  runs; an unsharpened 21-layer run reproduced our w00 seed42/75k map bit for bit, so those runs are the baseline.
- **Models**: seed42/75k and seed43/20k, forward; readouts: letter-scale hp_r against the team's 2.403 µm prediction
  and pixel AUC inside `supervision`, same code as before (`sharpen_exp.py`, numbers in `sharpen_results.json`).

2-checkpoint forward mean (S1 = with the tool's intensity map, S2 = `--no-map`):

| segment | hp_r base | hp_r S1 | hp_r S2 | AUC base | AUC S1 | AUC S2 |
|---|---|---|---|---|---|---|
| w00 | 0.0237 | 0.0274 | 0.0275 | 0.7938 | 0.8223 | 0.8189 |
| ag144 | 0.0292 | 0.0320 | 0.0329 | 0.7430 | 0.8051 | 0.8062 |
| ag174 | 0.0267 | 0.0291 | 0.0284 | 0.7567 | 0.7745 | 0.7668 |

- **Pixel level**: AUC goes up by +0.018 to +0.062 with the map (seed42/75k alone +0.029 to +0.056), the same
  direction and size as #1898.
- **Letter scale**: hp_r goes up by +0.002 to +0.004 (with or without the map). The plan's criterion for a
  letter-scale gain, +0.010 on at least 2 of 3 segments, is met on 0 of 3; the highest value is 0.033 (on Scheirer's
  scale a read where a person made out four letters scores 0.076). Shifted-key nulls stay at or below 0.008.
- **By eye** (`ag174_rows_crop.jpg`, full resolution: baseline, S1, S2, the team's prediction): the sharpened maps show
  the same fragments of the team's letters as the baseline, a few strokes slightly more continuous; no letter becomes
  legible.

So on these segments the filter's gain is at blob scale, not letter scale. Averaging the 14 released checkpoints was a
much larger letter-scale lever here (0.046 to 0.054). The filter was fitted (without labels) on these same segments,
so this test is in-sample; sharpening combined with the 14-checkpoint mean was not tested. The scripts are the copies
that ran; their paths are from our machine.
