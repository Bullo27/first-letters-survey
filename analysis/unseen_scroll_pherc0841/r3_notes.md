# R3 notes (visual readout, PLAN.md). Each entry is written BEFORE looking at the team's map for that segment.

## 20260220213127-w00, A1 (2-checkpoint means), 2026-09-24, written after the 09:01:20Z readout (before 09:08Z), our maps only (r3_ours_*.png, 1500 px tall)
- mean2_forward: speckle of short, mostly horizontally elongated strokes over the whole surface. A few brighter isolated
  shapes stand out that look like letters: upper right (~1/6 from the top, right third) two or three shapes with
  vertical strokes side by side; centre, a round shape; lower centre, a triangular shape with a bright blob below-left;
  upper left, a curved stroke. No rows visible. Nothing readable at this scale.
- mean2_reverse: uniform speckle; no letter-like shapes, no rows.
- Would the survey's QA have flagged the forward map? The isolated shapes would have drawn a closer look; the map as a
  whole would not read as text (no rows).
- Full-resolution crops of our forward map (9.366 um/px, 11.2 x 7.5 mm, placed on our own brightest shapes):
  upper right = an arch ~2 mm wide next to a single vertical bar, a second arch-like blob to the right; lower centre =
  a diagonal stroke ~2.5 mm long with a side branch, blobs around it. Blurry; no letter identifiable with confidence.
- THEN the team's map (r3_side_team.png, same grid): clear Greek letters in ~5 horizontal rows over the right half
  (rows ~5-6 mm apart), scattered dots elsewhere. Our forward map's isolated shapes sit on some of them: the upper-right
  cluster on the team's top-right word, the triangular shape at the start of the team's bottom row, the round shape
  near the row above it. Most of the team's letters are not distinguishable from the speckle in our map, and the rows
  the team sees are not visible as rows in ours. (Scores: row 13.5 < 28.7; r_team 0.541 vs null max 0.104; AUC 0.794.)

## 20260220214732-auto_grown_20260220144552896 (ag896), A1, 2026-09-24, written after the 09:08:05Z readout (before 09:11Z), our maps only
- mean2_forward: speckle over the whole surface; a vertical band through the middle holds brighter, letter-like
  strokes: upper middle a curved shape, centre a cluster of short strokes (a horizontal bar, an angular Z-like shape,
  vertical strokes), lower middle a few angular shapes. More letter-like strokes than w00, but no rows visible and
  nothing readable.
- mean2_reverse: uniform speckle with a faint grid-like texture; no letter shapes, no rows.
- THEN the team's map: Greek letters in ~6 rows (~5.8 mm apart) across the central band, scattered dots elsewhere.
  Our forward map's brighter shapes sit on the team's strongest strokes: our horizontal bar on the team's horizontal
  stroke in the middle rows, our Z-like shape next to it on the team's letters there, our upper-middle curve on the
  team's top row, our lower angular shapes on the team's row below the middle. Rows not visible in ours; most letters
  lost in speckle. (Scores: row 12.2 < 28.7; r_team 0.601 vs null max 0.126; AUC 0.743.)
- POST-HOC calibration (team_rowscore.py): the TEAM's own map on our grid scores 34.1 on w00 (5.99 mm) and 28.7 on
  ag896 (5.67 mm, -90 deg, the same peak as ours), i.e. R1 > 28.7 is barely or not reachable on these segments even
  with the team's map; the PHerc0139 controls (71-125) had denser text.

## 20260221022814-auto_grown_20260220174252405 (ag405), A1, written after the 09:14:47Z readout, our maps only
- mean2_forward: speckle, but bright letter-like strokes line up along 2-3 horizontal lines through the middle: open
  curves (C- and reversed-C shapes), short vertical bars, horizontal bars, an angular Z-like stroke; a few more strokes
  above and below. Reads as "possible rows of letters" at first sight: the survey's QA would have flagged this map for
  a closer look. Nothing readable.
- mean2_reverse: speckle with a grid-like texture, a few brighter blobs; no letter shapes, no rows.
- THEN the team's map: two very clear rows of Greek letters through the middle (5-7 letters each, readable), weaker
  rows above and below. Our forward map's two lines of strokes are those two rows: our blobs/curves sit on the team's
  letters one by one (first row: our blobs on the team's first four letters; second row: our vertical bar, curves and
  horizontal bar on the team's letters, the horizontal bar on the team's two T-like tops). Fainter and fragmented in
  ours; not readable without the team's map. (Scores: row 57.8 > 28.7, same peak 6.56 mm / -81.4 deg as the team's;
  r_team 0.602 vs null max 0.099; AUC 0.757.)
- POST-HOC calibration: the team's own ag405 map scores 111.8 (6.56 mm, -81.4 deg). Ours/team row score, A1 forward
  mean: w00 13.5/34.1, ag896 12.2/28.7, ag405 57.8/111.8.

## A2 (14-checkpoint means). NOTE: the team's maps were already seen during A1, so A2 notes are not blind.
- w00 mean14_forward (after the 09:49:29Z readout): like mean2_forward with finer, smoother background speckle and a
  faint grid texture; the same isolated shapes, a little crisper (upper-right arch + bar pair, centre shape, lower
  triangle, upper-left curved stroke). No rows; nothing readable. (row 10.1, r_team 0.555 vs null 0.126, AUC 0.813)

## B2_ag896 (full tool from the informed seed; 14.38 cm2), after the 09:53:54Z report, our maps only (fls.py PNGs)
- ink_mean_forward: dense, bright speckle over the whole patch (23 % of pixels > 0.5, vs 7 % in arm A's maps of the
  team surfaces); a few curved strokes near the centre (the seed's area) and a faint large ring at upper centre; no
  rows; nothing that stands out from the speckle the way arm A's shapes did. Looks like the survey's speckle maps.
- ink_mean_reverse: dense speckle, a faint diagonal band and vertical texture; no rows, no letters.
- Geometry: off the team sheet (median 19.9 vox over the overlap; 5.6 vox within 100 vox of the seed, drifting to ~30
  vox at 1000-2000 vox). On the ~1.2 cm2 within 5 vox of the team sheet: r_team 0.562 (forward), null not reliable there
  (most 10-20 mm shifts leave < 1000 overlapping px; the remaining null values are negative).
- THEN (r3_b_views.py: team map carried through the geometry, distance map): our surface is near the team sheet only
  in the centre/right, in patches with thin crossing lines (it weaves across the team sheet rather than following it),
  and far from it on the left. Where it is within 5 vox (centre), the team's map has letters and our forward map has a
  few strokes at the same places (r 0.562 there); over the whole patch they do not stand out from the speckle.

## B2_w00 (full tool from the informed seed; 14.30 cm2), after the 10:03:44Z report, our maps only (fls.py PNGs)
- ink_mean_forward: dense bright speckle over the whole patch (frac > 0.5: 25 %); a few curved strokes near the centre
  (an arc, a reversed-C curve, a diagonal stroke), a dark vertical band upper centre, a bright horizontal band lower
  left; no rows, nothing letter-like standing out. Survey-like.
- ink_mean_reverse: dense speckle, a dark vertical band, a ring-like shape upper centre; no rows, no letters.
- THEN (r3_b_views.py): the patch lies near the team sheet only from the upper left to the centre, and within 5 vox only
  in a small central area (~0.4 cm2) plus a thin crossing line; the rest is far off (the right half and bottom extend
  beyond the team mesh). In that small area the team's map has letters, and our reversed-C curve sits on one of them
  (r_team 0.605 vs null max 0.209 there; reverse 0.340 vs 0.136). Off the sheet: median 27.8 vox over the overlap.

## B2_ag405 (full tool from the informed seed; 14.29 cm2), after the 10:52:21Z report, our maps only (fls.py PNGs)
- ink_mean_forward: dense speckle over the whole patch; one small bright stroke near the centre (seed area); no rows,
  no letter-like shapes standing out. Nothing like arm A's ag405 map (letter-like strokes on 2-3 lines).
- ink_mean_reverse: speckle with faint vertical banding; no rows, no letters.
- THEN (r3_b_views.py distance map): the patch is off the team sheet almost everywhere; within 5 vox only along thin
  crossing lines and small patches on the right; dark (far) around the centre, i.e. the seed itself (snapped 7.73 vox
  from the team mesh point, the largest snap of the three) likely sat on a neighbouring sheet. On the <=5-vox overlap
  (184,747 px at 2 vox) r_team 0.100 vs null max 0.389: no agreement there (crossing lines, not a followed sheet).
- A2 ag405 mean14_forward (11:01:11Z): row 52.8 (6.56 mm), r_team 0.611 vs null 0.112, AUC 0.761 (A1: 57.8).

## B1_seed9 (blind, survey seed rule zf .5 rf .7; 15.53 cm2), after the 11:13:15Z report
- ink_mean_forward: speckle with curved, swirl-like arcs in the upper part (the survey's "swirls" class), dark vertical
  bands in the upper half; no rows; nothing letter-like. R1: mean fwd 10.2, rev 17.7 (max single 16.7).

## B1_seed0 (blind, zf .3 rf .5; 17.08 cm2), after the 11:53:42Z report
- ink_mean_forward: speckle, dark vertical bands, a brighter blotchy area lower right, a bright line at the left edge
  (render boundary); no rows; nothing letter-like. R1: mean fwd 11.3, rev 6.7 (max single 13.0).

## B1_seed6 (blind, zf .5 rf .5, the fls.py default; 13.89 cm2), after the 12:05:42Z report
- ink_mean_forward: speckle; upper right: a dark hole with a stepped edge (hole-rim artifact), bright blotches, blocky
  (chunk-like) edges; no rows; nothing letter-like. R1: mean fwd 13.1, rev 11.3 (max single 12.6).
