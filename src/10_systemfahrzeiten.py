"""Setzt die Kanten-Basiszeit auf die Systemfahrzeit der Linien statt auf die Bestzeit eines Einzelzuges."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sys; import fahrplan as F, sqlite3, collections, statistics, json
con=sqlite3.connect(DB); cur=con.cursor()
LIN=list(cur.execute("SELECT linie_key,laufweg,fahrten_tag FROM linie WHERE produkt IN ('ICE','IC')"))
req=collections.defaultdict(list)
for key,lauf,ft in LIN:
    if ft<1.0: continue
    path=lauf.split(' > ')
    idx=[i for i,s in enumerate(path) if s in F.PHI]
    for j in range(len(idx)-1):
        a,b=idx[j],idx[j+1]
        legt=[F.leg_time(key,path[k],path[k+1]) for k in range(a,b)]
        if any(t is None for t in legt): continue
        raw=sum(legt)+sum(F.dwell(path[k]) for k in range(a+1,b))
        kk=(path[a],path[b]) if path[a]<path[b] else (path[b],path[a])
        req[kk] += [raw]*max(1,int(round(ft)))     # nach Bedienhäufigkeit gewichtet
def p75(v):
    v=sorted(v); return v[min(len(v)-1,int(len(v)*0.75))]
upd=[]; stat=[]
for a,b,tmin in list(cur.execute("SELECT a_id,b_id,t_min FROM itf_kante")):
    pass
nm=dict(cur.execute("SELECT station_id,name FROM station"))
for a_id,b_id,tmin in list(cur.execute("SELECT a_id,b_id,t_min FROM itf_kante")):
    a,b=nm[a_id],nm[b_id]; kk=(a,b) if a<b else (b,a)
    v=req.get(kk)
    base=tmin if not v else max(tmin, min(p75(v), int(round(tmin*1.25))))
    stat.append(base-tmin); upd.append((base,a_id,b_id))
cur.executemany("UPDATE itf_kante SET t_min=? WHERE a_id=? AND b_id=?", upd)
con.commit()
stat.sort()
print(f"Basiszeiten angehoben: Median +{statistics.median(stat)} min, Mittel +{statistics.mean(stat):.1f}, max +{stat[-1]}")
print(f"unverändert: {100*sum(1 for s in stat if s==0)/len(stat):.0f} %")
con.close()
