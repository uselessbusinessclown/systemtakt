import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import opt2, pesp, time, json
rows=opt2.load()
for tag,acc,tl in (('N1',0,1500),('N0',12,1500)):
    t=time.time()
    r=pesp.solve_exact(rows, anchor='Berlin Hbf', max_acc=acc, time_limit=tl)
    if r is None: print(tag,'keine Lösung',flush=True); continue
    print(tag, {k:v for k,v in r.items() if k in ('kosten','kosten_je_gewicht','status','message',
        'sollband_pct','reserve_pct','beschl','max_zuschlag')}, 'Dauer', round(time.time()-t),'s', flush=True)
    json.dump(r, open(os.path.join(DATA, f'pesp_{tag}.json'),'w'), ensure_ascii=False)
