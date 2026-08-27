"""Taktqualität des heutigen Fahrplans, und das Soll-Skelett je Linie.

Beantwortet die Frage, wie weit der heutige Fernverkehr schon im Takt fährt: je Linie,
Knoten und Fahrtrichtung wird die Verteilung der Abfahrtsminuten ausgewertet und in drei
Stufen bewertet.

  60-min-Takt stabil          eine Minute trägt mindestens 60 % der Abfahrten
  Zwei-Lagen-Takt (120 min)   zwei Minuten tragen zusammen mindestens 70 %
  kein systematischer Takt    auch zu zweit reicht es nicht

Die zweite Stufe ist der häufige deutsche Fall: ein Zweistundentakt in zwei Lagen, der
sich zu einem unsauberen Stundentakt überlagert. Die zyklische Streuung allein erkennt
ihn nicht — sie ist dort hoch, obwohl der Takt sauber ist.
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, os, collections
con=sqlite3.connect(DB); cur=con.cursor()

# --- Rotation: Berlin Hbf = :00
# Der Knotenplan ist nur bis auf eine gemeinsame Verschiebung eindeutig (Ergebnis 3 der
# Studie). Hier wird sie so gelegt, dass Berlin auf :00 liegt.
#
# Die Ankunfts- und Abfahrtsfenster werden dabei aus den richtungsgetrennten Offsets
# off_a1/off_d1 (Richtung 1) und off_a2/off_d2 (Richtung 2) neu gebildet. Eine frühere
# Fassung schrieb hier pauschal ±3 Minuten — das ist die Symmetrie der Fassung 3 und
# würde die beidseitige Knotenbindung der Fassung 4 aus der Datenbank löschen.
b=list(cur.execute("SELECT knotenminute FROM itf_knotenzeit WHERE name='Berlin Hbf'"))[0][0]
for sid,m,a1,d1,a2,d2 in list(cur.execute(
        "SELECT station_id,knotenminute,off_a1,off_d1,off_a2,off_d2 FROM itf_knotenzeit")):
    n=(m-b)%30
    cur.execute("UPDATE itf_knotenzeit SET knotenminute=?, knotenzeit=?, ankunft=?, abfahrt=? WHERE station_id=?",
      (n, f":{n:02d} / :{(n+30)%60:02d}",
       f"Ri1 :{(n-a1)%60:02d} · Ri2 :{(n-a2)%60:02d}",
       f"Ri1 :{(n+d1)%60:02d} · Ri2 :{(n+d2)%60:02d}", sid))
con.commit()

PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
OFF={r[0]:r[1:] for r in cur.execute(
    "SELECT name,off_a1,off_d1,off_a2,off_d2 FROM itf_knotenzeit")}

# --- Soll-Fahrzeiten, richtungsabhängig
# itf_ergebnis speichert je Kante zwei Zeiten: t_soll_r1 gilt in der gespeicherten
# Orientierung a→b, t_soll_r2 in der Gegenrichtung b→a. Sie unterscheiden sich bei 37 der
# 68 Kanten, im Mittel um 3,6 und im Höchstfall um 23 Minuten — die Richtung ist also
# keine Formalie. RI merkt sich zusätzlich, welche Richtung eine Kante darstellt, damit
# unten das passende Knotenfenster gewählt wird.
TSOLL, RI = {}, {}
for a,b2,r1,r2 in cur.execute("SELECT a,b,t_soll_r1,t_soll_r2 FROM itf_ergebnis"):
    TSOLL[(a,b2)]=r1; RI[(a,b2)]=1
    TSOLL[(b2,a)]=r2; RI[(b2,a)]=2

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
  minuten TEXT, haeufigste_minute INT, anteil_haeufigste REAL, top2_anteil REAL,
  streuung REAL, takt_bewertung TEXT);""")
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
    haeufigste=c.most_common(2)
    top,tv=haeufigste[0]
    # Anteile aus den Rohwerten, nicht aus der gerundeten Anzeigespalte `minuten`.
    # Eine frühere Fassung las sie aus dem Anzeigetext zurück und kam dadurch auf
    # Anteile über 100 %.
    anteil1=tv/tot
    top2=sum(v for _,v in haeufigste)/tot
    # Streuung um die häufigste Minute (zyklisch) — nur noch als Kennwert ausgewiesen,
    # nicht mehr als Bewertungsgrundlage; beim Zwei-Lagen-Takt ist sie irreführend hoch.
    var=sum(v*min((m-top)%60,(top-m)%60)**2 for m,v in c.items())/tot
    sd=var**0.5
    bew=("60-min-Takt stabil" if anteil1>=0.6
         else "Zwei-Lagen-Takt (120 min)" if top2>=0.7
         else "kein systematischer Takt")
    rows.append((key,kn,ziel,round(tot,2), ', '.join(f"{m:02d}({v:.1f})" for m,v in c.most_common(6)),
                 top, round(anteil1,2), round(top2,2), round(sd,1), bew))
cur.executemany("INSERT INTO ist_takt VALUES(?,?,?,?,?,?,?,?,?,?)", rows)

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
        a1,d1,a2,d2 = OFF[k]
        an = ab = t = None
        if i>0:                                   # Ankunft aus der Richtung der Zulaufkante
            vor=knoten[i-1]
            t=TSOLL.get((vor,k))
            kum += (t or 0) + 6                   # 6 Minuten Aufenthalt im Knoten
            an = (PHI[k] - (a1 if RI.get((vor,k),1)==1 else a2)) % 60
        if i<len(knoten)-1:                       # Abfahrt in der Richtung der Ablaufkante
            nach=knoten[i+1]
            ab = (PHI[k] + (d1 if RI.get((k,nach),1)==1 else d2)) % 60
        sk.append((key,prio,kat,i,k,an,ab,t,kum))
cur.executemany("INSERT INTO soll_skelett VALUES(?,?,?,?,?,?,?,?,?)", sk)
con.commit()

print("Knotenzeiten nach Rotation (Berlin = :00):")
for r in cur.execute("SELECT name,knotenzeit,ankunft,abfahrt,grad FROM itf_knotenzeit ORDER BY gewicht DESC"):
    print(f"  {r[0][:24]:24s} {r[1]:12s} an {r[2]:20s} ab {r[3]:20s} Grad {r[4]:2d}")
print("\nIst-Taktqualität heute (gewichtet nach Abfahrten/Tag):")
for r in cur.execute("SELECT takt_bewertung,COUNT(*),ROUND(SUM(abfahrten_tag),1) FROM ist_takt GROUP BY 1 ORDER BY 3 DESC"):
    print(f"  {r[0]:<28}{r[1]:>5} Lagen{r[2]:>10} Abf./Tag")
print("\nLagen ohne erkennbaren Takt an Großknoten:")
for r in cur.execute("""SELECT linie,knoten,richtung,abfahrten_tag,anteil_haeufigste,top2_anteil,minuten
  FROM ist_takt WHERE abfahrten_tag>4 AND takt_bewertung='kein systematischer Takt'
  ORDER BY abfahrten_tag DESC LIMIT 12"""):
    print(f"  {r[0]:<10}{r[1][:22]:<23}→ {r[2][:16]:<17}{r[3]:>5.1f}/Tag  "
          f"häufigste {r[4]:.0%}, zwei {r[5]:.0%}   {r[6][:40]}")
con.close()
