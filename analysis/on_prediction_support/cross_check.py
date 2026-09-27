"""cross_check.py: support_check.py against villa PR #1906's own tracer.

Regrows a short patch several times from the seed of one survey patch with fls.py's grow() (the GrowPatch parameters,
thread_limit 8) and the vc_grow_seg_from_seed built from #1906, compares the support the tracer prints in each run
with support_check.check() on the surface it saved, and adds each surface's hit-rate profile along the normal.
Usage: VC_BIN=<directory with #1906's vc_grow_seg_from_seed> python cross_check.py v3/PHerc0211/s0 30 5 [build tag]
Output: cross_check_<build tag>.json next to this script; the tracer's logs stay under $FLS_WORK/cross_check/.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [REPO, HERE]
import fls
import support_check as SC

key, gens, runs = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tag = sys.argv[4] if len(sys.argv) > 4 else ''          # keeps runs of different builds apart
R = json.load(open(os.path.join(REPO, 'results', 'results.json')))
p = next(q for q in R['patches'] if SC.key_of(q) == key)
res = {'build': tag or None, 'seed_of': key, 'surface_of_seed_patch': p['visual_qa']['surface'], 'generations': gens, 'runs': []}
for i in range(1, runs + 1):
    out = os.path.join(fls.WORK, 'cross_check', f"{key.replace('/', '_')}_g{gens}_run{i}{'_' + tag if tag else ''}")
    seg = fls.grow(p['scroll'], p['seed']['x'], p['seed']['y'], p['seed']['z'], gens, 8, out)
    log = open(os.path.join(out, 'grow.log')).read()
    m = re.search(r'on-prediction support: ([\d.]+)% \((\d+)/(\d+) vertices[^\n]*', log)
    if not m:
        sys.exit('the tracer printed no on-prediction support: is VC_BIN the tracer built from #1906?')
    warns = [l for l in log.splitlines() if l.startswith('WARNING: vc_grow_seg_from_seed: on-prediction')]
    warning = next((l for l in warns if 'below min_on_prediction_support' in l), None)       # the absolute check
    relative = next((l for l in warns if 'no better than the background' in l), None)        # 3787b68f1 and later
    b = re.search(r'background ([\d.]+)% over (\d+) random points', m.group(0))
    ours = SC.check(seg, SC.PRED[p['volume']]['surface_prediction'])
    run = {'area_cm2': json.load(open(os.path.join(seg, 'meta.json'))).get('area_cm2'),
           'tracer_line': m.group(0), 'tracer_warning': warning, 'tracer_relative_warning': relative,
           'tracer_background_pct': float(b.group(1)) if b else None,
           'tracer_on_total': [int(m.group(2)), int(m.group(3))], 'ours_on_total': [ours['on'], ours['total']],
           'identical': [int(m.group(2)), int(m.group(3))] == [ours['on'], ours['total']], 'ours': ours}
    res['runs'].append(run)
    print(f"run {i}: {run['tracer_line']} | absolute warning: {bool(warning)} | relative warning: {bool(relative)} | ours {ours['on']}/{ours['total']} | "
          f"profile 0: {ours['profile_pct_by_normal_offset'][0]} %, +-5..6: "
          f"{[ours['profile_pct_by_normal_offset'][k] for k in (-6, -5, 5, 6)]}", flush=True)
s = [r['ours']['support_pct'] for r in res['runs']]
res['summary'] = {'support_pct_min_max': [min(s), max(s)], 'warnings': sum(bool(r['tracer_warning']) for r in res['runs']),
                  'relative_warnings': sum(bool(r['tracer_relative_warning']) for r in res['runs']),
                  'all_identical': all(r['identical'] for r in res['runs'])}
bgs = [r['tracer_background_pct'] for r in res['runs'] if r['tracer_background_pct'] is not None]
if bgs:
    res['summary']['tracer_background_pct_min_max'] = [min(bgs), max(bgs)]
json.dump(res, open(os.path.join(HERE, f"cross_check{'_' + tag if tag else ''}.json"), 'w'), indent=1)
print(res['summary'])
