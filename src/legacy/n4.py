import sqlite3, collections, json, os, statistics as st, time, opt2
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
nm=dict(cur.execute("SELECT station_id,name FROM station"))
name2id=dict(cur.execute("SELECT name,station_id FROM station"))
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((s2st[sid],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,verkehrstage FROM trip_summary")}
ALL=[r[0] for r in cur.execute("SELECT name FROM itf_knotenzeit")]
GEW=dict(cur.execute("SELECT name,gewicht FROM itf_knotenzeit"))
KERN={'Berlin Hbf','Hamburg Hbf','Hannover Hbf','Köln Hbf','Frankfurt(Main)Hbf','Mannheim Hbf','Stuttgart Hbf',
 'München Hbf','Nürnberg Hbf','Erfurt Hbf','Leipzig Hbf','Dresden Hbf','Bremen Hbf','Dortmund Hbf','Duisburg Hbf',
 'Düsseldorf Hbf','Essen Hbf','Kassel-Wilhelmshöhe','Fulda','Würzburg Hbf','Karlsruhe Hbf','Basel SBB','Ulm Hbf',
 'Augsburg Hbf','Halle(Saale)Hbf','Münster(Westf)Hbf','Osnabrück Hbf','Bielefeld Hbf','Magdeburg Hbf','Freiburg(Breisgau) Hbf',
 'Saarbrücken Hbf','Rostock Hbf','Kiel Hbf','Aachen Hbf','Göttingen'}
def edges_for(nodes):
    NID={name2id[n] for n in nodes}
    E=collections.defaultdict(lambda:{'t':[], 'spr':0.,'ice':0.,'ic':0.})
    for tid,p in seq.items():
        kat,vt=TS[tid]; vt=vt/31
        idx=[i for i,x in enumerate(p) if x[0] in NID]
        for j in range(len(idx)-1):
            a,b=p[idx[j]],p[idx[j+1]]
            dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
            if dep is None or arr is None: continue
            t=(arr-dep)//60
            if t<=0 or t>420: continue
            k=(a[0],b[0]) if a[0]<b[0] else (b[0],a[0]); e=E[k]; e['t'].append(t)
            if kat=='ICE-SPRINTER': e['spr']+=vt
            elif kat=='ICE': e['ice']+=vt
            elif kat=='IC': e['ic']+=vt
    out=[]
    for (a,b),e in E.items():
        tot=e['spr']+e['ice']+e['ic']
        if tot<0.5: continue
        ts=sorted(e['t']); p15=ts[max(0,int(len(ts)*0.15))]
        out.append((nm[a],nm[b],ts[0],p15,3*e['spr']+2*e['ice']+e['ic'],e['spr'],e['ice'],e['ic']))
    return out
def score(nodes, runs=150):
    r=opt2.solve(edges_for(nodes), allow_acc=False, runs=runs)
    exc=sum(x[7] for x in r['kanten'] if x[6]>25)/r['gewicht']*100
    return r, r['kosten_je_gewicht'], round(exc,1)
t0=time.time()
nodes=set(ALL)
r,kg,exc=score(nodes, runs=300)
print(f"Start: {len(nodes)} Knoten, Kosten/Gewicht {kg}, Ø Reserve {r['reserve_pct']} %, Kanten>25% {exc} % des Verkehrs", flush=True)
# Kandidaten: Nicht-Kernknoten, sortiert nach verursachtem Überschuss
def blame(res):
    b=collections.Counter()
    for x in res['kanten']:
        if x[6]>14: b[x[0]]+=x[7]*(x[6]-14); b[x[1]]+=x[7]*(x[6]-14)
    return b
cand=[n for n,_ in blame(r).most_common() if n not in KERN][:14]
print("Abstufungskandidaten:", cand, flush=True)
best=(kg,set(nodes),r)
for n in cand:
    trial=set(best[1])-{n}
    rr,kk,ee=score(trial, runs=180)
    mark='ÜBERNOMMEN' if kk<best[0]-0.005 else 'verworfen'
    print(f"  {n[:30]:30s} -> Kosten/Gewicht {kk:6.3f} (bisher {best[0]:6.3f})  {mark}", flush=True)
    if kk<best[0]-0.005: best=(kk,trial,rr)
print(f"\nEndauswahl: {len(best[1])} Knoten, {len(ALL)-len(best[1])} abgestuft", flush=True)
final=opt2.solve(edges_for(best[1]), allow_acc=False, runs=1200)
print(f"N4 final: Kosten {final['kosten']}  Kosten/Gewicht {final['kosten_je_gewicht']}  "
      f"Sollband {final['sollband_pct']} %  Ø Reserve {final['reserve_pct']} %  Beschleunigung {final['beschl']}", flush=True)
json.dump({'knoten':sorted(best[1]),'abgestuft':sorted(set(ALL)-best[1]),
           'ergebnis':final}, open('/root/bahn/n4.json','w'), ensure_ascii=False)
print('Dauer', round(time.time()-t0),'s')
