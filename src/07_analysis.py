import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, os, collections, statistics as st, math
con=sqlite3.connect(DB); cur=con.cursor()
S={r[0]:r[1:] for r in cur.execute("SELECT station_id,name,lat,lon,land_iso,stadt FROM station")}
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
def hav(a,b,c,d):
    R=6371.0088; p=math.pi/180
    return 2*R*math.asin(math.sqrt(math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2))

seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((s2st[sid],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("""SELECT trip_id,linie,gattung,produkt,kategorie,betreiber,verkehrstage,
        von,nach,dauer_min,halte,von_stadt,nach_stadt,km_luftlinie FROM trip_summary""")}

cur.executescript("""
DROP TABLE IF EXISTS linie; DROP TABLE IF EXISTS linie_halt;
DROP TABLE IF EXISTS kante; DROP TABLE IF EXISTS bahnhof_bedienung;
CREATE TABLE linie(linie_key TEXT PRIMARY KEY, gattung TEXT, nummer TEXT, produkt TEXT,
  betreiber TEXT, bezeichnung TEXT, laufweg TEXT, halte_typisch INT,
  fahrten_tag REAL, fahrten_tag_sprinter REAL, fahrzeit_min INT, km_luftlinie REAL, vschnitt REAL,
  endpunkt_a TEXT, endpunkt_b TEXT);
CREATE TABLE linie_halt(linie_key TEXT, station_id TEXT, name TEXT, reihenfolge INT, fahrten_tag REAL);
CREATE TABLE kante(a_id TEXT, b_id TEXT, a TEXT, b TEXT, km REAL,
  t_min INT, t_median INT, t_max INT, n_trassen INT, fahrten_tag REAL,
  produkte TEXT, PRIMARY KEY(a_id,b_id));
CREATE TABLE bahnhof_bedienung(station_id TEXT PRIMARY KEY, name TEXT, stadt TEXT, land TEXT, bundesland TEXT,
  lat REAL, lon REAL, halte_tag REAL, halte_ice REAL, halte_sprinter REAL, halte_ic REAL,
  linien INT, linien_liste TEXT, rang INT);
""")

# ---------- Linien ----------
byline=collections.defaultdict(list)
for tid,p in seq.items():
    g,nummer,prod,kat,betr,vt = TS[tid][1],TS[tid][0],TS[tid][2],TS[tid][3],TS[tid][4],TS[tid][5]
    key=f"{g} {nummer}" if nummer else f"{g} ({betr})"
    byline[key].append(tid)

lrows=[];lhrows=[]
for key,tids in byline.items():
    pats=collections.Counter()
    for t in tids: pats[tuple(x[0] for x in seq[t])]+= TS[t][5]
    pat,_=pats.most_common(1)[0]
    g=TS[tids[0]][1]; nummer=TS[tids[0]][0]; prod=TS[tids[0]][2]
    betr=collections.Counter(TS[t][4] for t in tids).most_common(1)[0][0]
    ft=sum(TS[t][5] for t in tids)/31
    fs=sum(TS[t][5] for t in tids if TS[t][3]=='ICE-SPRINTER')/31
    full=[t for t in tids if tuple(x[0] for x in seq[t])==pat]
    dur=int(st.median([TS[t][8] for t in full])) if full else None
    km =round(st.median([TS[t][12] for t in full]),1) if full else None
    a,b=S[pat[0]][0],S[pat[-1]][0]
    lrows.append((key,g,nummer,prod,betr,f"{a} – {b}",' > '.join(S[x][0] for x in pat),len(pat),
                  round(ft,2),round(fs,2),dur,km, round(km/(dur/60),1) if dur else None, a,b))
    cnt=collections.Counter()
    for t in tids:
        for x in seq[t]: cnt[x[0]]+=TS[t][5]
    order={s:i for i,s in enumerate(pat)}
    for sidd,v in cnt.items():
        lhrows.append((key,sidd,S[sidd][0],order.get(sidd,999),round(v/31,2)))
cur.executemany("INSERT INTO linie VALUES(%s)"%','.join('?'*15), lrows)
cur.executemany("INSERT INTO linie_halt VALUES(?,?,?,?,?)", lhrows)

# ---------- Kanten ----------
E=collections.defaultdict(lambda: {'t':[], 'n':0, 'f':0.0, 'p':collections.Counter()})
for tid,p in seq.items():
    prod=TS[tid][3]; vt=TS[tid][5]
    for i in range(len(p)-1):
        a,ar,ad=p[i]; b,br,bd=p[i+1]
        dep=ad if ad is not None else ar; arr=br if br is not None else bd
        if dep is None or arr is None: continue
        t=(arr-dep)//60
        if t<=0 or t>400: continue
        k=(a,b) if a<b else (b,a)
        e=E[k]; e['t'].append(t); e['n']+=1; e['f']+=vt/31; e['p'][prod]+=1
krows=[]
for (a,b),e in E.items():
    krows.append((a,b,S[a][0],S[b][0], round(hav(S[a][1],S[a][2],S[b][1],S[b][2]),1),
                  min(e['t']), int(st.median(e['t'])), max(e['t']), e['n'], round(e['f'],2),
                  ','.join(sorted(e['p']))))
cur.executemany("INSERT INTO kante VALUES(%s)"%','.join('?'*11), krows)

# ---------- Bahnhofsbedienung ----------
B=collections.defaultdict(lambda: {'all':0.0,'ice':0.0,'spr':0.0,'ic':0.0,'lin':set()})
for tid,p in seq.items():
    kat=TS[tid][3]; vt=TS[tid][5]/31; nummer=TS[tid][0]; g=TS[tid][1]; betr=TS[tid][4]
    key=f"{g} {nummer}" if nummer else f"{g} ({betr})"
    for x in p:
        d=B[x[0]]; d['all']+=vt; d['lin'].add(key)
        if kat=='ICE-SPRINTER': d['spr']+=vt; d['ice']+=vt
        elif kat=='ICE': d['ice']+=vt
        elif kat=='IC': d['ic']+=vt
brows=[]
for sid,d in B.items():
    n,lat,lon,land,city=S[sid][0],S[sid][1],S[sid][2],S[sid][3],S[sid][4]
    bl=list(cur.execute("SELECT bundesland FROM station WHERE station_id=?",(sid,)))[0][0]
    brows.append((sid,n,city,land,bl,lat,lon,round(d['all'],2),round(d['ice'],2),round(d['spr'],2),
                  round(d['ic'],2),len(d['lin']),', '.join(sorted(d['lin'])),0))
cur.executemany("INSERT INTO bahnhof_bedienung VALUES(%s)"%','.join('?'*14), brows)
cur.execute("""UPDATE bahnhof_bedienung SET rang=(SELECT COUNT(*)+1 FROM bahnhof_bedienung b2
               WHERE b2.halte_tag > bahnhof_bedienung.halte_tag)""")
con.commit()
print('Linien:',len(lrows),' Kanten:',len(krows),' bediente Bahnhöfe:',len(brows))
print('\nTop-20 Bahnhöfe (Halte/Tag, alle FV-Züge):')
for r in cur.execute("""SELECT rang,name,land,ROUND(halte_tag,1),ROUND(halte_ice,1),ROUND(halte_sprinter,1),ROUND(halte_ic,1),linien
   FROM bahnhof_bedienung ORDER BY halte_tag DESC LIMIT 20"""): print('  ',r)
con.close()
