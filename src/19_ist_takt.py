import sqlite3, os, collections, statistics as st
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
# --- Rotation: Berlin Hbf = :00
b=list(cur.execute("SELECT knotenminute FROM itf_knotenzeit WHERE name='Berlin Hbf'"))[0][0]
for sid,m in list(cur.execute("SELECT station_id,knotenminute FROM itf_knotenzeit")):
    n=(m-b)%30
    cur.execute("""UPDATE itf_knotenzeit SET knotenminute=?, knotenzeit=?, ankunft=?, abfahrt=? WHERE station_id=?""",
      (n, f":{n:02d} / :{(n+30)%60:02d}", f":{(n-3)%60:02d} / :{(n+27)%60:02d}",
       f":{(n+3)%60:02d} / :{(n+33)%60:02d}", sid))
con.commit()

PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
TSOLL={}
for a,b2,ts in cur.execute("SELECT a,b,t_soll FROM itf_ergebnis"):
    TSOLL[(a,b2)]=ts; TSOLL[(b2,a)]=ts

# --- Ist-Takt-Analyse: Abfahrtsminuten je Linie/Knoten
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
nm=dict(cur.execute("SELECT station_id,name FROM station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((s2st[sid],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,gattung,linie,kategorie,verkehrstage,von_stadt,nach_stadt FROM trip_summary")}
KN=set(PHI)
cur.executescript("""DROP TABLE IF EXISTS ist_takt;
CREATE TABLE ist_takt(linie TEXT, knoten TEXT, richtung TEXT, abfahrten_tag REAL,
  minuten TEXT, haeufigste_minute INT, anteil_haeufigste REAL, streuung REAL, takt_bewertung TEXT);""")
D=collections.defaultdict(lambda: collections.Counter())
for tid,p in seq.items():
    g,lin,kat,vt,vs,ns=TS[tid]
    if not lin: continue
    key=f"{g} {lin}"
    ziel=ns
    for sid,arr,dep in p[:-1]:
        if nm[sid] in KN and dep is not None:
            D[(key,nm[sid],ziel)][(dep//60)%60] += vt/31
rows=[]
for (key,kn,ziel),c in D.items():
    tot=sum(c.values())
    if tot<1.0: continue
    top,tv=c.most_common(1)[0]
    # Streuung um die häufigste Minute (zyklisch)
    var=sum(v*min((m-top)%60,(top-m)%60)**2 for m,v in c.items())/tot
    sd=var**0.5
    bew = "Takt stabil" if sd<=3 else ("Takt erkennbar" if sd<=8 else "kein Takt")
    rows.append((key,kn,ziel,round(tot,2), ', '.join(f"{m:02d}({v:.1f})" for m,v in c.most_common(6)),
                 top, round(tv/tot,2), round(sd,1), bew))
cur.executemany("INSERT INTO ist_takt VALUES(?,?,?,?,?,?,?,?,?)", rows)

# --- Soll-Skelett je Linie
cur.executescript("""DROP TABLE IF EXISTS soll_skelett;
CREATE TABLE soll_skelett(linie_key TEXT, prio INT, kategorie TEXT, folge INT, knoten TEXT,
  ankunft_min INT, abfahrt_min INT, kantenzeit_min INT, kum_min INT);""")
LIN=list(cur.execute("SELECT linie_key,laufweg,produkt,fahrten_tag,fahrten_tag_sprinter FROM linie"))
sk=[]
for key,lauf,prod,ft,fs in LIN:
    knoten=[x for x in lauf.split(' > ') if x in PHI]
    if len(knoten)<2: continue
    prio = 1 if fs>0.5 else (2 if prod=='ICE' else 3)
    kat = 'ICE-Sprinter' if prio==1 else ('ICE' if prio==2 else 'IC/EC')
    kum=0
    for i,k in enumerate(knoten):
        t = TSOLL.get((knoten[i-1],k)) if i>0 else None
        if i>0:
            if t is None: t=0
            kum += t + 6
        an = (PHI[k]-3)%60 if i>0 else None
        ab = (PHI[k]+3)%60 if i<len(knoten)-1 else None
        sk.append((key,prio,kat,i,k,an,ab,t,kum))
cur.executemany("INSERT INTO soll_skelett VALUES(?,?,?,?,?,?,?,?,?)", sk)
con.commit()

print("Knotenzeiten nach Rotation (Berlin = :00), Top 20:")
for r in cur.execute("SELECT name,knotenzeit,ankunft,abfahrt,gewicht,grad FROM itf_knotenzeit ORDER BY gewicht DESC LIMIT 20"):
    print(f"  {r[0][:26]:26s} {r[1]:12s} an {r[2]:12s} ab {r[3]:12s} Grad {r[5]:2d}")
print("\nIst-Taktqualität (gewichtet nach Abfahrten/Tag):")
for r in cur.execute("SELECT takt_bewertung,COUNT(*),ROUND(SUM(abfahrten_tag),1) FROM ist_takt GROUP BY 1 ORDER BY 3 DESC"): print('  ',r)
print("\nSchlechteste Taktlagen an Großknoten:")
for r in cur.execute("""SELECT linie,knoten,richtung,abfahrten_tag,streuung,minuten FROM ist_takt
  WHERE abfahrten_tag>4 ORDER BY streuung DESC LIMIT 12"""): print('  ',r)
con.close()
