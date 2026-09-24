## Arm A: render check (our render vs the team's 9.366 um surface volume, 512x512 centre crop, all 28 layers)

| segment | shape (ours = team) | corr, same layer order | corr, reversed order | identical voxels |
|---|---|---|---|---|
| w00 | 28x4220x4760 (same) | 0.999998 | 0.093 | 99.4 % |
| ag896 | 28x4640x4720 (same) | 0.999998 | 0.062 | 99.3 % |
| ag405 | 28x3760x4900 (same) | 0.999998 | 0.028 | 99.4 % |

## Arm A: readouts per map (R1 row score, R2 r vs the team map and the max of its 8 shifted nulls, R4 pixel AUC vs the team labels)

| segment | map | R1 row score | period mm | angle deg | R2 r | R2 null max | R2 > null | R4 AUC | R1 > 28.7 AND R2 > null |
|---|---|---|---|---|---|---|---|---|---|
| w00 | mean2_forward | 13.5 | 5.72 | -66.3 | 0.541 | 0.104 | yes | 0.794 | no |
| w00 | mean2_reverse | 12.5 | 7.38 | -100.0 | 0.140 | 0.145 | no | 0.478 | no |
| w00 | mean14_forward | 10.1 | 5.72 | -66.3 | 0.555 | 0.126 | yes | 0.813 | no |
| w00 | mean14_reverse | 10.8 | 5.72 | -113.7 | 0.163 | 0.130 | yes | 0.543 | no |
| w00 | hybrid_3d2d-seed42_step-010000_forward | 9.8 | 5.72 | -66.3 | 0.501 | 0.101 | yes | 0.766 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-010000_reverse | 8.4 | 4.01 | -32.3 | 0.121 | 0.153 | no | 0.523 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-020000_forward | 8.0 | 7.38 | -80.0 | 0.426 | 0.098 | yes | 0.765 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-020000_reverse | 8.2 | 3.0 | -73.7 | 0.040 | 0.108 | no | 0.573 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-030000_forward | 15.2 | 7.38 | -100.0 | 0.515 | 0.117 | yes | 0.771 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-030000_reverse | 8.8 | 4.09 | -101.0 | 0.065 | 0.168 | no | 0.539 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-040000_forward | 15.2 | 5.72 | -66.3 | 0.486 | 0.089 | yes | 0.761 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-040000_reverse | 13.0 | 5.39 | -120.3 | 0.075 | 0.133 | no | 0.507 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-050000_forward | 10.0 | 4.64 | -29.7 | 0.411 | 0.127 | yes | 0.747 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-050000_reverse | 11.4 | 4.35 | -35.5 | 0.132 | 0.111 | yes | 0.493 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-060000_forward | 16.6 | 5.72 | -66.3 | 0.474 | 0.095 | yes | 0.759 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-060000_reverse | 15.8 | 3.09 | -98.3 | 0.127 | 0.106 | yes | 0.511 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-075000_forward | 16.2 | 5.72 | -66.3 | 0.481 | 0.093 | yes | 0.748 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed42_step-075000_reverse | 16.5 | 7.38 | -100.0 | 0.139 | 0.148 | no | 0.502 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-010000_forward | 11.9 | 7.38 | -100.0 | 0.434 | 0.080 | yes | 0.715 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-010000_reverse | 11.1 | 4.78 | -116.6 | 0.105 | 0.102 | yes | 0.523 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-020000_forward | 11.0 | 4.01 | -147.7 | 0.497 | 0.096 | yes | 0.778 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-020000_reverse | 9.4 | 3.36 | -99.1 | 0.086 | 0.090 | no | 0.469 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-030000_forward | 8.1 | 3.4 | -85.4 | 0.389 | 0.082 | yes | 0.702 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-030000_reverse | 10.8 | 3.73 | -85.0 | 0.060 | 0.103 | no | 0.542 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-040000_forward | 10.3 | 7.49 | -90.0 | 0.447 | 0.138 | yes | 0.718 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-040000_reverse | 10.8 | 3.31 | -103.5 | 0.194 | 0.155 | yes | 0.536 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-050000_forward | 11.3 | 5.31 | -82.9 | 0.523 | 0.148 | yes | 0.821 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-050000_reverse | 6.2 | 4.06 | -40.5 | 0.165 | 0.107 | yes | 0.576 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-060000_forward | 7.3 | 7.38 | -80.0 | 0.447 | 0.133 | yes | 0.739 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-060000_reverse | 7.1 | 4.35 | -35.5 | 0.188 | 0.120 | yes | 0.584 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-075000_forward | 10.9 | 5.31 | -82.9 | 0.518 | 0.141 | yes | 0.772 | no (single checkpoint, not a criterion map) |
| w00 | hybrid_3d2d-seed43_step-075000_reverse | 8.6 | 4.06 | -40.5 | 0.150 | 0.126 | yes | 0.599 | no (single checkpoint, not a criterion map) |
| ag896 | mean2_forward | 12.2 | 5.67 | -90.0 | 0.601 | 0.126 | yes | 0.743 | no |
| ag896 | mean2_reverse | 10.0 | 4.39 | -84.0 | 0.096 | 0.177 | no | 0.570 | no |
| ag896 | mean14_forward | 13.8 | 5.67 | -90.0 | 0.603 | 0.121 | yes | 0.756 | no |
| ag896 | mean14_reverse | 15.4 | 3.6 | -85.1 | 0.092 | 0.159 | no | 0.585 | no |
| ag896 | hybrid_3d2d-seed42_step-010000_forward | 12.9 | 5.67 | -90.0 | 0.597 | 0.100 | yes | 0.751 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-010000_reverse | 10.3 | 2.6 | -23.1 | 0.081 | 0.089 | no | 0.533 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-020000_forward | 10.5 | 4.49 | -64.9 | 0.416 | 0.116 | yes | 0.710 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-020000_reverse | 12.9 | 6.54 | -98.9 | -0.007 | 0.121 | no | 0.527 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-030000_forward | 11.2 | 5.67 | -90.0 | 0.509 | 0.126 | yes | 0.730 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-030000_reverse | 13.0 | 4.93 | -83.3 | -0.038 | 0.201 | no | 0.577 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-040000_forward | 11.8 | 7.81 | -100.6 | 0.540 | 0.096 | yes | 0.738 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-040000_reverse | 15.9 | 6.54 | -98.9 | 0.017 | 0.152 | no | 0.577 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-050000_forward | 7.8 | 5.21 | -128.0 | 0.473 | 0.118 | yes | 0.695 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-050000_reverse | 11.6 | 5.16 | -148.7 | 0.105 | 0.119 | no | 0.542 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-060000_forward | 10.3 | 5.67 | -90.0 | 0.522 | 0.096 | yes | 0.706 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-060000_reverse | 15.3 | 3.6 | -85.1 | 0.052 | 0.093 | no | 0.556 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-075000_forward | 14.8 | 5.67 | -90.0 | 0.556 | 0.096 | yes | 0.719 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed42_step-075000_reverse | 9.6 | 6.54 | -98.9 | 0.073 | 0.142 | no | 0.568 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-010000_forward | 11.4 | 3.6 | -94.9 | 0.532 | 0.079 | yes | 0.737 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-010000_reverse | 13.2 | 4.71 | -123.8 | 0.047 | 0.074 | no | 0.518 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-020000_forward | 12.5 | 3.3 | -94.5 | 0.519 | 0.137 | yes | 0.718 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-020000_reverse | 7.3 | 4.42 | -128.8 | 0.091 | 0.156 | no | 0.547 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-030000_forward | 13.3 | 5.62 | -82.4 | 0.465 | 0.153 | yes | 0.660 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-030000_reverse | 14.7 | 3.95 | -84.6 | 0.089 | 0.176 | no | 0.573 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-040000_forward | 10.5 | 5.62 | -82.4 | 0.472 | 0.090 | yes | 0.712 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-040000_reverse | 14.3 | 3.3 | -85.5 | 0.154 | 0.069 | yes | 0.555 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-050000_forward | 9.4 | 5.21 | -128.0 | 0.497 | 0.155 | yes | 0.711 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-050000_reverse | 7.6 | 3.3 | -85.5 | 0.077 | 0.167 | no | 0.594 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-060000_forward | 7.7 | 3.27 | -81.1 | 0.477 | 0.079 | yes | 0.698 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-060000_reverse | 10.2 | 3.3 | -85.5 | 0.075 | 0.145 | no | 0.534 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-075000_forward | 10.7 | 5.67 | -90.0 | 0.528 | 0.098 | yes | 0.680 | no (single checkpoint, not a criterion map) |
| ag896 | hybrid_3d2d-seed43_step-075000_reverse | 9.4 | 3.3 | -85.5 | 0.096 | 0.198 | no | 0.552 | no (single checkpoint, not a criterion map) |
| ag405 | mean2_forward | 57.8 | 6.56 | -81.4 | 0.602 | 0.099 | yes | 0.757 | **yes** |
| ag405 | mean2_reverse | 6.3 | 4.15 | -131.3 | 0.121 | 0.077 | yes | 0.616 | no |
| ag405 | mean14_forward | 52.8 | 6.56 | -81.4 | 0.611 | 0.112 | yes | 0.761 | **yes** |
| ag405 | mean14_reverse | 11.1 | 3.68 | -90.0 | 0.137 | 0.079 | yes | 0.660 | no |
| ag405 | hybrid_3d2d-seed42_step-010000_forward | 25.0 | 6.56 | -81.4 | 0.518 | 0.065 | yes | 0.704 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-010000_reverse | 14.4 | 3.67 | -85.2 | 0.139 | 0.079 | yes | 0.626 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-020000_forward | 42.1 | 6.56 | -81.4 | 0.403 | 0.059 | yes | 0.700 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-020000_reverse | 10.0 | 3.68 | -90.0 | 0.095 | 0.112 | no | 0.648 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-030000_forward | 46.5 | 6.56 | -81.4 | 0.488 | 0.044 | yes | 0.737 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-030000_reverse | 7.6 | 3.67 | -85.2 | 0.097 | 0.051 | yes | 0.632 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-040000_forward | 29.0 | 6.56 | -81.4 | 0.520 | 0.107 | yes | 0.725 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-040000_reverse | 14.4 | 3.67 | -85.2 | 0.098 | 0.098 | yes | 0.641 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-050000_forward | 27.3 | 6.56 | -81.4 | 0.460 | 0.033 | yes | 0.714 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-050000_reverse | 17.5 | 3.67 | -85.2 | 0.164 | 0.121 | yes | 0.608 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-060000_forward | 46.8 | 6.56 | -81.4 | 0.537 | 0.084 | yes | 0.723 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-060000_reverse | 11.2 | 3.67 | -85.2 | 0.168 | 0.116 | yes | 0.602 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-075000_forward | 44.3 | 6.56 | -81.4 | 0.520 | 0.069 | yes | 0.750 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed42_step-075000_reverse | 6.9 | 4.94 | -116.7 | 0.152 | 0.097 | yes | 0.601 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-010000_forward | 31.9 | 6.56 | -81.4 | 0.476 | 0.088 | yes | 0.700 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-010000_reverse | 8.5 | 3.67 | -94.8 | 0.037 | 0.073 | no | 0.592 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-020000_forward | 45.8 | 6.56 | -81.4 | 0.541 | 0.110 | yes | 0.718 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-020000_reverse | 9.3 | 3.49 | -108.5 | 0.039 | 0.064 | no | 0.602 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-030000_forward | 29.0 | 6.56 | -81.4 | 0.460 | 0.131 | yes | 0.703 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-030000_reverse | 11.1 | 3.67 | -94.8 | 0.092 | 0.123 | no | 0.631 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-040000_forward | 26.2 | 6.56 | -81.4 | 0.515 | 0.152 | yes | 0.712 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-040000_reverse | 12.3 | 5.48 | -82.8 | 0.107 | 0.096 | yes | 0.633 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-050000_forward | 45.3 | 6.56 | -81.4 | 0.499 | 0.090 | yes | 0.755 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-050000_reverse | 7.3 | 7.76 | -69.4 | 0.109 | 0.080 | yes | 0.641 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-060000_forward | 26.8 | 6.56 | -81.4 | 0.482 | 0.120 | yes | 0.746 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-060000_reverse | 9.7 | 3.67 | -85.2 | 0.104 | 0.060 | yes | 0.618 | no (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-075000_forward | 41.5 | 6.56 | -81.4 | 0.536 | 0.123 | yes | 0.756 | **yes** (single checkpoint, not a criterion map) |
| ag405 | hybrid_3d2d-seed43_step-075000_reverse | 10.1 | 3.68 | -90.0 | 0.095 | 0.094 | yes | 0.617 | no (single checkpoint, not a criterion map) |

**Arm A verdict (pre-registered rule): INCONCLUSIVE.** Segments with a mean map meeting R1 > 28.7 AND R2 > null: 1 of 3 (ag405); PASS needs 2 of 3. FAIL needs every mean map on all 3 segments at R1 <= 28.7 and R2 within its null: not met (w00 R2, ag896 R2, ag405 R1 R2 above).

## POST-HOC calibration (not pre-registered): the survey row score of the TEAM's own ink map on our grid

| segment | team map R1 | period mm | angle deg | our best mean map R1 (A1/A2) |
|---|---|---|---|---|
| w00 | 34.1 | 5.99 | -73.7 | 13.5 (mean2_forward) |
| ag896 | 28.7 | 5.67 | -90.0 | 15.4 (mean14_reverse) |
| ag405 | 111.8 | 6.56 | -81.4 | 57.8 (mean2_forward) |

## Arm B (fls.py run, unmodified): readouts per patch

| job | area cm2 | R1 ink_mean_forward | R1 ink_mean_reverse | max R1 any map | on team sheet (median dist over <=60-vox overlap, vox) | share <= 5 vox | R2 fwd r / null max (overlap px at 2 vox) | B2 (i) | B2 (ii) |
|---|---|---|---|---|---|---|---|---|---|
| B1_seed0 | 17.08 | 11.3 | 6.7 | 13.0 | - | - | - | - | - |
| B1_seed6 | 13.89 | 13.1 | 11.3 | 13.1 | - | - | - | - | - |
| B1_seed9 | 15.53 | 10.2 | 17.7 | 17.7 | - | - | - | - | - |
| B2_ag405 | 14.29 | 9.3 | 7.8 | 10.0 | 26.9 | 4.8 % | 0.100 / 0.389 (184747) | no | no |
| B2_ag896 | 14.38 | 11.9 | 20.9 | 20.9 | 19.9 | 8.5 % | 0.562 / -0.088 (335195) | no | no |
| B2_w00 | 14.30 | 15.7 | 9.4 | 15.7 | 27.8 | 2.8 % | 0.605 / 0.209 (109460) | no | no |
