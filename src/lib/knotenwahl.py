"""Vergleicht Knotenmengen anhand der tatsächlichen Reisezeitverlängerung."""
import sys; sys.path.insert(0,'/root/bahn')
import sqlite3, collections, statistics, os, json, opt2, importlib
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
nm=dict(cur.execute("SELECT station_id,name FROM station")); name2id=dict(cur.execute("SELECT name,station_id FROM station"))
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((nm[s2st[sid]],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,verkehrstage,gattung,linie,betreiber FROM trip_summary")}
LIN=list(cur.execute("SELECT linie_key,laufweg,fahrten_tag,fahrzeit_min FROM linie WHERE produkt IN ('ICE','IC') AND fahrten_tag>=1"))
legs=collections.defaultdict(lambda: collections.defaultdict(list))
for tid,p in seq.items():
    kat,vt,g,lin,op=TS[tid]; key=f"{g} {lin}" if lin else f"{g} ({op})"
    for i in range(len(p)-1):
        a,b=p[i],p[i+1]; dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if 0<t<=400: legs[key][(a[0],b[0])].append(t)
KANTE={}
for a,b,t in cur.execute("SELECT a,b,t_min FROM kante"): KANTE[(a,b)]=t; KANTE[(b,a)]=t
HALTE=dict(cur.execute("SELECT name,halte_tag FROM bahnhof_bedienung"))
def legt(key,a,b):
    v=legs[key].get((a,b)) or legs[key].get((b,a))
    if v: return max(1,int(statistics.median(v)))
    return KANTE.get((a,b))
def dwell(s,NODES): return 6 if s in NODES else (2 if HALTE.get(s,0)>60 else 1)
def build_edges(NODES):
    E=collections.defaultdict(lambda:{'req':[], 'spr':0.,'ice':0.,'ic':0.,'t':[]})
    for tid,p in seq.items():
        kat,vt,g,lin,op=TS[tid]; vt=vt/31
        idx=[i for i,x in enumerate(p) if x[0] in NODES]
        for j in range(len(idx)-1):
            a,b=p[idx[j]],p[idx[j+1]]
            dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
            if dep is None or arr is None: continue
            t=(arr-dep)//60
            if t<=0 or t>500: continue
            k=(a[0],b[0]) if a[0]<b[0] else (b[0],a[0]); e=E[k]; e['t'].append(t)
            if kat=='ICE-SPRINTER': e['spr']+=vt
            elif kat=='ICE': e['ice']+=vt
            elif kat=='IC': e['ic']+=vt
    # Systemfahrzeit je Kante aus den Linien
    lreq=collections.defaultdict(list)
    for key,lauf,ft,fz in LIN:
        path=lauf.split(' > '); idx=[i for i,s in enumerate(path) if s in NODES]
        for j in range(len(idx)-1):
            a,b=idx[j],idx[j+1]
            L=[legt(key,path[k],path[k+1]) for k in range(a,b)]
            if any(x is None for x in L): continue
            raw=sum(L)+sum(dwell(path[k],NODES) for k in range(a+1,b))
            kk=(path[a],path[b]) if path[a]<path[b] else (path[b],path[a])
            lreq[kk]+=[raw]*max(1,int(round(ft)))
    out=[]
    for k,e in E.items():
        tot=e['spr']+e['ice']+e['ic']
        if tot<0.5: continue
        tmin=min(e['t'])
        v=sorted(lreq.get(k,[]))
        base=tmin if not v else max(tmin, min(v[min(len(v)-1,int(len(v)*0.75))], int(round(tmin*1.25))))
        out.append((k[0],k[1],base,base,3*e['spr']+2*e['ice']+e['ic'],e['spr'],e['ice'],e['ic']))
    return out
def reisezeit(NODES, PHI, TSOLL):
    """mittlere Reisezeitverlängerung der Linien gegenüber heute, gewichtet nach Fahrten"""
    fit=lambda t,d: min([x for x in range(d%30,1500,30) if x>=t])
    tot=0.0; wsum=0.0; det=[]
    for key,lauf,ft,fz in LIN:
        path=lauf.split(' > ')
        L=[legt(key,path[k],path[k+1]) for k in range(len(path)-1)]
        if any(x is None for x in L): continue
        heute=sum(L)+sum(dwell(path[k],set()) for k in range(1,len(path)-1))
        idx=[i for i,s in enumerate(path) if s in NODES]
        soll=0
        if len(idx)<2: soll=heute
        else:
            soll+=sum(L[k] for k in range(0,idx[0]))+sum(dwell(path[k],NODES) for k in range(1,idx[0]))
            for j in range(len(idx)-1):
                a,b=idx[j],idx[j+1]
                raw=sum(L[k] for k in range(a,b))+sum(dwell(path[k],NODES) for k in range(a+1,b))
                dphi=PHI[path[b]]-PHI[path[a]]-6
                ts=TSOLL.get((path[a],path[b]))
                soll += (ts if (ts is not None and ts>=raw) else fit(raw,dphi))
                if j<len(idx)-2: soll+=6
            soll+=sum(L[k] for k in range(idx[-1],len(path)-1))+sum(dwell(path[k],NODES) for k in range(idx[-1]+1,len(path)-1))
        tot+=ft*(soll-heute); wsum+=ft; det.append((key,heute,soll,soll-heute))
    det.sort(key=lambda x:-x[3])
    return tot/wsum, det
