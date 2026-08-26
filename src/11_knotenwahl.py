import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sys; import knotenwahl as K, opt2, pesp, sqlite3, json, time
con=sqlite3.connect(DB)
rank=[r[0] for r in con.execute("SELECT name FROM itf_knotenzeit ORDER BY gewicht DESC")]
alle=set(rank)
res={}
for n in (16,20,24,30,40,64):
    NODES=set(rank[:n])
    ed=K.build_edges(NODES)
    nodes_in=set(x[0] for x in ed)|set(x[1] for x in ed)
    if len(nodes_in)<n*0.8:
        print(f"n={n}: nur {len(nodes_in)} Knoten mit Kanten"); 
    t=time.time()
    r=pesp.solve_exact(ed, anchor='Berlin Hbf', max_acc=0, time_limit=300, mip_gap=0.003)
    PHI=r['phi']; TSOLL={}
    for x in r['kanten']: TSOLL[(x[0],x[1])]=x[4]; TSOLL[(x[1],x[0])]=x[4]
    verl,det=K.reisezeit(NODES,PHI,TSOLL)
    res[n]={'knoten':len(nodes_in),'kanten':len(ed),'reserve':r['reserve_pct'],'sollband':r['sollband_pct'],
            'kosten_je_gewicht':r['kosten_je_gewicht'],'verlaengerung':round(verl,1),
            'optimal':r['status']==0,'phi':PHI,'kanten_soll':r['kanten']}
    print(f"n={n:2d}  Knoten {len(nodes_in):2d}  Kanten {len(ed):3d}  Ø Reserve {r['reserve_pct']:5.2f} %  "
          f"Sollband {r['sollband_pct']:5.1f} %  mittlere Reisezeitverlängerung {verl:+6.1f} min  "
          f"{'optimal' if r['status']==0 else 'Zeitlimit'} {round(time.time()-t)} s", flush=True)
    print(f"     schlimmste Linien: {[(d[0],d[3]) for d in det[:4]]}", flush=True)
json.dump(res, open(os.path.join(DATA, 'knotenwahl.json'),'w'), ensure_ascii=False)
