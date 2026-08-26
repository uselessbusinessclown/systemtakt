import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, os, collections, statistics as st
con=sqlite3.connect(DB); cur=con.cursor()

NODES = ["Kiel Hbf","Hamburg Hbf","Rostock Hbf","Schwerin Hbf","Bremen Hbf","Osnabrück Hbf",
 "Münster(Westf)Hbf","Hannover Hbf","Wolfsburg Hbf","Braunschweig Hbf","Magdeburg Hbf","Berlin Hbf",
 "Leipzig Hbf","Halle(Saale)Hbf","Erfurt Hbf","Dresden Hbf","Bielefeld Hbf","Hamm(Westf)Hbf",
 "Dortmund Hbf","Essen Hbf","Duisburg Hbf","Oberhausen Hbf","Düsseldorf Hbf","Wuppertal Hbf",
 "Hagen Hbf","Köln Hbf","Siegburg/Bonn","Bonn Hbf","Koblenz Hbf","Mainz Hbf","Wiesbaden Hbf",
 "Frankfurt(Main)Hbf","Hanau Hbf","Fulda","Kassel-Wilhelmshöhe","Göttingen","Würzburg Hbf",
 "Nürnberg Hbf","Ingolstadt Hbf","Augsburg Hbf","München Hbf","Ulm Hbf","Stuttgart Hbf",
 "Heidelberg Hbf","Mannheim Hbf","Karlsruhe Hbf","Offenburg","Freiburg(Breisgau) Hbf","Basel SBB",
 "Saarbrücken Hbf","Kaiserslautern Hbf","Hildesheim Hbf","Lutherstadt Wittenberg Hbf","Bamberg",
 "Regensburg Hbf","Aachen Hbf","Flensburg","Stralsund Hbf","Emden Hbf","Trier Hbf","Gießen",
 "Marburg(Lahn)","Paderborn Hbf","Singen(Hohentwiel)","Lindau-Reutin","Salzburg Hbf","Passau Hbf"]
name2id=dict(cur.execute("SELECT name,station_id FROM station"))
NID={name2id[n]:n for n in NODES if n in name2id}
print("nicht im Netz:", [n for n in NODES if n not in name2id])

s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((s2st[sid],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,verkehrstage,gattung,linie FROM trip_summary")}

E=collections.defaultdict(lambda:{'t':[],'zw':[],'spr':0.,'ice':0.,'ic':0.,'lin':collections.Counter(),'zwn':None})
nm=dict(cur.execute("SELECT station_id,name FROM station"))
for tid,p in seq.items():
    kat,vt,g,lin=TS[tid]; vt=vt/31
    idx=[i for i,x in enumerate(p) if x[0] in NID]
    for j in range(len(idx)-1):
        i0,i1=idx[j],idx[j+1]
        a,b=p[i0],p[i1]
        dep=a[2] if a[2] is not None else a[1]; arr=b[1] if b[1] is not None else b[2]
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if t<=0 or t>420: continue
        key=(a[0],b[0]) if a[0]<b[0] else (b[0],a[0])
        e=E[key]; e['t'].append(t); e['zw'].append(i1-i0-1)
        if kat=='ICE-SPRINTER': e['spr']+=vt
        elif kat=='ICE': e['ice']+=vt
        elif kat=='IC': e['ic']+=vt
        if lin: e['lin'][f"{g} {lin}"]+=1
        if e['zwn'] is None or (i1-i0-1)<len(e['zwn']):
            e['zwn']=[nm[x[0]] for x in p[i0+1:i1]]

cur.executescript("""DROP TABLE IF EXISTS itf_kante;
CREATE TABLE itf_kante(a_id TEXT,b_id TEXT,a TEXT,b TEXT,
 t_min INT,t_p15 INT,t_median INT,zwischenhalte INT,zwischen TEXT,
 f_sprinter REAL,f_ice REAL,f_ic REAL,f_gesamt REAL,gewicht REAL,linien TEXT,
 PRIMARY KEY(a_id,b_id));""")
rows=[]
for (a,b),e in E.items():
    tot=e['spr']+e['ice']+e['ic']
    if tot < 0.5: continue
    ts=sorted(e['t']); p15=ts[max(0,int(len(ts)*0.15))]
    w = 3*e['spr'] + 2*e['ice'] + 1*e['ic']
    rows.append((a,b,nm[a],nm[b],ts[0],p15,int(st.median(ts)),min(e['zw']),
                 ' > '.join(e['zwn'] or []), round(e['spr'],2),round(e['ice'],2),round(e['ic'],2),
                 round(tot,2), round(w,2), ', '.join(k for k,_ in e['lin'].most_common(8))))
cur.executemany("INSERT INTO itf_kante VALUES(%s)"%','.join('?'*15), rows)
con.commit()
print('ITF-Knoten:',len(NID),' ITF-Kanten:',len(rows))
for r in cur.execute("SELECT a,b,t_min,t_p15,zwischenhalte,f_gesamt,gewicht FROM itf_kante ORDER BY gewicht DESC LIMIT 25"):
    print(f"  {r[0][:22]:22s}-{r[1][:22]:22s} tmin{r[2]:4d} t15{r[3]:4d} zw{r[4]:2d} f{r[5]:6.1f} w{r[6]:7.1f}")
con.close()
