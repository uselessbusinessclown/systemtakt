"""Rollt den Minutenplan zum vollständigen Tagesfahrplan aus (Szenario A, 5–23 Uhr)."""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sys; import fahrplan2 as F, sqlite3, collections, os
con=sqlite3.connect(DB); cur=con.cursor()
START, ENDE = 5*60, 23*60           # Abfahrtsfenster am Startbahnhof
TAKT={'30 min':30,'60 min':60,'120 min':120,'Einzelleistungen':120}
cur.executescript("""
DROP TABLE IF EXISTS fahrplan_zug; DROP TABLE IF EXISTS fahrplan_halt;
CREATE TABLE fahrplan_zug(zug_id INTEGER PRIMARY KEY, linie TEXT, gattung TEXT, nummer TEXT,
  produkt TEXT, kategorie TEXT, betreiber TEXT, richtung INT, von TEXT, nach TEXT,
  abfahrt INT, ankunft INT, dauer INT, halte INT, takt INT);
CREATE TABLE fahrplan_halt(zug_id INT, folge INT, station TEXT, an INT, ab INT, knoten INT);
""")
LIN=list(cur.execute("""SELECT z.linie_key,z.bezeichnung,z.takt_ziel,z.prio,z.ebene,l.laufweg,l.gattung,
  l.nummer,l.produkt,l.betreiber FROM ziel_linie z JOIN linie l ON l.linie_key=z.linie_key ORDER BY z.prio, z.linie_key"""))
zid=0; zrows=[]; hrows=[]; skipped=[]
for key,bez,takt,prio,ebene,lauf,g,nr,prod,op in LIN:
    path=[s for s in lauf.split(' > ')]
    if len(path)<2: continue
    step=TAKT.get(takt,120)
    for richtung,p in ((1,path),(2,list(reversed(path)))):
        plan=F.plan(key,p)
        if plan is None: skipped.append((key,richtung)); continue
        dep0=plan[0][2]
        if dep0 is None: skipped.append((key,richtung)); continue
        offs=[(x[1]-dep0 if x[1] is not None else None, x[2]-dep0 if x[2] is not None else None) for x in plan]
        base=dep0 % 60
        t=START + ((base - START) % step)
        while t<=ENDE:
            zid+=1
            arr_end=t+offs[-1][0]
            zrows.append((zid,key,g,nr,prod,'ICE-Sprinter' if prio==1 else ('ICE' if prio==2 else 'IC/EC'),
                          op,richtung,p[0],p[-1],t,arr_end,arr_end-t,len(p),step))
            for i,(st_,(a,d)) in enumerate(zip(p,offs)):
                hrows.append((zid,i,st_, None if a is None else t+a, None if d is None else t+d,
                              1 if st_ in F.PHI else 0))
            t+=step
cur.executemany("INSERT INTO fahrplan_zug VALUES(%s)"%','.join('?'*15), zrows)
cur.executemany("INSERT INTO fahrplan_halt VALUES(?,?,?,?,?,?)", hrows)
cur.executescript("CREATE INDEX ix_fh ON fahrplan_halt(station); CREATE INDEX ix_fh2 ON fahrplan_halt(zug_id);")
con.commit()
print('Züge',len(zrows),'Halte',len(hrows),'übersprungen',len(skipped))
if skipped: print('  ohne Plan:', skipped[:10])
for r in cur.execute("SELECT kategorie,COUNT(*),SUM(halte) FROM fahrplan_zug GROUP BY 1"): print('  ',r)
print('Ø Halte je Bahnhof/Tag:', round(len(hrows)/len(set(h[2] for h in hrows)),1))
con.close()
