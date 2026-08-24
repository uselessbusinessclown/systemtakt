
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, os, random, math, collections, json, statistics as st
con=sqlite3.connect(DB); cur=con.cursor()
NAMES=[r[0] for r in cur.execute("SELECT name FROM itf_knotenzeit")]
name2id=dict(cur.execute("SELECT name,station_id FROM station")); nm=dict(cur.execute("SELECT station_id,name FROM station"))
NID={name2id[n] for n in NAMES}
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((s2st[sid],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,verkehrstage,gattung,linie FROM trip_summary")}
E=collections.defaultdict(lambda:{'t':[],'spr':0.,'ice':0.,'ic':0.,'zw':[], 'lin':collections.Counter(),'zwn':None})
for tid,p in seq.items():
    kat,vt,g,lin=TS[tid]; vt=vt/31
    idx=[i for i,x in enumerate(p) if x[0] in NID]
    for j in range(len(idx)-1):
        i0,i1=idx[j],idx[j+1]; a,b=p[i0],p[i1]
        dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if t<=0 or t>420: continue
        k=(a[0],b[0]) if a[0]<b[0] else (b[0],a[0]); e=E[k]
        e['t'].append(t); e['zw'].append(i1-i0-1)
        if kat=='ICE-SPRINTER': e['spr']+=vt
        elif kat=='ICE': e['ice']+=vt
        elif kat=='IC': e['ic']+=vt
        if lin: e['lin'][f"{g} {lin}"]+=1
        if e['zwn'] is None or (i1-i0-1)<len(e['zwn']): e['zwn']=[nm[x[0]] for x in p[i0+1:i1]]
rows=[]
for (a,b),e in E.items():
    tot=e['spr']+e['ice']+e['ic']
    if tot<0.5: continue
    ts=sorted(e['t']); p15=ts[max(0,int(len(ts)*0.15))]
    rows.append((a,b,nm[a],nm[b],ts[0],p15,int(st.median(ts)),min(e['zw']),' > '.join(e['zwn'] or []),
                 round(e['spr'],2),round(e['ice'],2),round(e['ic'],2),round(tot,2),
                 round(3*e['spr']+2*e['ice']+e['ic'],2), ', '.join(k for k,_ in e['lin'].most_common(8))))
cur.execute("DELETE FROM itf_kante")
cur.executemany("INSERT INTO itf_kante VALUES(%s)"%','.join('?'*15), rows); con.commit()
ids=sorted({r[0] for r in rows}|{r[1] for r in rows}); IX={n:i for i,n in enumerate(ids)}
edges=[(IX[r[0]],IX[r[1]],r[4]+6,r[4],r[13],r[2],r[3],r[9],r[10],r[11],r[5]) for r in rows]
DW,RES=6,0.07
def ecost(d,T0,w):
    if d>=0: return w*(0.15*d+2.0*max(0.0,d-RES*T0-2))
    return w*(4.0*(-d)+20.0)
COST=[[min(ecost(n,e[2],e[4]),ecost(n-30,e[2],e[4])) for n in range(30)] for e in edges]
adj=collections.defaultdict(list)
for i,e in enumerate(edges): adj[e[0]].append(i); adj[e[1]].append(i)
def total(phi): return sum(COST[i][(phi[e[1]]-phi[e[0]]-e[2])%30] for i,e in enumerate(edges))
def local(phi,k): return sum(COST[i][(phi[edges[i][1]]-phi[edges[i][0]]-edges[i][2])%30] for i in adj[k])
rnd=random.Random(20260822); best=None
for run in range(2000):
    phi=[rnd.randrange(30) for _ in ids]; c=total(phi)
    for it in range(40000):
        T=40.0*math.exp(-it/6000)+.01
        k=rnd.randrange(len(phi)); old=phi[k]; b4=local(phi,k)
        phi[k]=rnd.randrange(30); d=local(phi,k)-b4
        if d<=0 or rnd.random()<math.exp(-d/T): c+=d
        else: phi[k]=old
    imp=True
    while imp:
        imp=False
        for k in range(len(phi)):
            old=phi[k]; bv=old; bc=local(phi,k)
            for v in range(30):
                phi[k]=v; cc=local(phi,k)
                if cc<bc-1e-9: bc=cc; bv=v
            phi[k]=bv
            if bv!=old: imp=True
    c=total(phi)
    if best is None or c<best[0]: best=(c,list(phi)); print('run',run,round(c,1),flush=True)
cost,phi=best
# Anker Berlin Hbf = :00
bi=IX[name2id['Berlin Hbf']]; off=phi[bi]
phi=[(p-off)%30 for p in phi]
deg=collections.Counter(); gw=collections.Counter()
for e in edges: deg[e[0]]+=1; deg[e[1]]+=1; gw[e[0]]+=e[4]; gw[e[1]]+=e[4]
cur.execute("DELETE FROM itf_knotenzeit")
cur.executemany("INSERT INTO itf_knotenzeit VALUES(?,?,?,?,?,?,?,?)",
 [(sid,nm[sid],phi[i],f":{phi[i]:02d} / :{(phi[i]+30)%60:02d}",
   f":{(phi[i]-3)%60:02d} / :{(phi[i]+27)%60:02d}", f":{(phi[i]+3)%60:02d} / :{(phi[i]+33)%60:02d}",
   round(gw[i],1), deg[i]) for sid,i in IX.items()])
cur.execute("DELETE FROM itf_ergebnis")
res=[]
for e in edges:
    need=(phi[e[1]]-phi[e[0]]-e[2])%30
    d=need if ecost(need,e[2],e[4])<=ecost(need-30,e[2],e[4]) else need-30
    tsoll=e[2]+d-DW; r=(tsoll-e[3])/e[3]*100 if e[3] else 0
    mass=(f"Beschleunigung nötig: {-d} min unter heutiger Bestzeit" if d<0 else
          (f"Überschussreserve {r:.0f} % – Zusatzhalt möglich" if r>14 else "taktkonform"))
    res.append((e[5],e[6],e[3],e[10],tsoll,d,round(r,1),mass,e[4],e[7],e[8],e[9]))
cur.executemany("INSERT INTO itf_ergebnis VALUES(%s)"%','.join('?'*12), res)
con.commit()
print('FERTIG Kosten',round(cost,1),'Knoten',len(ids),'Kanten',len(edges))
print('Gesamtgewicht',round(sum(e[4] for e in edges),1))
