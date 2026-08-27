import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sys; import knotenwahl as K, pesp, json, time
SETS={
 'K20 kuratiert': ['Hamburg Hbf','Bremen Hbf','Hannover Hbf','Berlin Hbf','Leipzig Hbf','Erfurt Hbf',
   'Dresden Hbf','Dortmund Hbf','Duisburg Hbf','Köln Hbf','Frankfurt(Main)Hbf','Kassel-Wilhelmshöhe',
   'Fulda','Würzburg Hbf','Nürnberg Hbf','München Hbf','Stuttgart Hbf','Mannheim Hbf','Karlsruhe Hbf',
   'Münster(Westf)Hbf'],
 'K16 kuratiert': ['Hamburg Hbf','Hannover Hbf','Berlin Hbf','Leipzig Hbf','Erfurt Hbf','Dortmund Hbf',
   'Duisburg Hbf','Köln Hbf','Frankfurt(Main)Hbf','Kassel-Wilhelmshöhe','Würzburg Hbf','Nürnberg Hbf',
   'München Hbf','Stuttgart Hbf','Mannheim Hbf','Bremen Hbf'],
 'K24 kuratiert': ['Hamburg Hbf','Bremen Hbf','Hannover Hbf','Berlin Hbf','Leipzig Hbf','Halle(Saale)Hbf',
   'Erfurt Hbf','Dresden Hbf','Magdeburg Hbf','Dortmund Hbf','Duisburg Hbf','Düsseldorf Hbf','Köln Hbf',
   'Frankfurt(Main)Hbf','Kassel-Wilhelmshöhe','Fulda','Würzburg Hbf','Nürnberg Hbf','München Hbf',
   'Augsburg Hbf','Stuttgart Hbf','Mannheim Hbf','Karlsruhe Hbf','Münster(Westf)Hbf'],
}
out={}
for name,lst in SETS.items():
    NODES=set(lst); ed=K.build_edges(NODES)
    t=time.time()
    r=pesp.solve_exact(ed, anchor='Berlin Hbf', max_acc=0, time_limit=300, mip_gap=0.002)
    PHI=r['phi']; TS={}
    for x in r['kanten']: TS[(x[0],x[1])]=x[4]; TS[(x[1],x[0])]=x[4]
    v,det=K.reisezeit(NODES,PHI,TS)
    out[name]={'knoten':sorted(NODES),'phi':PHI,'kanten':r['kanten'],'reserve':r['reserve_pct'],
               'sollband':r['sollband_pct'],'kje':r['kosten_je_gewicht'],'verl':round(v,1),'optimal':r['status']==0}
    print(f"{name:16s} Kanten {len(ed):3d}  Ø Reserve {r['reserve_pct']:5.2f} %  Sollband {r['sollband_pct']:5.1f} %  "
          f"Reisezeit {v:+6.1f} min  {'optimal' if r['status']==0 else 'Limit'} {round(time.time()-t)} s", flush=True)
    print(f"    Knotenzeiten: " + ', '.join(f"{k.replace(' Hbf','')} :{PHI[k]:02d}" for k in sorted(PHI,key=lambda x:PHI[x])), flush=True)
json.dump(out, open(os.path.join(DATA, 'knotenwahl2.json'),'w'), ensure_ascii=False)
