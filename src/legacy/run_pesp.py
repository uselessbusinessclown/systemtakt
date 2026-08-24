
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import opt2, pesp, time, json
rows=opt2.load()
for tag,acc,tl in (('N1',0,1500),('N0',12,1500)):
    t=time.time()
    r=pesp.solve_exact(rows, anchor='Berlin Hbf', max_acc=acc, time_limit=tl)
    if r is None: print(tag,'keine Lösung',flush=True); continue
    print(tag, {k:v for k,v in r.items() if k in ('kosten','kosten_je_gewicht','status','message',
        'sollband_pct','reserve_pct','beschl','max_zuschlag')}, 'Dauer', round(time.time()-t),'s', flush=True)
    json.dump(r, open(fos.path.join(ROOT, 'pesp_{tag}.json'),'w'), ensure_ascii=False)
