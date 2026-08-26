import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, os, collections
con=sqlite3.connect(DB); cur=con.cursor()
cur.execute("UPDATE trip_summary SET kategorie=produkt, sprinter_korridor=NULL")

# Korridore und offizielle Angebotsdichte je Richtung (bahn.de, Fahrplan 2026)
KORR = {
 'SPR-1': ('Hamburg/Hannover – Frankfurt (+Flughafen)', 4,
           {frozenset(('Hamburg','Frankfurt')), frozenset(('Hannover','Frankfurt'))}),
 'SPR-2': ('Hamburg – Essen/Duisburg/Düsseldorf/Köln', 3,
           {frozenset(('Hamburg',c)) for c in ('Essen','Duisburg','Düsseldorf','Köln')}),
 'SPR-3': ('Berlin – Köln/Bonn', 4,
           {frozenset(('Berlin','Köln')), frozenset(('Berlin','Bonn'))}),
 'SPR-4': ('Berlin/Halle/Erfurt – Nürnberg/München', 16,
           {frozenset((a,b)) for a in ('Berlin','Halle','Erfurt') for b in ('Nürnberg','München')}),
 'SPR-5': ('Berlin/Halle/Erfurt – Frankfurt (+Flughafen)', 7,
           {frozenset((a,'Frankfurt')) for a in ('Berlin','Halle','Erfurt')}),
 'SPR-6': ('Frankfurt/Mannheim/Karlsruhe – Paris', 1,
           {frozenset((a,'Paris')) for a in ('Frankfurt','Mannheim','Karlsruhe','Saarbrücken','Stuttgart')}),
 'SPR-7': ('Stuttgart – Nürnberg – Berlin', 1, {frozenset(('Stuttgart','Berlin'))}),
}
rel2k={}
for k,(lbl,n,S) in KORR.items():
    for fs in S: rel2k[fs]=k

rows=list(cur.execute("""SELECT trip_id,von_stadt,nach_stadt,dauer_min,halte,verkehrstage,km_luftlinie
                         FROM trip_summary WHERE produkt='ICE'"""))
bucket=collections.defaultdict(list)
for r in rows:
    if r[1]==r[2]: continue
    k=rel2k.get(frozenset((r[1],r[2])))
    if k and (r[6] or 0)>=180: bucket[(k, r[1], r[2])].append(r)   # je Richtung

# Zielzahl je Richtung auf die Richtungspaare des Korridors verteilen: greedy nach Fahrzeit
marks=[]; rep=collections.defaultdict(float)
korr_dirs=collections.defaultdict(list)
for (k,a,b),rs in bucket.items(): korr_dirs[(k, tuple(sorted((a,b))) )].append(((a,b),rs))
# pro Korridor & Richtung: nimm die schnellsten Trassen bis Zielfrequenz erreicht
per_dir=collections.defaultdict(list)
for (k,a,b),rs in bucket.items(): per_dir[(k,(a,b))]=rs
# Zielfrequenz pro Korridor und Richtung gilt für den Korridor insgesamt -> pro Richtungssinn aggregieren
korr_richtung=collections.defaultdict(list)
for (k,(a,b)),rs in per_dir.items(): korr_richtung[(k,(a,b))]=rs
for k,(lbl,ziel,S) in KORR.items():
    # zwei "Richtungssinne": wir gruppieren alle Trassen des Korridors und teilen nach (von,nach)
    alle=[( (a,b), r) for (kk,(a,b)),rs in per_dir.items() if kk==k for r in rs]
    dirs=collections.defaultdict(list)
    for (a,b),r in alle: dirs[(a,b)].append(r)
    # jede Richtung eines Städtepaares ist ein eigener Richtungssinn; Zielwert gilt je Sinn des Hauptpaares
    # -> wir behandeln jede (von,nach)-Kombination als Richtung und verteilen ziel proportional
    # Vereinfachung: sortiere ALLE Trassen des Korridors nach Fahrzeit und nimm bis 2*ziel Fahrten/Tag
    flat=sorted([r for _,r in alle], key=lambda r:r[3])
    acc=0.0
    for r in flat:
        if acc >= 2*ziel: break
        marks.append((k,r[0])); acc += r[5]/31
    rep[k]=acc
cur.executemany("UPDATE trip_summary SET kategorie='ICE-SPRINTER', sprinter_korridor=? WHERE trip_id=?", marks)
con.commit()
print(f"{'Korr':6s} {'Fahrten/Tag':>11s} {'Soll(bahn.de)':>13s}  Korridor")
for k,(lbl,n,S) in KORR.items(): print(f"{k:6s} {rep[k]:11.1f} {2*n:13d}  {lbl}")
print()
for r in cur.execute("SELECT kategorie,COUNT(*) trassen,ROUND(SUM(verkehrstage)/31.0,1) fahrten_tag FROM trip_summary GROUP BY 1 ORDER BY 3 DESC"): print(' ',r)
print()
print("Sprinter-Trassen: schnellste je Korridor")
for r in cur.execute("""SELECT sprinter_korridor,von,nach,dauer_min,halte,ROUND(verkehrstage/31.0,2)
 FROM trip_summary WHERE kategorie='ICE-SPRINTER' GROUP BY sprinter_korridor HAVING MIN(dauer_min) ORDER BY 1"""): print('  ',r)
con.close()
