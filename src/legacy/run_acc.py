import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import opt2, pesp2, json, time
rows=opt2.load()
for acc in (3,6):
    t=time.time()
    r=pesp2.solve(rows, anchor='Berlin Hbf', max_acc=acc, acc_cost=4.0, time_limit=1000, mip_gap=0.003)
    if not r: print(acc,'keine Lösung',flush=True); continue
    print(f"max. Beschleunigung {acc} min: Kosten {r['kosten']} ({r['kosten_je_gewicht']}/Gewicht) "
          f"Sollband {r['sollband_pct']} % Ø Reserve {r['reserve_pct']} % Kanten mit Verkürzung {r['beschl']} "
          f"{'optimal' if r['optimal'] else 'Zeitlimit'} {round(time.time()-t)} s", flush=True)
    json.dump(r, open(os.path.join(DATA, f'pesp_acc{acc}.json'),'w'), ensure_ascii=False)
