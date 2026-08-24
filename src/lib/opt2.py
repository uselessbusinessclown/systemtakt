"""Wiederverwendbarer ITF-Optimierer mit Optionen."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, os, random, math, collections
DW, RES = 6, 0.07
def load(db=None):
    con=sqlite3.connect(db or DB); cur=con.cursor()
    nm=dict(cur.execute("SELECT station_id,name FROM station"))
    rows=[(nm[a],nm[b],t,p15,w,fs,fi,fc) for a,b,t,p15,w,fs,fi,fc in
          cur.execute("SELECT a_id,b_id,t_min,t_p15,gewicht,f_sprinter,f_ice,f_ic FROM itf_kante")]
    con.close(); return rows
def ecost(d,T0,w,allow_acc=True):
    if d>=0: return w*(0.15*d + 2.0*max(0.0, d-RES*T0-2))
    return w*(4.0*(-d)+20.0) if allow_acc else 1e12
def solve(rows, allow_acc=True, domain=None, prio=None, prio_factor=1.0,
          fixed=None, runs=600, iters=40000, seed=20260823, verbose=False):
    nodes=sorted({r[0] for r in rows}|{r[1] for r in rows}); IX={n:i for i,n in enumerate(nodes)}
    dom = domain or list(range(30))
    edges=[]
    for a,b,t,p15,w,fs,fi,fc in rows:
        ww = w*prio_factor if (prio and (a==prio or b==prio)) else w
        edges.append((IX[a],IX[b],t+DW,t,ww,w,a,b,fs,fi,fc,p15))
    COST=[[min(ecost(n,e[2],e[4],allow_acc), ecost(n-30,e[2],e[4],allow_acc)) for n in range(30)] for e in edges]
    adj=collections.defaultdict(list)
    for i,e in enumerate(edges): adj[e[0]].append(i); adj[e[1]].append(i)
    fixed = {IX[k]:v for k,v in (fixed or {}).items() if k in IX}
    free=[i for i in range(len(nodes)) if i not in fixed]
    def total(phi): return sum(COST[i][(phi[e[1]]-phi[e[0]]-e[2])%30] for i,e in enumerate(edges))
    def local(phi,k): return sum(COST[i][(phi[edges[i][1]]-phi[edges[i][0]]-edges[i][2])%30] for i in adj[k])
    rnd=random.Random(seed); best=None
    for run in range(runs):
        if best and run%3==2:
            phi=list(best[1])
            for _ in range(max(2,len(free)//8)):
                k=rnd.choice(free); phi[k]=rnd.choice(dom)
        else:
            phi=[rnd.choice(dom) for _ in nodes]
        for k,v in fixed.items(): phi[k]=v
        c=total(phi)
        for it in range(iters):
            T=40.0*math.exp(-it/6000)+.01
            k=rnd.choice(free); old=phi[k]; b4=local(phi,k)
            phi[k]=rnd.choice(dom); d=local(phi,k)-b4
            if d<=0 or (d<1e11 and rnd.random()<math.exp(-min(d,700)/T)): c+=d
            else: phi[k]=old
        imp=True
        while imp:
            imp=False
            for k in free:
                old=phi[k]; bv=old; bc=local(phi,k)
                for v in dom:
                    phi[k]=v; cc=local(phi,k)
                    if cc<bc-1e-9: bc=cc; bv=v
                phi[k]=bv
                if bv!=old: imp=True
        c=total(phi)
        if best is None or c<best[0]:
            best=(c,list(phi))
            if verbose: print('  run',run,round(c,1),flush=True)
    cost,phi=best
    out=[]; acc=0; band=0.0; wsum=0.0; wres=0.0; maxpad=0
    for e in edges:
        need=(phi[e[1]]-phi[e[0]]-e[2])%30
        c1,c2=ecost(need,e[2],e[5],allow_acc), ecost(need-30,e[2],e[5],allow_acc)
        d=need if c1<=c2 else need-30
        ts=e[2]+d-DW; r=(ts-e[3])/e[3]*100 if e[3] else 0
        wsum+=e[5]; wres+=e[5]*max(r,0)
        if d<0: acc+=1
        if 0<=r<=7: band+=e[5]
        maxpad=max(maxpad,d)
        out.append((e[6],e[7],e[3],e[11],ts,d,round(r,1),e[5],e[8],e[9],e[10]))
    return {'kosten':round(cost,1),'phi':{nodes[i]:phi[i] for i in range(len(nodes))},
            'kanten':out,'beschl':acc,'sollband_pct':round(100*band/wsum,1),
            'reserve_pct':round(wres/wsum,2),'gewicht':round(wsum,1),'max_zuschlag':maxpad,
            'kosten_je_gewicht':round(cost/wsum,3)}
def anchor(phi, node):
    off=phi[node]; return {k:(v-off)%30 for k,v in phi.items()}
