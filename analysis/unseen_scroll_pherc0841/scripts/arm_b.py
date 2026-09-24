"""arm_b.py [--par 2] [job ...]: arm B of PLAN.md. Runs the published fls.py, unmodified, on PHerc0841 (FLS_WORK holds
the catalog row for it), 100 generations, default checkpoints, both directions. Jobs:
  B1_seed9, B1_seed0, B1_seed6   blind: the survey's seed rule (seed indices from `fls.py seeds`, seeds_blind.txt)
  B2_w00, B2_ag896, B2_ag405     informed: seeds_informed.json (densest team text per segment)
Each job resumes where it stopped (fls.py skips finished steps). Logs: armB/<job>.log"""
import argparse, json, os, subprocess, sys, time, concurrent.futures as cf
T = '/media/bullo/Storage/vesuvius_work/unseen_test'; FS = '/media/bullo/Storage/vesuvius_work/fl_survey'
ENV = dict(os.environ, FLS_WORK=f'{T}/fls_work', VC_BIN='/home/bullo/vesuvius-work/villa/build/rt/bin', FLS_CKPTS=f'{FS}/checkpoints/ink_9um',
           VC3D_CONFIG_DIR=f'{T}/vc3d_cfg', PYTHONPATH='/home/bullo/vesuvius-work/villa/vesuvius/src', FLS_NO_CUDNN='1')
inf = {s['segment'].split('-', 1)[1]: s for s in json.load(open(f'{T}/seeds_informed.json'))}
short = {'w00': 'w00', 'ag896': 'auto_grown_20260220144552896', 'ag405': 'auto_grown_20260220174252405'}
JOBS = {'B1_seed9': ['--seed-index', '9'], 'B1_seed0': ['--seed-index', '0'], 'B1_seed6': ['--seed-index', '6']}
for k, full in short.items():
    s = inf[full]; JOBS[f'B2_{k}'] = ['--seed', str(s['x']), str(s['y']), str(s['z'])]
ap = argparse.ArgumentParser(); ap.add_argument('--par', type=int, default=2); ap.add_argument('jobs', nargs='*'); a = ap.parse_args()
names = a.jobs or list(JOBS)
os.makedirs(f'{T}/armB', exist_ok=True); os.makedirs(f'{T}/vc3d_cfg', exist_ok=True)
def run(name):
    cmd = ['/home/bullo/vesuvius-work/venv/bin/python', f'{FS}/repo/fls.py', 'run', '--scroll', 'PHerc0841', '--gens', '100', '--name', name] + JOBS[name]
    t = time.time()
    with open(f'{T}/armB/{name}.log', 'a') as f:
        f.write(f'# {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} {" ".join(cmd)}\n'); f.flush()
        rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=ENV).returncode
    line = f'{time.strftime("%H:%M:%SZ", time.gmtime())} {name} rc={rc} wall={time.time() - t:.0f}s'
    print(line, flush=True); open(f'{T}/armB/armB.log', 'a').write(line + '\n')
    return rc
with cf.ThreadPoolExecutor(a.par) as ex:
    list(ex.map(run, names))
