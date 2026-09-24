"""make_results_tables.py: the numeric tables of RESULTS.md, generated from armA_results.json, armB_results.json and
team_rowscore.json (no number typed by hand), plus the pre-registered verdicts computed from them. Writes
results_tables.md."""
import json, os
T = '/media/bullo/Storage/vesuvius_work/unseen_test'
A = json.load(open(f'{T}/armA_results.json')); B = json.load(open(f'{T}/armB_results.json')) if os.path.exists(f'{T}/armB_results.json') else {}
TR = json.load(open(f'{T}/team_rowscore.json')) if os.path.exists(f'{T}/team_rowscore.json') else {}
THR = 28.7
SHORT = {'20260220213127-w00': 'w00', '20260220214732-auto_grown_20260220144552896': 'ag896', '20260221022814-auto_grown_20260220174252405': 'ag405'}
L = []
def f(x, n=3): return '-' if x is None else (f'{x:.{n}f}' if isinstance(x, float) else str(x))
L.append('## Arm A: render check (our render vs the team\'s 9.366 um surface volume, 512x512 centre crop, all 28 layers)\n')
L.append('| segment | shape (ours = team) | corr, same layer order | corr, reversed order | identical voxels |\n|---|---|---|---|---|')
for seg, R in A.items():
    rc = R['render_check']
    L.append(f"| {SHORT[seg]} | {'x'.join(map(str, rc['shape_ours']))} ({'same' if rc['shape_ours'] == rc['shape_team'] else 'DIFFERENT'}) | {rc['corr_same_order']:.6f} | {rc['corr_reversed_order']:.3f} | {100 * rc['identical_fraction']:.1f} % |")
L.append('\n## Arm A: readouts per map (R1 row score, R2 r vs the team map and the max of its 8 shifted nulls, R4 pixel AUC vs the team labels)\n')
L.append('| segment | map | R1 row score | period mm | angle deg | R2 r | R2 null max | R2 > null | R4 AUC | R1 > 28.7 AND R2 > null |\n|---|---|---|---|---|---|---|---|---|---|')
order = ['mean2_forward', 'mean2_reverse', 'mean14_forward', 'mean14_reverse']
verdict = {}
for seg, R in A.items():
    maps = R['maps']; names = [n for n in order if n in maps] + sorted(n for n in maps if n not in order)
    ok_any = False; r1_any = False; r2_any = False
    for n in names:
        s = maps[n]; row = s['row'] or {}
        r1 = (row.get('score') or 0) > THR; r2 = s['r_team'] is not None and s['r_null_max'] is not None and s['r_team'] > s['r_null_max']
        both = r1 and r2
        if n.startswith('mean'):
            ok_any |= both; r1_any |= r1; r2_any |= r2
        L.append(f"| {SHORT[seg]} | {n} | {row.get('score')} | {row.get('period_mm')} | {row.get('angle_deg')} | {f(s['r_team'])} | {f(s['r_null_max'])} | {'yes' if r2 else 'no'} | {f(s['auc_labels'])} | {'**yes**' if both else 'no'}{'' if n.startswith('mean') else ' (single checkpoint, not a criterion map)'} |")
    verdict[seg] = {'pass_map': ok_any, 'any_mean_R1': r1_any, 'any_mean_R2': r2_any}
n_pass = sum(v['pass_map'] for v in verdict.values())
all_fail = all(not v['any_mean_R1'] and not v['any_mean_R2'] for v in verdict.values())
va = 'PASS' if n_pass >= 2 else ('FAIL' if all_fail and len(verdict) == 3 else 'INCONCLUSIVE')
L.append(f"\n**Arm A verdict (pre-registered rule): {va}.** Segments with a mean map meeting R1 > 28.7 AND R2 > null: "
         f"{n_pass} of {len(verdict)} ({', '.join(SHORT[s] for s, v in verdict.items() if v['pass_map']) or 'none'}); PASS needs 2 of 3. "
         f"FAIL needs every mean map on all 3 segments at R1 <= 28.7 and R2 within its null: "
         f"{'met' if all_fail else 'not met (' + ', '.join(SHORT[s] + (' R1' if v['any_mean_R1'] else '') + (' R2' if v['any_mean_R2'] else '') for s, v in verdict.items() if v['any_mean_R1'] or v['any_mean_R2']) + ' above)'}.")
if TR:
    L.append('\n## POST-HOC calibration (not pre-registered): the survey row score of the TEAM\'s own ink map on our grid\n')
    L.append('| segment | team map R1 | period mm | angle deg | our best mean map R1 (A1/A2) |\n|---|---|---|---|---|')
    for seg, t in TR.items():
        best = max(((A[seg]['maps'][n]['row'] or {}).get('score') or 0, n) for n in A[seg]['maps'] if n.startswith('mean'))
        L.append(f"| {SHORT[seg]} | {t.get('score')} | {t.get('period_mm')} | {t.get('angle_deg')} | {best[0]} ({best[1]}) |")
if B:
    L.append('\n## Arm B (fls.py run, unmodified): readouts per patch\n')
    L.append('| job | area cm2 | R1 ink_mean_forward | R1 ink_mean_reverse | max R1 any map | on team sheet (median dist over <=60-vox overlap, vox) | share <= 5 vox | R2 fwd r / null max (overlap px at 2 vox) | B2 (i) | B2 (ii) |\n|---|---|---|---|---|---|---|---|---|---|')
    for job in sorted(B):
        R = B[job]; rows = R.get('row', {})
        def sc(n): return (rows.get(n) or {}).get('score')
        mx = max(((v or {}).get('score') or 0) for v in rows.values()) if rows else None
        if job.startswith('B2_'):
            d = R['dist_vox']; rt = R['r_team'].get('ink_mean_forward.tif', {})
            i_ok = R['on_sheet']
            def both(n):                                    # the arm A test on ONE map: R1 > 28.7 and R2 above its null
                v = R['r_team'].get(n, {})
                return ((rows.get(n) or {}).get('score') or 0) > THR and v.get('r') is not None and v.get('r_null_max') is not None and v['r'] > v['r_null_max']
            ii_ok = both('ink_mean_forward.tif') or both('ink_mean_reverse.tif')
            L.append(f"| {job} | {R['area_cm2']:.2f} | {sc('ink_mean_forward.tif')} | {sc('ink_mean_reverse.tif')} | {mx} | {f(d['median_overlap'], 1)} | {100 * d['share_le5']:.1f} % | {f(rt.get('r'))} / {f(rt.get('r_null_max'))} ({rt.get('overlap_px')}) | {'yes' if i_ok else 'no'} | {'yes' if ii_ok else 'no'} |")
        else:
            L.append(f"| {job} | {R['area_cm2']:.2f} | {sc('ink_mean_forward.tif')} | {sc('ink_mean_reverse.tif')} | {mx} | - | - | - | - | - |")
open(f'{T}/results_tables.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
