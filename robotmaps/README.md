# Robot occupancy-grid benchmark for grid pathfinding (Moving AI format)

> **Repository copy.** This directory holds the four building maps used in the paper (intel-lab, fr079,
> mit-cscail, longwood), their scenario files and source grids, and all scripts. Two things described below are
> not included: `wean5300` (weaker provenance, not used in the paper) and the HouseExpo maps and grids, because
> HouseExpo is derived from SUNCG and its licence for redistribution is unclear. To rebuild the 100 HouseExpo maps,
> download `HouseExpo/json.tar.gz` from the commit named below and run `scripts/houseexpo2pgm.py`, which draws
> the same 100 layouts with its default seed (their ids are in `source_grids/houseexpo/subset.txt`), and then
> `scripts/to_movingai.py`. `raw/` is not included either; the
> sources and licences of every file are listed below.


Built 2026-11-05. Everything here was produced by the scripts in `scripts/` (own Python, numpy/scipy/Pillow);
no downloaded code was built or run. Downloaded files (treated as untrusted data) are in `raw/`.

## Contents

| Path | What |
|---|---|
| `maps/real/*.map`, `*.map.scen` | 5 maps of real buildings mapped from real robot laser data (4 tier A, 1 tier B) |
| `maps/houseexpo/*.map`, `*.map.scen` | 100 HouseExpo layouts (synthetic floor plans, **not** robot data) |
| `source_grids/` | intermediate ROS-style PGM+YAML grids (before inflation), one per map; `source_grids/houseexpo/subset.txt` lists the 100 layout ids |
| `maps.csv` | one row per map: provenance, citation, license, resolution, inflation radius, sizes, free cells, component size, scenario count |
| `stats_real.json`, `stats_houseexpo.json` | the raw numbers behind `maps.csv` |
| `raw/` | downloaded source data (FLIRTLib logs, CARMEN map files, HouseExpo JSON archive, licence texts) |
| `scripts/` | `build_grid.py` (logs to grid), `carmen2pgm.py`, `houseexpo2pgm.py`, `to_movingai.py` (inflate, `.map`, `.scen`), `check_graph.py`, `make_docs.py`, `parse_log.py`, `probe.sh` |

Provenance tiers: **A** means the environment, the recording and the licence are documented by the original
repository (Radish, archived at MIT DSpace) and the file we used can be traced to that dataset. **B** means the file
is a real robot map, but it is documented only by its own embedded header, with no dataset record or publication.
**S** means synthetic.

## Real-robot maps

| map | tier | environment | res (m/cell) | inflation (cells) | size W x H | free cells | largest component | scenarios |
|---|---|---|---|---|---|---|---|---|
| intel-lab | A | Intel Research Lab, Seattle | 0.05 | 5 | 726 x 679 | 129501 | 128167 | 200 |
| fr079 | A | Univ. Freiburg, building 079 | 0.05 | 5 | 784 x 312 | 92034 | 90776 | 200 |
| mit-cscail | A | MIT CSAIL, 3rd floor | 0.05 | 5 | 1462 x 1070 | 225523 | 196688 | 200 |
| longwood | A | Longwood at Oakmont nursing home | 0.10 | 3 | 527 x 367 | 62549 | 61865 | 200 |
| wean5300 | B | "Wean 5300 Corridor" (CARMEN sample map) | 0.10 | 3 | 604 x 247 | 15824 | 15739 | 200 |

"free cells" and the size are counted after inflation and cropping. Source sizes and pre-inflation free counts are in `maps.csv`.

### intel-lab, fr079 and mit-cscail (tier A): grids built by us from SLAM-corrected logs
* **Source files:** `data/intel-lab.log`, `data/fr079.log` and `data/mit-cscail.log` from FLIRTLib,
  https://github.com/tipaldi/flirtlib (commit f608c8c486b53320a5fc701de6d70e7e803c412c). The FLIRTLib README says
  these are "the log files used in the paper". Each file holds a pose graph (`VERTEX2` and `EDGE2`) and one
  `ROBOTLASER1` scan per vertex.
* **Pose correction check:** the poses are consistent with every sequential and loop-closure constraint in the
  file. Median residuals are 0.3/1.1 cm (Intel), 0.2/0.7 cm (fr079) and 0.1/1.2 cm (CSAIL) for sequential/loop
  edges. So they are SLAM-corrected poses, not raw odometry (`scripts/check_graph.py`). FLIRTLib does not
  say which SLAM system produced them.
* **Original datasets (Radish, now archived at MIT DSpace):**
  * Intel: Radish "intel_lab", hdl:1721.1/62287. DSpace lists Dieter Fox as contributor. The Freiburg
    SLAM-evaluation page (http://ais.informatik.uni-freiburg.de/slamevaluation/datasets.php) credits the raw log
    to Dirk Haehnel.
  * fr079: Radish "fr079", hdl:1721.1/62290, contributed by Cyrill Stachniss. Recorded 2003-11-18 in
    Univ. Freiburg building 079 with a Pioneer2 and a SICK LMS.
  * mit-cscail: Radish "mit-csail-3rd-floor", hdl:1721.1/62274, contributed by Cyrill Stachniss. Recorded
    2005-12-17 on the 3rd floor of MIT CSAIL with a B21r and a SICK LMS.
* **Licence:** each DSpace record says CC0 1.0. The Radish front page (radish.sourceforge.net) says CC BY 1.0
  and asks for an acknowledgement of the data provider plus a citation of Radish. FLIRTLib is LGPL-3.0-or-later.
  Recommendation: acknowledge the provider and cite Radish anyway.
* **Citations (all verified on Crossref unless noted):**
  * A. Howard, N. Roy. *The Robotics Data Set Repository (Radish)*, 2003, http://radish.sourceforge.net/. This is
    the repository's own BibTeX; it has no DOI. The archive is at https://dspace.mit.edu/handle/1721.1/62236.
  * G. D. Tipaldi, K. O. Arras. *FLIRT - Interest regions for 2D range data*. IEEE ICRA 2010, pp. 3616-3622,
    doi:10.1109/ROBOT.2010.5509864. This is the source of the redistributed logs.
  * R. Kuemmerle, B. Steder, C. Dornhege, M. Ruhnke, G. Grisetti, C. Stachniss, A. Kleiner. *On measuring the
    accuracy of SLAM algorithms*. Autonomous Robots 27(4):387-407, 2009, doi:10.1007/s10514-009-9155-6. This is the
    standard SLAM benchmark that uses these datasets; cite it optionally.
* **Grid construction (`scripts/build_grid.py`):** 0.05 m cells, counting model as in GMapping. For every beam
  with range below the sensor maximum (50 m in these files), the endpoint cell gets a hit and every cell sampled
  every 0.025 m before the endpoint gets a visit. Each cell is counted at most once per scan. Beams with no return
  are ignored. Occupancy p = hits/visits. The PGM follows the ROS map_saver convention: 0 if p > 0.65, 254 if
  p < 0.196, 205 otherwise or if never visited.

### longwood (tier A): robot-built CARMEN map
* **Source:** `data/longwood.map` from https://github.com/LCAD-UFES/carmen_lcad (commit
  85d31fa2003086454338ccdd7bfbca2ca6971495), a fork of CARMEN (GPL-2.0). The embedded header gives author
  "nickr", date 2002-09-20, origin "longwood.large.log" and the description "Full longwood map made from two
  sets of data". The GRIDMAP chunk is 536 x 379 cells at 0.1 m.
* **Original dataset:** Radish "Longwood", hdl:1721.1/62284, contributed by Nick Roy, licence CC0 1.0. The
  record describes "The Longwood at Oakmont nursing home", a map built from two separate robot data runs (beeSoft),
  merged, at 10 cm resolution. This matches the file header.
* **Citations:** Howard & Roy 2003 (Radish) as above. M. Montemerlo, N. Roy, S. Thrun. *Perspectives on
  standardization in mobile robot programming: the Carnegie Mellon Navigation (CARMEN) Toolkit*. IROS 2003,
  pp. 2436-2441, doi:10.1109/IROS.2003.1249235. That is the package that distributes the file. I found no
  publication that describes this map itself. Pineau et al. (RAS 2003) mention only "a retirement community near
  Pittsburgh" and are not cited.
* **Conversion (`scripts/carmen2pgm.py`):** reads the GRIDMAP float probabilities (-1 = unknown) and applies the
  same 0.65 / 0.196 thresholds. The YAML origin is set to 0,0 because the original metric offset is not used.

### wean5300 (tier B, weaker provenance)
* **Source:** `data/wean5300.map` (gzip) from the same carmen_lcad commit. The header gives author "mmde", date
  2002-12-06, origin "/home/mmde/wean-map-run-1.log" and the description "Wean 5300 Corridor". So it was built from
  a robot log, presumably in CMU's Wean Hall, but that is not stated.
* It has no Radish record and I found no publication. Licence: CARMEN GPL-2.0. Cite only CARMEN (above).
  **Exclude this map if strict provenance is required.**

## HouseExpo subset (tier S)
* **Source:** https://github.com/TeaganLi/HouseExpo (commit 45e2b2505f6ea1fe49c0203f14efb7ce20b94e7c), file
  `HouseExpo/json.tar.gz` (35,126 JSON layouts). Repository licence: MIT (c) 2019 Tingguang Li.
* **Citation:** T. Li, D. Ho, C. Li, D. Zhu, C. Wang, M. Q.-H. Meng. *HouseExpo: A Large-scale 2D Indoor Layout
  Dataset for Learning-based Algorithms on Mobile Robots*. IEEE/RSJ IROS 2020, pp. 5839-5846,
  doi:10.1109/IROS45743.2020.9341284 (verified on Crossref).
* **Caveat:** HouseExpo is derived from SUNCG (S. Song et al., *Semantic Scene Completion from a Single Depth
  Image*, CVPR 2017, pp. 190-198, doi:10.1109/CVPR.2017.28). These are synthetic floor plans, not robot maps.
  SUNCG's own terms of use applied to the original data, and SUNCG distribution was discontinued. The MIT licence
  covers the HouseExpo repository, but whether it can relicense SUNCG-derived geometry is not stated.
* **Subset:** `random.Random(20201025).sample(sorted(all 35126 ids), 100)`. The ids are in
  `source_grids/houseexpo/subset.txt`.
* **Rasterisation (`scripts/houseexpo2pgm.py`):** 0.05 m cells. The grid covers the polygon's bounding box plus a
  0.5 m margin. A cell is free if its centre is inside the `verts` polygon (even-odd rule). Every cell touched by a
  polygon edge is blocked (edges sampled every 0.00625 m). Cells outside the polygon are blocked. Inflation and
  scenarios are then the same as for the real maps (radius 5 cells).
* Size statistics are in `maps.csv` (columns width, height, free_cells, largest_component_cells). Over the 100
  maps, after inflation and cropping:

  | statistic | min | median | max |
  |---|---|---|---|
  | width | 38 | 250.5 | 1059 |
  | height | 74 | 212 | 810 |
  | free cells | 3,245 | 34,474 | 547,977 |
  | largest component | 3,245 | 34,474 | 547,652 |
  | mean optimal cost | 35.5 | 143.1 | 564.0 |

  Each map has 200 scenarios.

## Conversion to Moving AI format (`scripts/to_movingai.py`), identical for all maps
1. **Free test:** p = (255 - v)/255 (negate = 0). A cell is free iff p < free_thresh from the YAML (0.196). In
   practice only value 254 is free. Occupied cells (0) and unknown cells (205) are blocked.
2. **Inflation:** robot radius 0.25 m. R = floor(0.25/res + 0.5) cells, so 5 cells at 0.05 m and 3 cells at
   0.10 m (3 cells is 0.30 m, because 2.5 rounds up). A cell becomes blocked if any blocked cell, or any position
   outside the grid, lies within Euclidean distance R (in cells, centre to centre). This is done with
   scipy.ndimage.binary_dilation and a disk structuring element.
3. **Crop:** the map is cropped to the bounding box of the remaining free cells plus a 1-cell blocked border.
   Nothing else is removed: all free components stay in the `.map`.
4. **`.map`:** `type octile`, `height H`, `width W`, `map`, then H rows. `.` is free and `@` is blocked.
   Row 0 is the top (maximum y).
5. **Component:** the largest connected free component under 8-connected moves with no corner cutting (a
   diagonal move needs both orthogonal neighbours free). This rule makes it the same as the 4-connected component
   (scipy.ndimage.label with the cross structure).
6. **`.map.scen`:** the line `version 1`, then 200 lines of
   `bucket<TAB>name.map<TAB>W<TAB>H<TAB>sx<TAB>sy<TAB>gx<TAB>gy<TAB>optimal`.
   * Coordinates: x = column, y = row.
   * Start and goal are distinct cells drawn uniformly, with replacement across pairs, from the largest
     component. The generator is `random.Random(20261105 + crc32(map name))`.
   * `optimal` is the shortest octile path cost (1 for straight moves, sqrt 2 for diagonals, no corner cutting),
     computed by our own A* with the octile heuristic (consistent) and printed with 8 decimals.
   * bucket = floor(optimal/4). Lines are sorted by bucket.
   * Check: for the first 3 scenarios of every map, a full Dijkstra from the start gave the same cost (|diff| < 1e-9).

## Rejected candidates and why
* **robot-motion/bench-mr** `bin/image_mazes/intel-lab.png`, `freiburg.png`: the repository does not document how
  they were made, which dataset they come from, or their resolution. Intel is covered from the primary log instead.
* **f1tenth/f1tenth_gym** `levine`, `stata_basement` (0.05 m yaml), **mit-racecar/particle_filter**
  `basement_fixed.png` (0.0504 m), **uos/uos_tools** `uos_maps` (avz, rilo, cic; some are floor-plan or Gazebo
  variants): none documents how the map was recorded, who recorded it, or a publication. The repositories carry
  MIT or BSD code licences only.
* **anindex/gtmp** (GTMP, arXiv 2411.19393): the paper uses Intel, ACES3, Orebro and Freiburg-campus maps "from
  Radish", but the map files (`*.npy`) are not in the repository and are rescaled to a 20 x 20 box.
* **ut-amrl/amrl_maps:** vector maps, and the method used to make them is not documented.
* **FLIRTLib `kenmore_first_loop.log`:** suburban streets, about 1.15 km x 1.16 km (Radish "kenmore-pradoroof",
  a roof-mounted laser on a vehicle). It is outdoor, and 18% of returns are at maximum range. It would be about
  23,000 x 23,000 cells at 0.05 m. **`fr-clinic.log`:** no poses in the file (all zero), so no grid can be built
  without running SLAM. **`victoria-park.log`:** outdoor park with tree-trunk landmarks, not suitable for occupancy.
* **CARMEN `freiburg.map`:** the header says only "bee2carmen ... Created from freiburg.map", so the origin is
  unknown. **`nsh_level_3.map`:** the header fields are placeholders ("origin", "description").
  **`thickwean.map`:** built from a log ("cleanmaprun1.log"), but there is no place description.
* **MRPT `2006-MalagaCampus.gridmap.gz` and `malaga-cs-fac-building.simplemap.gz`:** these use MRPT's binary
  serialisation, which would need a re-implementation, and I did not verify their provenance. Not attempted.
* **ACES Austin, MIT Killian Court, Freiburg campus, and other Radish maps:** available on DSpace (CC0) and
  partly as raw CLF logs on GitHub (e.g. xiaofeng419/SLAM-2D-LIDAR-SCAN), but I found no SLAM-corrected poses or
  PGM maps of them on GitHub. DSpace cannot be reached from this shell, and running our own SLAM on raw logs was
  out of scope.

## Known limitations
* Thin, single-cell walls in the self-built grids can contain gaps. After 0.25 m inflation these are closed in
  practice, but a gap wider than about 0.5 m would remain open.
* People and clutter seen during mapping (e.g. Intel lab lower left) appear as small obstacles that become discs
  of radius R after inflation.
* Laser rays through windows and doors create thin free "fans" outside the buildings. Inflation removes most of
  them. Any fan that is still free is in a separate component and is never used for scenarios.
* The FLIRT log for mit-cscail reports a 50 m maximum range, while the Radish record says 80 m. The scans are used
  as distributed.
