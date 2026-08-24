
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, collections, os
con=sqlite3.connect(DB); cur=con.cursor()
BSTD=17   # Betriebsstunden 05–22 Uhr
STUFEN=[('120 min',BSTD//2+1),('60 min',BSTD),('30 min',2*BSTD)]
F=1.2
PHIm=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))

cur.executescript("""
DROP TABLE IF EXISTS ziel_linie; DROP TABLE IF EXISTS ziel_sprinter;
CREATE TABLE ziel_linie(prio INT, ebene TEXT, linie_key TEXT, bezeichnung TEXT, betreiber TEXT,
 fahrten_tag_ist REAL, richtungsfahrten_ist REAL, takt_ist TEXT, takt_ziel TEXT,
 richtungsfahrten_ziel INT, zuege_ziel_tag INT, veraenderung TEXT, km REAL,
 zugkm_ist INT, zugkm_ziel INT, takt_ziel_b TEXT, richtungsfahrten_ziel_b INT, zugkm_ziel_b INT,
 knotenfolge TEXT, laufweg TEXT);
CREATE TABLE ziel_sprinter(korridor TEXT PRIMARY KEY, relation TEXT, km REAL,
 fahrten_tag_ist REAL, takt_ziel TEXT, richtungsfahrten_ziel INT, zuege_ziel_tag INT,
 fahrzeit_ist_min INT, fahrzeit_ziel_min INT, knotenlage TEXT);
""")
# ---------- Ebene 1: Sprinter-Korridore ----------
KORR={'SPR-1':'Hamburg – Hannover – Frankfurt (+Flughafen)','SPR-2':'Hamburg – Bremen/Münster – Ruhr – Köln',
 'SPR-3':'Berlin – Hannover – Ruhr – Köln/Bonn','SPR-4':'Berlin – Halle/Erfurt – Nürnberg – München',
 'SPR-5':'Berlin – Halle/Erfurt – Frankfurt','SPR-6':'Frankfurt/Mannheim/Karlsruhe – Paris',
 'SPR-7':'Stuttgart – Nürnberg – Berlin'}
srows=[]
for k,label in KORR.items():
    d=list(cur.execute("""SELECT ROUND(SUM(verkehrstage)/31.0,2), MIN(dauer_min), MAX(km_luftlinie)
        FROM trip_summary WHERE sprinter_korridor=?""",(k,)))[0]
    ft, tmin, km = d[0] or 0, d[1], (d[2] or 0)*F
    rf_ziel=12                    # 2-h-Grundtakt + HVZ-Verdichtung
    srows.append((k,label,round(km,1),ft,'120 min Grundtakt, HVZ 60 min',rf_ziel,rf_ziel*2,tmin,
                  int(round(tmin*0.97)) if tmin else None,'Knotenlage der Endknoten, Zwischenknoten überholfrei'))
cur.executemany("INSERT INTO ziel_sprinter VALUES(?,?,?,?,?,?,?,?,?,?)", srows)

# ---------- Ebenen 2/3: Linien ----------
LK=list(cur.execute("""SELECT linie_key,bezeichnung,laufweg,produkt,betreiber,fahrten_tag,fahrten_tag_sprinter,km_luftlinie
                       FROM linie WHERE produkt IN ('ICE','IC')"""))
out=[]
for key,bez,lauf,prod,betr,ft,fs,km in LK:
    ft_net=max(0.0, ft-fs)            # Sprinterfahrten zählen zu Ebene 1
    rf=ft_net/2
    km=(km or 0)*F
    takt_ist = '~30 min' if rf>=17 else ('~60 min' if rf>=9 else ('~120 min' if rf>=4 else 'Einzelleistungen'))
    # Szenario A "Taktordnung": nächstgelegene saubere Taktstufe (volumenneutral)
    stufen=[('120 min',BSTD//2+1),('60 min',BSTD),('30 min',2*BSTD)]
    zielA=min(stufen,key=lambda s:abs(s[1]-rf)) if rf>=4.5 else ('Einzelleistungen', max(1,int(round(rf))))
    # Szenario B "Vollausbau ITF": mindestens Stundentakt, Hauptachsen 30 min
    if   rf<2:   zielB=('120 min (Teilstrecke)', BSTD//2+1)
    elif rf<=6:  zielB=('120 min', BSTD//2+1)
    elif rf<=14: zielB=('60 min', BSTD)
    else:        zielB=('30 min', 2*BSTD)
    ziel=zielA
    prio = 2 if prod=='ICE' else 3
    ebene= 'Ebene 2 – ICE' if prio==2 else 'Ebene 3 – IC/EC'
    d=ziel[1]-rf
    ver = f"+{d:.0f}" if d>0.5 else (f"{d:.0f}" if d<-0.5 else "±0")
    kn=[x for x in lauf.split(' > ') if x in PHIm]
    out.append((prio,ebene,key,bez,betr,round(ft_net,1),round(rf,1),takt_ist,ziel[0],ziel[1],ziel[1]*2,
                ver+" Fahrten/Ri/Tag", round(km,1), int(ft_net*km), int(ziel[1]*2*km),
                zielB[0], zielB[1], int(zielB[1]*2*km),
                ' > '.join(f"{x} :{PHIm[x]:02d}" for x in kn), lauf))
out.sort(key=lambda r:(r[0],-r[5]))
cur.executemany("INSERT INTO ziel_linie VALUES(%s)"%','.join('?'*20), out)

# ---------- Betriebsleistung ----------
cur.execute("DELETE FROM betriebsleistung")
cur.executescript('''DROP TABLE IF EXISTS betriebsleistung;
CREATE TABLE betriebsleistung(ebene TEXT, zugkm_tag_ist REAL, zugkm_tag_A REAL, zugkm_tag_B REAL,
 mio_jahr_ist REAL, mio_jahr_A REAL, mio_jahr_B REAL, delta_A_pct REAL, delta_B_pct REAL);''')
agg=collections.defaultdict(lambda:[0.0,0.0,0.0])
for r in cur.execute("SELECT ebene,zugkm_ist,zugkm_ziel,zugkm_ziel_b FROM ziel_linie"):
    agg[r[0]][0]+=r[1]; agg[r[0]][1]+=r[2]; agg[r[0]][2]+=r[3]
for k,label,km,ft,tz,rfz,zz,t1,t2,kl in srows:
    a=agg['Ebene 1 – ICE-Sprinter']; a[0]+=ft*km; a[1]+=9*2*km; a[2]+=zz*km
rows=[]
for eb in sorted(agg):
    i,A,B=agg[eb]
    rows.append((eb,round(i),round(A),round(B),round(i*365/1e6,1),round(A*365/1e6,1),round(B*365/1e6,1),
                 round(100*(A-i)/i,1),round(100*(B-i)/i,1)))
ti=sum(v[0] for v in agg.values()); tA=sum(v[1] for v in agg.values()); tB=sum(v[2] for v in agg.values())
rows.append(('GESAMT',round(ti),round(tA),round(tB),round(ti*365/1e6,1),round(tA*365/1e6,1),round(tB*365/1e6,1),
             round(100*(tA-ti)/ti,1),round(100*(tB-ti)/ti,1)))
cur.executemany("INSERT INTO betriebsleistung VALUES(?,?,?,?,?,?,?,?,?)", rows)
con.commit()
for r in rows: print(f"  {r[0]:26s} ist {r[1]:8,}  A {r[2]:8,} ({r[7]:+6.1f}%)  B {r[3]:8,} ({r[8]:+6.1f}%)  Zug-km/Tag")
print()
print("Ebene 2 – Taktveränderung (Top 12):")
for r in cur.execute("SELECT linie_key,bezeichnung,richtungsfahrten_ist,takt_ist,takt_ziel,richtungsfahrten_ziel FROM ziel_linie WHERE prio=2 ORDER BY richtungsfahrten_ist DESC LIMIT 12"):
    print(f"  {r[0]:10s} {r[1][:40]:40s} {r[2]:5.1f}/Ri {r[3]:9s} -> {r[4]:9s} {r[5]:3d}/Ri")
con.close()
