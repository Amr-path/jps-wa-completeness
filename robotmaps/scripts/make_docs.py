"""Write maps.csv from stats_real.json + stats_houseexpo.json and per-map provenance metadata.
usage: python3 -I make_docs.py ROOT"""
import sys, os, json, csv
root = sys.argv[1]
FL = 'https://github.com/tipaldi/flirtlib/tree/f608c8c486b53320a5fc701de6d70e7e803c412c/data'
CA = 'https://github.com/LCAD-UFES/carmen_lcad/tree/85d31fa2003086454338ccdd7bfbca2ca6971495/data'
HE = 'https://github.com/TeaganLi/HouseExpo/tree/45e2b2505f6ea1fe49c0203f14efb7ce20b94e7c/HouseExpo'
META = {
 'intel-lab': dict(tier='A', environment='Intel Research Lab, Seattle (indoor office)',
   source_url=FL + '/intel-lab.log', source_kind='SLAM-corrected laser log (VERTEX2 poses + ROBOTLASER1 scans); grid built by us',
   dataset='Radish intel_lab (hdl:1721.1/62287); raw log by Dirk Haehnel per Freiburg SLAM-evaluation page; DSpace lists Dieter Fox as contributor',
   citation='Howard & Roy 2003 (Radish); Tipaldi & Arras, ICRA 2010, doi:10.1109/ROBOT.2010.5509864 (log redistribution); Kuemmerle et al., Auton. Robots 27(4) 2009, doi:10.1007/s10514-009-9155-6 (standard SLAM benchmark use)',
   license='Radish item CC0 1.0 (DSpace); FLIRTLib repository LGPL-3.0+'),
 'fr079': dict(tier='A', environment='University of Freiburg building 079 (indoor office)',
   source_url=FL + '/fr079.log', source_kind='SLAM-corrected laser log; grid built by us',
   dataset='Radish fr079 (hdl:1721.1/62290), recorded 2003-11-18 by Cyrill Stachniss, Pioneer2 + SICK LMS',
   citation='Howard & Roy 2003 (Radish); Tipaldi & Arras ICRA 2010 doi:10.1109/ROBOT.2010.5509864; Kuemmerle et al. 2009 doi:10.1007/s10514-009-9155-6',
   license='Radish item CC0 1.0 (DSpace); FLIRTLib repository LGPL-3.0+'),
 'mit-cscail': dict(tier='A', environment='MIT CSAIL, 3rd floor (indoor office)',
   source_url=FL + '/mit-cscail.log', source_kind='SLAM-corrected laser log; grid built by us',
   dataset='Radish mit-csail-3rd-floor (hdl:1721.1/62274), recorded 2005-12-17 by Cyrill Stachniss, B21r + SICK LMS',
   citation='Howard & Roy 2003 (Radish); Tipaldi & Arras ICRA 2010 doi:10.1109/ROBOT.2010.5509864; Kuemmerle et al. 2009 doi:10.1007/s10514-009-9155-6',
   license='Radish item CC0 1.0 (DSpace); FLIRTLib repository LGPL-3.0+'),
 'longwood': dict(tier='A', environment='Longwood at Oakmont nursing home, Pennsylvania (indoor)',
   source_url=CA + '/longwood.map', source_kind='robot-built occupancy grid (CARMEN map file, GRIDMAP chunk)',
   dataset='Radish Longwood (hdl:1721.1/62284), contributed by Nick Roy: map built from two robot data runs (beeSoft), merged, 10 cm; file header: author nickr, 2002-09-20, origin longwood.large.log',
   citation='Howard & Roy 2003 (Radish); Montemerlo, Roy & Thrun, IROS 2003, doi:10.1109/IROS.2003.1249235 (CARMEN, distributing package)',
   license='Radish item CC0 1.0 (DSpace); file distributed in CARMEN (GPL-2.0)'),
 'wean5300': dict(tier='B', environment='"Wean 5300 Corridor" (per file header; presumably CMU Wean Hall)',
   source_url=CA + '/wean5300.map', source_kind='robot-built occupancy grid (CARMEN map file)',
   dataset='CARMEN sample map; header only: author mmde, 2002-12-06, origin /home/mmde/wean-map-run-1.log, description "Wean 5300 Corridor". Not on Radish; no publication found',
   citation='Montemerlo, Roy & Thrun, IROS 2003, doi:10.1109/IROS.2003.1249235 (CARMEN)',
   license='CARMEN GPL-2.0'),
}
HEM = dict(tier='S', environment='HouseExpo layout (synthetic floor plan derived from SUNCG; not robot data)',
   source_kind='JSON polygon (m) rasterised by us at 0.05 m',
   dataset='HouseExpo (35,126 layouts) built on SUNCG',
   citation='Li et al., IROS 2020, pp. 5839-5846, doi:10.1109/IROS45743.2020.9341284; Song et al., CVPR 2017, doi:10.1109/CVPR.2017.28 (SUNCG)',
   license='HouseExpo repository MIT; underlying SUNCG terms of use apply (see README)')
rows = []
for fn, group in (('stats_real.json', 'real'), ('stats_houseexpo.json', 'houseexpo')):
    p = os.path.join(root, fn)
    if not os.path.exists(p): continue
    st = json.load(open(p))
    for name in sorted(st, key=lambda n: (group, list(META).index(n) if n in META else 0, n)):
        s = st[name]
        m = dict(META[name]) if name in META else dict(HEM, source_url=HE + '/json.tar.gz (json/%s.json)' % name[len('houseexpo_'):])
        rows.append(dict(map=name, set=group, provenance_tier=m['tier'], environment=m['environment'],
            source_url=m['source_url'], source_kind=m['source_kind'], original_dataset=m['dataset'],
            citation=m['citation'], license=m['license'], resolution_m=round(s['resolution'], 4),
            inflation_radius_m=0.25, inflation_radius_cells=s['radius_cells'],
            source_width=s['src_w'], source_height=s['src_h'], source_free_cells=s['src_free'],
            width=s['width'], height=s['height'], free_cells=s['free_cells'],
            free_components=s['n_components'], largest_component_cells=s['lcc_cells'],
            scenarios=s['n_scen'], mean_optimal=round(s['mean_cost'], 2), max_optimal=round(s['max_cost'], 2),
            map_file='maps/%s/%s.map' % (group, name), scen_file='maps/%s/%s.map.scen' % (group, name)))
with open(os.path.join(root, 'maps.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), 'rows')
for r in rows:
    if r['set'] == 'real':
        print('| %s | %s | %.2f | %d | %dx%d | %d | %d | %d |' % (r['map'], r['provenance_tier'], r['resolution_m'], r['inflation_radius_cells'],
              r['width'], r['height'], r['free_cells'], r['largest_component_cells'], r['scenarios']))
he = [r for r in rows if r['set'] == 'houseexpo']
if he:
    import statistics as S
    for k in ('width', 'height', 'free_cells', 'largest_component_cells', 'mean_optimal'):
        v = [r[k] for r in he]; print('houseexpo', k, 'min', min(v), 'median', S.median(v), 'max', max(v))
