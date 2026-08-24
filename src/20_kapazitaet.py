
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, os, collections, math
con=sqlite3.connect(DB); cur=con.cursor()

# ---- Ist-Takt neu bewerten (Zwei-Lagen-Takt erkennen)
cur.execute("ALTER TABLE ist_takt ADD COLUMN top2_anteil REAL") if 'top2_anteil' not in [d[1] for d in cur.execute("PRAGMA table_info(ist_takt)")] else None
rows=list(cur.execute("SELECT rowid,minuten,abfahrten_tag,anteil_haeufigste FROM ist_takt"))
upd=[]
for rid,minuten,tot,top1 in rows:
    parts=[p for p in minuten.split(', ') if p]
    vals=[float(p.split('(')[1].rstrip(')')) for p in parts]
    top2=(sum(vals[:2])/tot) if tot else 0
    bew = "60-min-Takt stabil" if top1>=0.6 else ("Zwei-Lagen-Takt (120 min)" if top2>=0.7 else "kein systematischer Takt")
    upd.append((round(top2,2),bew,rid))
cur.executemany("UPDATE ist_takt SET top2_anteil=?, takt_bewertung=? WHERE rowid=?", upd)

# ---- Knotenbelastung: Züge im Knotenfenster je Stunde
cur.executescript("""DROP TABLE IF EXISTS knoten_kapazitaet;
CREATE TABLE knoten_kapazitaet(knoten TEXT PRIMARY KEY, knotenzeit TEXT, grad INT,
 zuege_tag REAL, zuege_hvz_h REAL, zuege_je_knotenfenster REAL, gleise_bedarf INT, bewertung TEXT);""")
PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
KZ =dict(cur.execute("SELECT name,knotenzeit FROM itf_knotenzeit"))
deg=dict(cur.execute("SELECT name,grad FROM itf_knotenzeit"))
halte=dict(cur.execute("SELECT name,halte_tag FROM bahnhof_bedienung"))
rows=[]
for k,phi in PHI.items():
    ht=halte.get(k,0)
    h_hvz = ht/17*1.35                 # 17 Betriebsstunden, HVZ-Faktor
    per_window = h_hvz/2               # zwei Knotenfenster je Stunde
    # Gleisbedarf: Zug belegt Gleis ~ 8 min; Fenster 6 min -> praktisch 1 Gleis je Zug im Fenster
    gl = max(2, math.ceil(per_window*1.15))
    bew = "unkritisch" if gl<=6 else ("anspruchsvoll" if gl<=10 else "Engpass – Ausbau/Entflechtung nötig")
    rows.append((k,KZ[k],deg[k],round(ht,1),round(h_hvz,1),round(per_window,1),gl,bew))
cur.executemany("INSERT INTO knoten_kapazitaet VALUES(?,?,?,?,?,?,?,?)", rows)

# ---- Sprinter: Überholbedarf
cur.executescript("""DROP TABLE IF EXISTS sprinter_ueberholung;
CREATE TABLE sprinter_ueberholung(korridor TEXT, relation TEXT, t_sprinter INT, t_ice INT,
 zeitgewinn INT, uebersprungene_knoten TEXT, ueberholungen_30min INT, ueberholungen_60min INT);""")
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))
nm=dict(cur.execute("SELECT station_id,name FROM station"))
seq=collections.defaultdict(list)
for tid,sq,sid in cur.execute("SELECT trip_id,stop_seq,stop_id FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append(nm[s2st[sid]])
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,sprinter_korridor,von_stadt,nach_stadt,dauer_min FROM trip_summary")}
KORRNAME={'SPR-1':'Hamburg/Hannover – Frankfurt','SPR-2':'Hamburg – Ruhr/Köln','SPR-3':'Berlin – Köln/Bonn',
 'SPR-4':'Berlin/Halle/Erfurt – Nürnberg/München','SPR-5':'Berlin/Halle/Erfurt – Frankfurt',
 'SPR-6':'Frankfurt/Mannheim/Karlsruhe – Paris','SPR-7':'Stuttgart – Nürnberg – Berlin'}
best=collections.defaultdict(lambda:(10**9,None,None))
for tid,(kat,korr,vs,ns,dur) in TS.items():
    if kat!='ICE-SPRINTER': continue
    key=(korr, tuple(sorted((vs,ns))))
    if dur<best[key][0]: best[key]=(dur,tid,seq[tid])
srows=[]
for (korr,rel),(dur,tid,path) in best.items():
    # langsamste vergleichbare ICE-Fahrt derselben Stadtrelation
    alt=[TS[t][4] for t in TS if TS[t][0]=='ICE' and tuple(sorted((TS[t][2],TS[t][3])))==rel]
    if not alt: continue
    t_ice=int(sorted(alt)[len(alt)//2])
    gew=t_ice-dur
    skipped=[k for k in PHI if k not in path and any(k in seq[t] for t in TS if TS[t][0]=='ICE' and tuple(sorted((TS[t][2],TS[t][3])))==rel)]
    srows.append((KORRNAME.get(korr,korr),' – '.join(rel),dur,t_ice,gew,', '.join(sorted(skipped)[:12]),
                  max(0,gew//30), max(0,gew//60)))
srows.sort(key=lambda r:-r[4])
cur.executemany("INSERT INTO sprinter_ueberholung VALUES(?,?,?,?,?,?,?,?)", srows)
con.commit()
print("Ist-Taktqualität neu:")
for r in cur.execute("SELECT takt_bewertung,COUNT(*),ROUND(SUM(abfahrten_tag),1) FROM ist_takt GROUP BY 1 ORDER BY 3 DESC"): print('  ',r)
print("\nKnotenkapazität (Top 15):")
for r in cur.execute("SELECT knoten,knotenzeit,zuege_je_knotenfenster,gleise_bedarf,bewertung FROM knoten_kapazitaet ORDER BY zuege_je_knotenfenster DESC LIMIT 15"): print('  ',r)
print("\nSprinter-Überholbedarf:")
for r in cur.execute("SELECT relation,t_sprinter,t_ice,zeitgewinn,ueberholungen_30min FROM sprinter_ueberholung ORDER BY zeitgewinn DESC LIMIT 12"): print('  ',r)
con.close()
