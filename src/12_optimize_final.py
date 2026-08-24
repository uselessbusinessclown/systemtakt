
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sys; import knotenwahl as K, pesp_sym, json, time
for name in ('K16 kuratiert','K20 kuratiert'):
    NODES=set(json.load(open(os.path.join(ROOT, 'knotenwahl2.json')))[name]['knoten'])
    ed=K.build_edges(NODES)
    t=time.time()
    r=pesp_sym.solve(ed, anchor='Berlin Hbf', time_limit=900, mip_gap=0.004)
    if r is None: print(name,'keine Lösung',flush=True); continue
    print(name, {k:v for k,v in r.items() if k in ('kosten','kosten_je_gewicht','reserve_pct','sollband_pct','optimal')},
          round(time.time()-t),'s', flush=True)
    json.dump(r, open(fos.path.join(ROOT, "pesp_sym_{name.split()[0]}.json"),'w'), ensure_ascii=False)
