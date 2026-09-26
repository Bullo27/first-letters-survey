# Depth sharpening (villa #1898) at letter scale on PHerc0841: plan, written before any inference

Question. villa #1898 (AndreasHad04) reports that a fixed depth filter on the 21-layer input window raises
`ink_9um`'s pixel AUC on PHerc0841's native 9.366 um surfaces (median +0.0291, seed42/75k; 41 of 42
checkpoint x segment pairs). Does it also raise the letter-scale score (Chris Scheirer's hp score, as in
`hp_score_posthoc.py`), i.e. does it make the maps more letter-like, not only better at pixel level?

Caveat fixed in advance: the filter was fitted (without labels) on these same three PHerc0841 segments, so
PHerc0841 is in-sample for the filter. This measures the letter-scale effect where the AUC effect is known;
it is not a test of generalization.

Tool: https://github.com/AndreasHad04/villa-apple-silicon at c47b0a3365bad3ebbd51da583c573f311433ed64,
`bench/depth_sharpen_9um.py` + `bench/depth_sharpen_9um.json` (copied here unmodified), called through its
`sharpen()` on 256-row strips (the filter is per pixel along depth, so strips are exact), `layer_um = 9.366`.

Inputs: our arm A renders `armA/<seg>/sv.zarr` (28 layers, equal to the team's 9.366 um surface volumes,
r 0.999998), centred 21 layers as villa's `centered_slice(28, 21)` picks them: layers 4..24. For the model's
17-layer window villa's `center_crop_layer_indices` then reads layers 2..18 of those 21 = layers 6..22 of the
28, the same layers arm A's 28-layer runs read, so arm A's maps are the unsharpened baseline.

Variants: S0 = unsharpened 21-layer window (sanity check only: w00, seed42/75k, forward; must reproduce arm A's
map, else S0 is run for every map and used as the baseline); S1 = sharpened with the intensity map (the
tool's default); S2 = sharpened, `--no-map` (exploratory in #1898).

Models: hybrid_3d2d-seed42/step-075000 and seed43/step-020000 (the survey defaults), forward (the correct
direction on these surfaces), plus the 2-checkpoint mean. Inference exactly as arm A (fls.infer, cuDNN off).

Readouts (same code as arm A / hp_score_posthoc.py): hp_r (letter scale) on the core mask with the team's
2.403 um prediction as key; pixel AUC inside `supervision` against the 20260918 labels; then by eye.

Criteria (fixed now):
- Letter-scale gain: 2-checkpoint mean hp_r(S1) - hp_r(baseline) >= +0.010 on at least 2 of 3 segments.
- Letter-level read: only if hp_r >= 0.076 on a segment (Scheirer's four-letter read on his exams) AND
  letters are visible by eye. Otherwise no readability claim.
- AUC: report the change; #1898's protocol differs (label pooling, label-free direction choice), so only
  the sign and rough size are compared.
Nothing from this is published without the gate and the user's decision.
