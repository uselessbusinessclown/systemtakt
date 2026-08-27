import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, json, os, collections
con=sqlite3.connect(DB); cur=con.cursor()
r=json.load(open(os.path.join(DATA, 'pesp_N1.json')))
PHI=r['phi']; off=PHI['Berlin Hbf']; PHI={k:(v-off)%30 for k,v in PHI.items()}
name2id=dict(cur.execute("SELECT name,station_id FROM station"))
deg=collections.Counter(); gw=collections.Counter()
for x in r['kanten']: deg[x[0]]+=1; deg[x[1]]+=1; gw[x[0]]+=x[7]; gw[x[1]]+=x[7]
cur.execute("DELETE FROM itf_knotenzeit")
cur.executemany("INSERT INTO itf_knotenzeit VALUES(?,?,?,?,?,?,?,?)",
  [(name2id[n],n,m,f":{m:02d} / :{(m+30)%60:02d}",f":{(m-3)%60:02d} / :{(m+27)%60:02d}",
    f":{(m+3)%60:02d} / :{(m+33)%60:02d}",round(gw[n],1),deg[n]) for n,m in PHI.items()])
cur.execute("DELETE FROM itf_ergebnis")
res=[]
for a,b,tmin,p15,ts,d,rr,w,fs,fi,fc in r['kanten']:
    mass=("taktkonform" if rr<=14 else f"Überschussreserve {rr:.0f} % – Zusatzhalt oder Knotenabstufung")
    res.append((a,b,tmin,p15,ts,d,rr,mass,w,fs,fi,fc))
cur.executemany("INSERT INTO itf_ergebnis VALUES(%s)"%','.join('?'*12), res)
# Variantenvergleich
nf=json.load(open(os.path.join(DATA, 'neubaufrei.json')))
cur.executescript("""DROP TABLE IF EXISTS takt_varianten;
CREATE TABLE takt_varianten(variante TEXT PRIMARY KEY, beschreibung TEXT, verfahren TEXT,
 knotenraster TEXT, beschleunigung_erlaubt TEXT, kanten_mit_beschleunigung INT,
 kosten REAL, kosten_je_gewicht REAL, sollband_pct REAL, mittlere_reserve_pct REAL,
 max_zuschlag_min INT, bewertung TEXT);""")
rows=[
 ('T1 – neubaufrei','Keine Kante darf schneller werden als heute; der Takt entsteht allein aus Fahrzeitzuschlägen',
  'exakt (MILP, HiGHS, Optimalität bewiesen)','frei, 1-Minuten-Schritte','nein',0,
  r['kosten'],r['kosten_je_gewicht'],r['sollband_pct'],r['reserve_pct'],r['max_zuschlag'],
  'Empfohlen. Erreicht das schweizerische Reserveziel von 7 % und braucht keinen Streckenausbau.'),
 ('T2 – Raster :00/:15','Alle Knoten liegen entweder auf :00/:30 oder auf :15/:45 (Voll-/Halbknotenschema)',
  'heuristisch','nur :00 und :15','nein',0,
  nf['N2']['kosten'],nf['N2']['kosten_je_gewicht'],nf['N2']['sollband_pct'],nf['N2']['reserve_pct'],
  nf['N2']['max_zuschlag'],'Nicht darstellbar. Mittlere Reserve 36 % – der Fahrplan würde ein Drittel Zeit verschenken.'),
 ('T3 – 5-Minuten-Raster','Knotenminuten nur in Fünferschritten',
  'heuristisch','0,5,10,15,20,25','nein',0,
  nf['N3']['kosten'],nf['N3']['kosten_je_gewicht'],nf['N3']['sollband_pct'],nf['N3']['reserve_pct'],
  nf['N3']['max_zuschlag'],'Nicht empfehlenswert. Mittlere Reserve 15,5 % – doppelt so viel wie nötig.'),
]
cur.executemany("INSERT INTO takt_varianten VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)
con.commit()
print('Knoten',len(PHI),'Kanten',len(res))
for x in cur.execute("SELECT variante,kosten_je_gewicht,sollband_pct,mittlere_reserve_pct FROM takt_varianten"): print('  ',x)
con.close()
