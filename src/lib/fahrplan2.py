"""Minutenfahrplan mit beidseitiger Knotendisziplin."""
import sqlite3, collections, os, statistics as st
DB=os.path.expanduser('~/bahn/bahn.db')
con=sqlite3.connect(DB); cur=con.cursor()
PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
OFF={n:{'a1':a1,'d1':d1,'a2':a2,'d2':d2} for n,a1,d1,a2,d2 in
     cur.execute("SELECT name,off_a1,off_d1,off_a2,off_d2 FROM itf_knotenzeit")}
SOLL={}
for a,b,r1,r2 in cur.execute("SELECT a,b,t_soll_r1,t_soll_r2 FROM itf_ergebnis"):
    SOLL[(a,b)]=r1; SOLL[(b,a)]=r2
DIR1=set()
for a,b in cur.execute("SELECT a,b FROM itf_ergebnis"): DIR1.add((a,b))
HALTE=dict(cur.execute("SELECT name,halte_tag FROM bahnhof_bedienung"))
KANTE={}
for a,b,t in cur.execute("SELECT a,b,t_min FROM kante"): KANTE[(a,b)]=t; KANTE[(b,a)]=t
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station")); nm=dict(cur.execute("SELECT station_id,name FROM station"))
_seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    _seq[tid].append((nm[s2st[sid]],arr,dep))
_TL={r[0]:r[1:] for r in cur.execute("SELECT trip_id,gattung,linie,betreiber FROM trip_summary")}
LEGS=collections.defaultdict(lambda: collections.defaultdict(list))
for tid,p in _seq.items():
    g,lin,op=_TL[tid]; key=f"{g} {lin}" if lin else f"{g} ({op})"
    for i in range(len(p)-1):
        a,b=p[i],p[i+1]; dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if 0<t<=400: LEGS[key][(a[0],b[0])].append(t)
con.close()
def legt(key,a,b):
    v=LEGS[key].get((a,b)) or LEGS[key].get((b,a))
    if v: return max(1,int(st.median(v)))
    return KANTE.get((a,b))
def dwell(s): return None if s in PHI else (2 if HALTE.get(s,0)>60 else 1)
def node_an(s,r): return PHI[s]-OFF[s]['a1' if r==1 else 'a2']
def node_ab(s,r): return PHI[s]+OFF[s]['d1' if r==1 else 'd2']
def edge_soll(a,b,base):
    """Soll-Fahrzeit für die tatsächlich gefahrene Richtung; None wenn Kante unbekannt."""
    return SOLL.get((a,b))
def orient(a,b): return 1 if (a,b) in DIR1 else 2
def plan(key, path, r=None):
    n=len(path)
    L=[legt(key,path[i],path[i+1]) for i in range(n-1)]
    if any(x is None for x in L): return None
    arr=[None]*n; dep=[None]*n
    idx=[i for i,s in enumerate(path) if s in PHI]
    def spread(i0,i1,start,total):
        raw=[L[k] for k in range(i0,i1)]
        dws=[dwell(path[k]) or 1 for k in range(i0+1,i1)]
        avail=total-sum(dws); s0=sum(raw) or 1
        sc=[max(1,int(round(x*avail/s0))) for x in raw]
        d=avail-sum(sc); j=0
        while d!=0 and j<100000:
            i=j%len(sc)
            if d>0: sc[i]+=1; d-=1
            elif sc[i]>1: sc[i]-=1; d+=1
            j+=1
        t=start
        for j2,k in enumerate(range(i0,i1)):
            t+=sc[j2]; arr[k+1]=t
            if k+1<i1: t+=dws[j2]; dep[k+1]=t
    if not idx:
        dep[0]=0; t=0
        for k in range(n-1):
            t+=L[k]; arr[k+1]=t
            if k+1<n-1: t+=(dwell(path[k+1]) or 1); dep[k+1]=t
        return [(path[i],arr[i],dep[i]) for i in range(n)]
    if len(idx)==1:
        i0=idx[0]; o=1
        dep[i0]=PHI[path[i0]]+OFF[path[i0]]['d1']
        arr[i0]=PHI[path[i0]]-OFF[path[i0]]['a1']
        t=arr[i0]
        for k in range(i0-1,-1,-1):
            t-=L[k]; dep[k]=t
            if k>0: t-=(dwell(path[k]) or 1); arr[k]=t
        t=dep[i0]
        for k in range(i0,n-1):
            t+=L[k]; arr[k+1]=t
            if k+1<n-1: t+=(dwell(path[k+1]) or 1); dep[k+1]=t
        dep[n-1]=None; arr[0]=None
        return [(path[i],arr[i],dep[i]) for i in range(n)]
    # Abschnitte zwischen Knoten
    o0=orient(path[idx[0]],path[idx[1]])
    dep[idx[0]]=PHI[path[idx[0]]]+OFF[path[idx[0]]]['d1' if o0==1 else 'd2']
    a0=idx[0]
    if a0>0:
        arr[a0]=PHI[path[a0]]-OFF[path[a0]]['a1' if o0==1 else 'a2']
        if dep[a0]-arr[a0]<4: arr[a0]-=30
        t=arr[a0]
        for k in range(a0-1,-1,-1):
            t-=L[k]; dep[k]=t
            if k>0: t-=(dwell(path[k]) or 1); arr[k]=t
    for j in range(len(idx)-1):
        a,b=idx[j],idx[j+1]
        o=orient(path[a],path[b])
        if dep[a] is None: dep[a]=PHI[path[a]]+OFF[path[a]]['d1' if o==1 else 'd2']
        raw=sum(L[k] for k in range(a,b))+sum((dwell(path[k]) or 1) for k in range(a+1,b))
        tgt=PHI[path[b]]-OFF[path[b]]['a1' if o==1 else 'a2']
        ts=SOLL.get((path[a],path[b]))
        need=(tgt-dep[a])%30
        total=ts if (ts is not None and ts>=raw and (ts-need)%30==0) else None
        if total is None:
            total=need if need>0 else 30
            while total<raw: total+=30
        spread(a,b,dep[a],total)
        arr[b]=dep[a]+total
        if j+1<len(idx)-1:
            o2=orient(path[b],path[idx[j+2]])
            d=PHI[path[b]]+OFF[path[b]]['d1' if o2==1 else 'd2']
            while d-arr[b]<4: d+=30
            while d-arr[b]>=34: d-=30
            dep[b]=d
        else:
            dep[b]=arr[b]+OFF[path[b]]['d1' if o==1 else 'd2']+OFF[path[b]]['a1' if o==1 else 'a2']
    iL=idx[-1]
    if iL<n-1:
        t=dep[iL]
        for k in range(iL,n-1):
            t+=L[k]; arr[k+1]=t
            if k+1<n-1: t+=(dwell(path[k+1]) or 1); dep[k+1]=t
    dep[n-1]=None; arr[0]=None
    return [(path[i],arr[i],dep[i]) for i in range(n)]
