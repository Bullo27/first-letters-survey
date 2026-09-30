#!/usr/bin/env python
"""Run a released ink-8um model (v8-in or a finetune) on surface volumes.

Inputs: a layers/ directory (00.tif...) or one of our fls.py sv.zarr renders (level 0, D x H x W).
The central 24 layers are used (fls.py renders 28 slices at offsets -13.5..+13.5, so the
central 24 are -11.5..+11.5, the model's training offsets).
Outputs per input and depth order: <out>_<fwd|rev>.png (8-bit), .tif (16-bit), _prev.jpg (1/4 size).
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np, cv2, tifffile

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--code", default="/media/bullo/Storage/vesuvius_work/v8in/ink-8um-v8in")
ap.add_argument("--input", nargs="+", required=True, help="layers dirs or sv.zarr dirs")
ap.add_argument("--out", nargs="+", required=True, help="output prefix per input")
ap.add_argument("--order", default="both", choices=["fwd", "rev", "both"])
ap.add_argument("--stride", type=int, default=21)
ap.add_argument("--batch", type=int, default=16)
ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--norm-blend", action="store_true", help="stitch with sum(p*w)/sum(w) (no vignetting at large strides); default = released recipe sum(p*w)/count")
ap.add_argument("--reverse-auto", default=None, help="JSON {input: true/false} overriding --order per input")
ap.add_argument("--crop", type=int, nargs=4, default=None, metavar=("R0","R1","C0","C1"), help="crop rows R0:R1, cols C0:C1 (render pixels)")
a = ap.parse_args()
assert len(a.input) == len(a.out)
sys.path.insert(0, a.code)
from ink8um import InkDetector
from ink8um.inference import read_stack, predict_stack, save_prediction

def load_stack(p: Path, depth=24, clip_max=200):
    if p.suffix == ".zarr" or (p / ".zattrs").exists():
        import zarr
        arr = zarr.open(str(p), mode="r")
        a0 = arr["0"] if "0" in arr else arr
        d = a0.shape[0]
        s = max(0, (d - depth) // 2)
        vol = np.asarray(a0[s:s + depth])            # D x H x W uint8
        stack = np.ascontiguousarray(np.clip(vol, 0, clip_max).astype(np.uint8).transpose(1, 2, 0))
        return stack, {"source": "zarr", "depth_total": int(d), "layer_start": int(s)}
    return read_stack(p, depth=depth, clip_max=clip_max), {"source": "layers"}

model = InkDetector.from_pretrained(a.model)
import torch
from ink8um.inference import coverage_mask, tile_positions, gkern
@torch.inference_mode()
def predict_norm(model, stack, reverse, stride, batch_size, progress=None):
    """Same tiles/model/fp16 as the released predict_stack, but weights normalised: sum(p*w)/sum(w)."""
    ts = int(model.tile_size)
    if reverse: stack = np.ascontiguousarray(stack[..., ::-1])
    H, W = stack.shape[:2]
    pts = tile_positions(coverage_mask(stack), ts, stride)
    num = np.zeros((H, W), np.float32); den = np.zeros((H, W), np.float32)
    w = gkern(ts, 1); w = (w / w.max()).astype(np.float32)
    model = model.cuda().eval()
    for i in range(0, len(pts), batch_size):
        b = pts[i:i + batch_size]
        x = torch.from_numpy(np.stack([np.ascontiguousarray(stack[y:y + ts, x0:x0 + ts].transpose(2, 0, 1)) for x0, y in b])).cuda().float().mul_(1 / 255.0)
        with torch.autocast("cuda"):
            pr = torch.sigmoid(model(x)).float()
        if pr.shape[-2:] != (ts, ts): pr = torch.nn.functional.interpolate(pr, size=(ts, ts), mode="bilinear")
        pr = pr[:, 0].cpu().numpy()
        for p_, (x0, y) in zip(pr, b):
            num[y:y + ts, x0:x0 + ts] += p_ * w; den[y:y + ts, x0:x0 + ts] += w
        if progress: progress(min(i + batch_size, len(pts)), len(pts))
    out = np.divide(num, den, out=np.zeros_like(num), where=den > 1e-6)
    return np.clip(out, 0, 1)
print(f"model {a.model} in_depth={model.in_depth} reverse_default={model.reverse_layers}", flush=True)
for inp, outp in zip(a.input, a.out):
    inp, outp = Path(inp), Path(outp)
    outp.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    stack, info = load_stack(inp)
    if a.crop:
        r0, r1, c0, c1 = a.crop
        stack = np.ascontiguousarray(stack[r0:r1, c0:c1]); info["crop"] = a.crop
    print(f"{inp}: stack {stack.shape} read in {time.time()-t0:.0f}s {info}", flush=True)
    orders = ["fwd", "rev"] if a.order == "both" else [a.order]
    if a.reverse_auto:
        ra = json.load(open(a.reverse_auto))
        if str(inp) in ra: orders = ["rev" if ra[str(inp)] else "fwd"]
    for o in orders:
        t1 = time.time()
        last = [0.0]
        def prog(done, total):
            if time.time() - last[0] > 60 or done == total:
                last[0] = time.time(); print(f"   {o} {done}/{total} tiles ({time.time()-t1:.0f}s)", flush=True)
        if a.norm_blend:
            pred = predict_norm(model, stack, reverse=(o == "rev"), stride=a.stride, batch_size=a.batch, progress=prog)
        else:
            pred = predict_stack(model, stack, reverse=(o == "rev"), stride=a.stride, batch_size=a.batch,
                                 num_workers=a.workers, progress=prog)
        save_prediction(pred, Path(f"{outp}_{o}.png"))
        save_prediction(pred, Path(f"{outp}_{o}.tif"))
        h, w = pred.shape
        cv2.imwrite(f"{outp}_{o}_prev.jpg", cv2.resize((pred * 255).astype(np.uint8), (w // 4, h // 4), interpolation=cv2.INTER_AREA))
        meta = {"input": str(inp), "order": o, "stride": a.stride, "model": a.model, "shape": [h, w],
                "mean": float(pred.mean()), "max": float(pred.max()), "secs": round(time.time() - t1, 1), **info}
        Path(f"{outp}_{o}.json").write_text(json.dumps(meta, indent=1))
        print(f"   {o}: done {time.time()-t1:.0f}s mean={pred.mean():.4f} max={pred.max():.3f}", flush=True)
