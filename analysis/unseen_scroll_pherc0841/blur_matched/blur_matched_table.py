"""blur_matched_table.py: prints the markdown table and the summary numbers from blur_matched.json (no hand-typed numbers)."""
import json, statistics
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
d = json.load(open(f'{T}/blur_matched.json'))
short = {'20260220213127-w00': 'w00', '20260220214732-auto_grown_20260220144552896': 'ag144',
         '20260221022814-auto_grown_20260220174252405': 'ag174'}
SIGMAS = ['0', '2', '4']
print('| segment | blur σ (px) | 14 single checkpoints, min–median–max | 14-checkpoint mean | mean ÷ best single | mean ÷ median single |')
print('|---|---|---|---|---|---|')
ratios = {s: [] for s in SIGMAS}; ratios_med = {s: [] for s in SIGMAS}; means = {s: [] for s in SIGMAS}; singles_all = {s: [] for s in SIGMAS}
for seg, R in d.items():
    singles = {k: v for k, v in R['hp_r'].items() if k.startswith('seed')}
    assert len(singles) == 14, len(singles)
    for s in SIGMAS:
        v = sorted(x[s] for x in singles.values()); m = R['hp_r']['mean14'][s]
        med = statistics.median(v)
        ratios[s].append(m / v[-1]); ratios_med[s].append(m / med); means[s].append(m); singles_all[s] += v
        print(f'| {short[seg]} | {s} | {v[0]:.3f}–{med:.3f}–{v[-1]:.3f} | {m:.3f} | {m / v[-1]:.2f} | {m / med:.2f} |')
print()
for s in SIGMAS:
    print(f'sigma {s}: mean14 {min(means[s]):.3f}-{max(means[s]):.3f}; singles {min(singles_all[s]):.3f}-{max(singles_all[s]):.3f}; '
          f'mean/best {min(ratios[s]):.2f}-{max(ratios[s]):.2f}; mean/median {min(ratios_med[s]):.2f}-{max(ratios_med[s]):.2f}')
print()
for seg, R in d.items():
    print(short[seg], 'common_px', R['common_px'], 'core_px', R['core_px'], 'nulls', json.dumps(R['null_max_abs']))
    print('   sigma 0 check vs hp_score_posthoc.json:', {k: R['hp_r'][k]['0'] for k in ('seed42_step-075000', 'seed43_step-020000', 'mean2', 'mean14')})
    print('   mean14 all sigmas:', R['hp_r']['mean14'])
    best_single_any = max(max(v.values()) for k, v in R['hp_r'].items() if k.startswith('seed'))
    print('   best single at any sigma (<=8):', best_single_any)
