# The ring area with the 9 µm model released on 2026-09-29

Models: [YoussefMoNader/ink-8um-v8in](https://huggingface.co/YoussefMoNader/ink-8um-v8in) (base, never trained on
PHerc1447) and [YoussefMoNader/ink-8um-v8in-pherc1447-loo-w062](https://huggingface.co/YoussefMoNader/ink-8um-v8in-pherc1447-loo-w062)
(fine-tuned on PHerc1447 windings w058 and w060). Input: the team's surface volume of segment 20250702235910
(`PHerc1447/segments/20250702235910-auto_grown_20250702235910292/surface-volumes/8.64um-1.2m-116keV-volume-20250521151220.zarr`,
31 layers; the central 24 are used), rows 900-1900 and columns 1300-2700, which hold the ring (row 1439, column 2253)
and the point nearest to the announced text location (row 1340, column 1720; 8.6 voxels from x 4144, y 2742, z 12557).

Depth order: forward. The models read the layers going from behind the sheet toward the scroll centre; this
segment's grid normal points away from the scroll axis on all its vertices and the team's surface volumes are
rendered with the normals flipped, so the stored order is already the right one. On the same crop, forward
reproduces the pattern the released base prediction shows on the team's own winding w062 around the text.

```bash
python run_v8in.py --model ink-8um-v8in --input <surface volume>.zarr --out ring_area_base --order fwd --stride 21 --batch 2 --crop 900 1900 1300 2700
python run_v8in.py --model loo-w062     --input <surface volume>.zarr --out ring_area_loo  --order fwd --stride 21 --batch 2 --crop 900 1900 1300 2700
```

`run_v8in.py` needs the `ink8um` package that ships with the model (`--code` points to it). Figure:
`results/figures/pherc1447_ring_v8in.jpg`.
