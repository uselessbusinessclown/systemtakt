import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import json, opt2, time
rows=opt2.load()
t=time.time()
res={}
print("N0  Referenz (Beschleunigung erlaubt)", flush=True)
res['N0']=opt2.solve(rows, allow_acc=True,  runs=900)
print("   ", {k:v for k,v in res['N0'].items() if k in ('kosten','beschl','sollband_pct','reserve_pct','max_zuschlag','kosten_je_gewicht')}, flush=True)
print("N1  neubaufrei (keine Verkürzung erlaubt)", flush=True)
res['N1']=opt2.solve(rows, allow_acc=False, runs=900)
print("   ", {k:v for k,v in res['N1'].items() if k in ('kosten','beschl','sollband_pct','reserve_pct','max_zuschlag','kosten_je_gewicht')}, flush=True)
print("N2  neubaufrei + Raster :00/:15 für ALLE Knoten", flush=True)
res['N2']=opt2.solve(rows, allow_acc=False, domain=[0,15], runs=600)
print("   ", {k:v for k,v in res['N2'].items() if k in ('kosten','beschl','sollband_pct','reserve_pct','max_zuschlag','kosten_je_gewicht')}, flush=True)
print("N3  neubaufrei + Raster in 5-Minuten-Schritten", flush=True)
res['N3']=opt2.solve(rows, allow_acc=False, domain=[0,5,10,15,20,25], runs=600)
print("   ", {k:v for k,v in res['N3'].items() if k in ('kosten','beschl','sollband_pct','reserve_pct','max_zuschlag','kosten_je_gewicht')}, flush=True)
json.dump({k:{kk:vv for kk,vv in v.items()} for k,v in res.items()}, open(os.path.join(DATA, 'neubaufrei.json'),'w'), ensure_ascii=False)
print('Dauer', round(time.time()-t), 's')
