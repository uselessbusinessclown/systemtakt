import sqlite3, os, sys, random, math, collections, statistics as st, json
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
BASE=[r[0] for r in cur.execute("SELECT name FROM itf_knotenzeit")]
FBF='Frankfurt(M) Flughafen Fernbf'; HBF='Frankfurt(Main)Hbf'
VAR=sys.argv[1]
nodes=set(BASE)
if VAR=='V1': nodes.add(FBF)
if VAR=='V2': nodes.add(FBF); nodes.discard(HBF)
name2id=dict(cur.execute("SELECT name,station_id FROM station"))
NID={name2id[n] for n in nodes if n in name2id}
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
nm=dict(cur.execute("SELECT station_id,name FROM station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((s2st[sid],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,verkehrstage FROM trip_summary")}
E=collections.defaultdict(lambda:{'t':[],'spr':0.,'ice':0.,'ic':0.})
for tid,p in seq.items():
    kat,vt=TS[tid]; vt=vt/31
    idx=[i for i,x in enumerate(p) if x[0] in NID]
    for j in range(len(idx)-1):
        a=p[idx[j]]; b=p[idx[j+1]]
        dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if t<=0 or t>420: continue
        k=(a[0],b[0]) if a[0]<b[0] else (b[0],a[0])
        e=E[k]; e['t'].append(t)
        if kat=='ICE-SPRINTER': e['spr']+=vt
        elif kat=='ICE': e['ice']+=vt
        elif kat=='IC': e['ic']+=vt
edges=[]; ids=sorted({k[0] for k in E}|{k[1] for k in E}); IX={n:i for i,n in enumerate(ids)}
for (a,b),e in E.items():
    tot=e['spr']+e['ice']+e['ic']
    if tot<0.5: continue
    w=3*e['spr']+2*e['ice']+e['ic']
    edges.append((IX[a],IX[b],min(e['t'])+6,min(e['t']),w,nm[a],nm[b],e['spr'],e['ice'],e['ic']))
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
for run in range(int(os.environ.get("RUNS","240"))):
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
    if best is None or c<best[0]: best=(c,list(phi))
cost,phi=best
res=[]; acc=0; accw=0.0; wsum=0.0; band=0.0; wres=0.0
for i,e in enumerate(edges):
    need=(phi[e[1]]-phi[e[0]]-e[2])%30
    d=need if ecost(need,e[2],e[4])<=ecost(need-30,e[2],e[4]) else need-30
    ts=e[2]+d-DW; r=(ts-e[3])/e[3]*100 if e[3] else 0
    wsum+=e[4]; wres+=e[4]*max(r,0)
    if d<0: acc+=1; accw+=e[4]
    if 0<=r<=7: band+=e[4]
    res.append((e[5],e[6],e[3],ts,d,round(r,1),e[4]))
out={'variante':VAR,'knoten':len(ids),'kanten':len(edges),'kosten':round(cost,1),
     'beschl_kanten':acc,'beschl_gewicht':round(accw,1),
     'anteil_sollband_pct':round(100*band/wsum,1),'mittlere_reserve_pct':round(wres/wsum,2),
     'phi':{nm[ids[i]]:phi[i] for i in range(len(ids))},
     'kanten_detail':sorted(res,key=lambda r:-r[6])[:12]}
json.dump(out,open(f'var_{VAR}.json','w'),ensure_ascii=False,indent=1)
print(VAR,'Knoten',len(ids),'Kanten',len(edges),'Kosten',round(cost,1),
      '| Beschl.-Kanten',acc,'| Sollband',out['anteil_sollband_pct'],'% | Ø Reserve',out['mittlere_reserve_pct'],'%')
for k in (FBF,HBF):
    if k in out['phi']: print('   ',k,'-> :%02d'%out['phi'][k])
