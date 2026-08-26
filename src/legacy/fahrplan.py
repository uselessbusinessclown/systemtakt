"""Erzeugt aus dem ITF-Knotenplan einen vollständigen Minutenfahrplan für alle Linien."""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, collections, os, json, statistics as st
con=sqlite3.connect(DB); cur=con.cursor()
PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
TSOLL={}
for a,b,ts in cur.execute("SELECT a,b,t_soll FROM itf_ergebnis"): TSOLL[(a,b)]=ts; TSOLL[(b,a)]=ts
HALTE=dict(cur.execute("SELECT name,halte_tag FROM bahnhof_bedienung"))
KANTE={}
for a,b,t in cur.execute("SELECT a,b,t_min FROM kante"): KANTE[(a,b)]=t; KANTE[(b,a)]=t

# --- beobachtete Fahrzeiten je Linie und Halteabfolge
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station")); nm=dict(cur.execute("SELECT station_id,name FROM station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((nm[s2st[sid]],arr,dep))
TL={r[0]:r[1:] for r in cur.execute("SELECT trip_id,gattung,linie,betreiber,kategorie FROM trip_summary")}
legs=collections.defaultdict(lambda: collections.defaultdict(list))   # linie -> (a,b) -> [min]
for tid,p in seq.items():
    g,lin,op,kat=TL[tid]
    key=f"{g} {lin}" if lin else f"{g} ({op})"
    for i in range(len(p)-1):
        a,b=p[i],p[i+1]
        dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if 0<t<=400: legs[key][(a[0],b[0])].append(t)

def leg_time(key,a,b):
    v=legs[key].get((a,b)) or legs[key].get((b,a))
    if v: return max(1,int(st.median(v)))
    if (a,b) in KANTE: return max(1,KANTE[(a,b)])
    return None
def dwell(nameOfStation):
    if nameOfStation in PHI: return 6
    return 2 if HALTE.get(nameOfStation,0)>60 else 1

def fit(t,dphi):
    """kleinste Soll-Zeit >= t mit t ≡ dphi (mod 30) — neubaufrei"""
    return min([x for x in range(dphi%30,1200,30) if x>=t])

def plan_line(key, path):
    """Minutenplan Richtung 1: Liste (Station, Ankunft, Abfahrt) in absoluten Minuten-Offsets."""
    n=len(path)
    if n<2: return None
    legt=[leg_time(key,path[i],path[i+1]) for i in range(n-1)]
    if any(t is None for t in legt): return None
    dw=[dwell(s) for s in path]
    arr=[None]*n; dep=[None]*n
    idx=[i for i,s in enumerate(path) if s in PHI]

    def spread(i0,i1,start,total):
        raw=[legt[k] for k in range(i0,i1)]
        dws=[dw[k] for k in range(i0+1,i1)]
        avail=total-sum(dws)
        s0=sum(raw) or 1
        sc=[max(1,int(round(r*avail/s0))) for r in raw]
        d=avail-sum(sc); j=0
        while d!=0 and j<100000:
            i=j%len(sc)
            if d>0: sc[i]+=1; d-=1
            elif sc[i]>1: sc[i]-=1; d+=1
            j+=1
        t=start
        for j2,k in enumerate(range(i0,i1)):
            t+=sc[j2]; arr[k+1]=t
            if k+1<i1: t+=dw[k+1]; dep[k+1]=t

    if not idx:
        dep[0]=0; t=0
        for k in range(n-1):
            t+=legt[k]; arr[k+1]=t
            if k+1<n-1: t+=dw[k+1]; dep[k+1]=t
        return [(path[i],arr[i],dep[i]) for i in range(n)]

    a0=idx[0]; A=PHI[path[a0]]
    if a0==0: dep[0]=A+3
    else:
        arr[a0]=A-3; dep[a0]=A+3
        t=arr[a0]
        for k in range(a0-1,-1,-1):
            t-=legt[k]; dep[k]=t
            if k>0: t-=dw[k]; arr[k]=t
    for j in range(len(idx)-1):
        a,b=idx[j],idx[j+1]
        if dep[a] is None: dep[a]=PHI[path[a]]+3
        raw=sum(legt[k] for k in range(a,b))+sum(dw[k] for k in range(a+1,b))
        dphi=PHI[path[b]]-PHI[path[a]]-6
        ts=TSOLL.get((path[a],path[b]))
        total=ts if (ts is not None and ts>=raw) else fit(raw,dphi)
        spread(a,b,dep[a],total)
        arr[b]=dep[a]+total; dep[b]=arr[b]+6
    iL=idx[-1]
    if iL<n-1:
        if dep[iL] is None: dep[iL]=PHI[path[iL]]+3
        t=dep[iL]
        for k in range(iL,n-1):
            t+=legt[k]; arr[k+1]=t
            if k+1<n-1: t+=dw[k+1]; dep[k+1]=t
    dep[n-1]=None; arr[0]=None
    return [(path[i],arr[i],dep[i]) for i in range(n)]

def plan_line_rev(key, path):
    """Gegenrichtung: gleiche Knotendisziplin, umgekehrter Laufweg."""
    return plan_line(key, list(reversed(path)))
