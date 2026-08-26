import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, os, collections
con=sqlite3.connect(DB); cur=con.cursor()
st_city = dict(cur.execute("SELECT station_id,stadt FROM station"))
cur.execute("UPDATE trip_summary SET kategorie=produkt, sprinter_korridor=NULL")
try: cur.execute("ALTER TABLE trip_summary ADD COLUMN von_stadt TEXT")
except: pass
try: cur.execute("ALTER TABLE trip_summary ADD COLUMN nach_stadt TEXT")
except: pass
cur.execute("UPDATE trip_summary SET von_stadt=(SELECT stadt FROM station WHERE station_id=von_id), nach_stadt=(SELECT stadt FROM station WHERE station_id=nach_id)")
con.commit()

KORR = {
 'HH-FFM':  ('Hamburg/Hannover – Frankfurt', {frozenset(('Hamburg','Frankfurt')), frozenset(('Hannover','Frankfurt'))}),
 'HH-RHEIN':('Hamburg – Ruhr/Düsseldorf/Köln', {frozenset(('Hamburg',c)) for c in ('Essen','Duisburg','Düsseldorf','Köln','Dortmund')}),
 'B-KOELN': ('Berlin – Köln/Bonn', {frozenset(('Berlin','Köln')), frozenset(('Berlin','Bonn'))}),
 'B-MUC':   ('Berlin/Halle/Erfurt – Nürnberg/München', {frozenset((a,b)) for a in ('Berlin','Halle','Erfurt') for b in ('Nürnberg','München')}),
 'B-FFM':   ('Berlin/Halle/Erfurt – Frankfurt', {frozenset((a,'Frankfurt')) for a in ('Berlin','Halle','Erfurt')}),
 'FFM-PAR': ('Frankfurt/Mannheim/Karlsruhe – Paris', {frozenset((a,'Paris')) for a in ('Frankfurt','Mannheim','Karlsruhe','Stuttgart','Saarbrücken')}),
 'S-B':     ('Stuttgart – Nürnberg – Berlin', {frozenset(('Stuttgart','Berlin'))}),
}
rel2korr={}
for k,(lbl,S) in KORR.items():
    for fs in S: rel2korr[fs]=k

rows=list(cur.execute("""SELECT trip_id,von_stadt,nach_stadt,dauer_min,halte,verkehrstage,km_luftlinie
                         FROM trip_summary WHERE produkt='ICE'"""))
byrel=collections.defaultdict(list)
for r in rows: byrel[frozenset((r[1],r[2]))].append(r)

marks=[]; rep=[]
for fs,rs in byrel.items():
    k=rel2korr.get(fs)
    if not k: continue
    if len(fs)<2: continue
    km=max(r[6] for r in rs)
    if km < 200: continue
    tmin=min(r[3] for r in rs)
    fast=[r for r in rs if r[3] <= tmin*1.15]
    slow_exists = any(r[3] > tmin*1.25 for r in rs)
    if not slow_exists and len(rs)>3: continue
    for r in fast: marks.append((k, r[0]))
    rep.append((k, '–'.join(sorted(fs)), tmin, round(sum(r[5] for r in fast)/31,1), round(sum(r[5] for r in rs)/31,1)))
cur.executemany("UPDATE trip_summary SET kategorie='ICE-SPRINTER', sprinter_korridor=? WHERE trip_id=?", marks)
con.commit()
rep.sort(key=lambda x:(x[0],-x[3]))
print(f"{'Korr':9s} {'Relation':38s} {'best':>6s} {'Sprinter/Tag':>13s} {'alle ICE/Tag':>13s}")
for k,rel,t,f,a in rep: print(f"{k:9s} {rel:38s} {t:5d}m {f:13.1f} {a:13.1f}")
print()
agg=collections.defaultdict(float)
for k,rel,t,f,a in rep: agg[k]+=f
print("Sprinter/Tag je Korridor (beide Richtungen) vs. bahn.de-Angabe (x2):")
soll={'HH-FFM':7,'HH-RHEIN':6,'B-KOELN':8,'B-MUC':32,'B-FFM':14,'FFM-PAR':2,'S-B':2}
for k in KORR: print(f"  {k:9s} berechnet {agg.get(k,0):5.1f}   bahn.de ~{soll[k]}")
for r in cur.execute("SELECT kategorie,COUNT(*),ROUND(SUM(verkehrstage)/31.0,1) FROM trip_summary GROUP BY 1 ORDER BY 3 DESC"): print(' ',r)
con.close()
