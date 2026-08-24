import sqlite3, os
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
KORR = {
 'HH-FFM':   ('Hamburg/Hannover – Frankfurt (+Flughafen)', ('Hamburg','Hannover'), ('Frankfurt(Main)','Frankfurt(M) Flughafen')),
 'HH-RUHR':  ('Hamburg – Ruhr/Düsseldorf/Köln',            ('Hamburg',), ('Essen','Duisburg','Düsseldorf','Köln')),
 'B-KOELN':  ('Berlin – Köln/Bonn',                        ('Berlin',), ('Köln','Bonn')),
 'B-MUC':    ('Berlin/Halle/Erfurt – Nürnberg/München',    ('Berlin','Halle(Saale)','Erfurt'), ('Nürnberg','München')),
 'B-FFM':    ('Berlin/Halle/Erfurt – Frankfurt',           ('Berlin','Halle(Saale)','Erfurt'), ('Frankfurt(Main)','Frankfurt(M) Flughafen')),
 'FFM-PAR':  ('Frankfurt/Mannheim/Karlsruhe – Paris',      ('Frankfurt(Main)','Mannheim','Karlsruhe','Frankfurt(M) Flughafen'), ('Paris',)),
 'S-B':      ('Stuttgart – Nürnberg – Berlin',             ('Stuttgart',), ('Berlin',)),
}
cur.execute("UPDATE trip_summary SET kategorie=produkt, sprinter_korridor=NULL")
rows=list(cur.execute("SELECT trip_id,von,nach,dauer_min,halte,verkehrstage FROM trip_summary WHERE produkt='ICE'"))
def m(a,b,A,B):
    return (any(a.startswith(x) for x in A) and any(b.startswith(x) for x in B)) or \
           (any(b.startswith(x) for x in A) and any(a.startswith(x) for x in B))
report=[]
for k,(label,A,B) in KORR.items():
    sel=[r for r in rows if m(r[1],r[2],A,B)]
    if not sel: continue
    tmin=min(r[3] for r in sel); hmin=min(r[4] for r in sel)
    fast=[r for r in sel if r[3] <= tmin*1.07 and r[4] <= hmin+3]
    cur.executemany("UPDATE trip_summary SET kategorie='ICE-SPRINTER', sprinter_korridor=? WHERE trip_id=?",
                    [(k,r[0]) for r in fast])
    report.append((k,label,tmin,hmin,round(sum(r[5] for r in fast)/31,1),len(fast)))
con.commit()
print(f"{'Korridor':10s} {'schnellste':>10s} {'Hp':>3s} {'Fahrten/Tag':>12s} {'Trassen':>8s}  Bezeichnung")
for k,label,tmin,hmin,perday,n in report:
    print(f"{k:10s} {tmin:8d}min {hmin:3d} {perday:12.1f} {n:8d}  {label}")
print()
for r in cur.execute("SELECT kategorie,COUNT(*),ROUND(SUM(verkehrstage)/31.0,1) FROM trip_summary GROUP BY 1 ORDER BY 3 DESC"): print(' ',r)
con.close()
