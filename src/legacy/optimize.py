
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, os, random, math, collections
con=sqlite3.connect(DB); cur=con.cursor()
E=list(cur.execute("SELECT a_id,b_id,a,b,t_min,t_p15,zwischenhalte,f_sprinter,f_ice,f_ic,f_gesamt,gewicht FROM itf_kante"))
nodes=sorted({e[0] for e in E}|{e[1] for e in E})
IX={n:i for i,n in enumerate(nodes)}
NAME=dict(cur.execute("SELECT station_id,name FROM station"))
DWELL=6; RES_SOLL=0.07
edges=[]
for a,b,an,bn,tmin,tp15,zw,fs,fi,fc,fg,w in E:
    edges.append((IX[a],IX[b],tmin+DWELL,tmin,w,an,bn,fs,fi,fc,fg,zw,tp15))
adj=collections.defaultdict(list)
for ei,e in enumerate(edges): adj[e[0]].append(ei); adj[e[1]].append(ei)

def ecost(delta,T0,w):
    if delta>=0: return w*(0.15*delta + 2.0*max(0.0, delta-RES_SOLL*T0-2))
    return w*(4.0*(-delta)+20.0)
# Vorberechnung: Kosten je Kante für jeden möglichen Restwert need 0..29
COST=[]
for i,j,T0,tmin,w,*r in edges:
    COST.append([min(ecost(n,T0,w), ecost(n-30,T0,w)) for n in range(30)])

def total(phi):
    s=0.0
    for ei,(i,j,T0,tmin,w,*r) in enumerate(edges):
        s+=COST[ei][(phi[j]-phi[i]-T0)%30]
    return s
def local(phi, k):
    s=0.0
    for ei in adj[k]:
        i,j,T0=edges[ei][0],edges[ei][1],edges[ei][2]
        s+=COST[ei][(phi[j]-phi[i]-T0)%30]
    return s

rnd=random.Random(20260822); best=None
for run in range(300):
    phi=[rnd.randrange(30) for _ in nodes]
    c=total(phi)
    for it in range(40000):
        T=40.0*math.exp(-it/6000)+0.01
        k=rnd.randrange(len(phi)); old=phi[k]
        b4=local(phi,k); phi[k]=rnd.randrange(30); af=local(phi,k)
        d=af-b4
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
    if best is None or c<best[0]:
        best=(c,list(phi)); print(f"  run{run:4d} cost {c:12.1f}", flush=True)
cost,phi=best
print("Zielfunktion:", round(cost,1))

cur.executescript("""DROP TABLE IF EXISTS itf_knotenzeit; DROP TABLE IF EXISTS itf_ergebnis;
CREATE TABLE itf_knotenzeit(station_id TEXT PRIMARY KEY,name TEXT,knotenminute INT,
  knotenzeit TEXT, ankunft TEXT, abfahrt TEXT, gewicht REAL, grad INT);
CREATE TABLE itf_ergebnis(a TEXT,b TEXT,t_technisch INT,t_ist_p15 INT,t_soll INT,
  delta INT, reserve_pct REAL, massnahme TEXT, gewicht REAL, f_sprinter REAL,f_ice REAL,f_ic REAL);""")
deg=collections.Counter(); gw=collections.Counter()
for i,j,T0,tmin,w,*r in edges: deg[i]+=1; deg[j]+=1; gw[i]+=w; gw[j]+=w
cur.executemany("INSERT INTO itf_knotenzeit VALUES(?,?,?,?,?,?,?,?)",
 [(n,NAME[n],phi[i],f":{phi[i]:02d} / :{(phi[i]+30)%60:02d}",
   f":{(phi[i]-3)%60:02d} / :{(phi[i]+27)%60:02d}", f":{(phi[i]+3)%60:02d} / :{(phi[i]+33)%60:02d}",
   round(gw[i],1), deg[i]) for n,i in IX.items()])
res=[]
for ei,(i,j,T0,tmin,w,an,bn,fs,fi,fc,fg,zw,tp15) in enumerate(edges):
    need=(phi[j]-phi[i]-T0)%30
    delta = need if ecost(need,T0,w)<=ecost(need-30,T0,w) else need-30
    tsoll=T0+delta-DWELL
    reserve=(tsoll-tmin)/tmin*100 if tmin else 0
    if delta<0: mass=f"Beschleunigung nötig: {-delta} min unter heutiger Bestzeit"
    elif reserve>14: mass=f"Überschussreserve {reserve:.0f} % – Zusatzhalt möglich"
    else: mass="taktkonform"
    res.append((an,bn,tmin,tp15,tsoll,delta,round(reserve,1),mass,w,fs,fi,fc))
cur.executemany("INSERT INTO itf_ergebnis VALUES(%s)"%','.join('?'*12), res)
con.commit()
print("\nKnotenzeiten (Top 30 nach Gewicht):")
for r in cur.execute("SELECT name,knotenzeit,ankunft,abfahrt,gewicht,grad FROM itf_knotenzeit ORDER BY gewicht DESC LIMIT 30"):
    print(f"  {r[0][:28]:28s} Knoten {r[1]:12s} an {r[2]:12s} ab {r[3]:12s} w{r[4]:7.0f} Grad {r[5]}")
print("\nKanten mit Beschleunigungsbedarf:")
for r in cur.execute("SELECT a,b,t_technisch,t_soll,delta,gewicht FROM itf_ergebnis WHERE delta<0 ORDER BY gewicht DESC"):
    print(f"  {r[0][:24]:24s}-{r[1][:24]:24s} tech{r[2]:4d} soll{r[3]:4d} Δ{r[4]:+3d} w{r[5]:7.0f}")
print("\nMaßnahmenverteilung:")
for r in cur.execute("SELECT massnahme,COUNT(*),ROUND(SUM(gewicht)) FROM itf_ergebnis GROUP BY 1 ORDER BY 3 DESC LIMIT 6"): print('  ',r)
con.close()
