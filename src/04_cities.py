import sqlite3, os, re
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
try: cur.execute("ALTER TABLE station ADD COLUMN stadt TEXT")
except Exception: pass
try: cur.execute("ALTER TABLE station ADD COLUMN ist_fv_knoten INT DEFAULT 0")
except Exception: pass

GROUPS = {
 'Frankfurt(Oder)':['Frankfurt(Oder)'],
 'Berlin':      ['Berlin'],
 'Hamburg':     ['Hamburg'],
 'Frankfurt':   ['Frankfurt(Main)','Frankfurt(M) Flughafen'],
 'München':     ['München'],
 'Köln':        ['Köln'],
 'Düsseldorf':  ['Düsseldorf'],
 'Stuttgart':   ['Stuttgart'],
 'Nürnberg':    ['Nürnberg'],
 'Hannover':    ['Hannover'],
 'Leipzig':     ['Leipzig'],
 'Bremen':      ['Bremen Hbf','Bremen-'],
 'Dresden':     ['Dresden'],
 'Essen':       ['Essen Hbf'],
 'Dortmund':    ['Dortmund'],
 'Mannheim':    ['Mannheim'],
 'Karlsruhe':   ['Karlsruhe Hbf'],
 'Basel':       ['Basel'],
 'Wien':        ['Wien'],
 'Zürich':      ['Zürich','Zuerich'],
 'Paris':       ['Paris'],
 'Bruxelles':   ['Bruxelles'],
 'Amsterdam':   ['Amsterdam'],
 'Warszawa':    ['Warszawa'],
 'Praha':       ['Praha'],
 'Budapest':    ['Budapest'],
 'København':   ['Koebenhavn','København'],
}
rows=list(cur.execute("SELECT station_id,name FROM station"))
upd=[]
for sid,name in rows:
    city=None
    for g,pre in GROUPS.items():
        if any(name.startswith(p) for p in pre): city=g; break
    if city is None:
        city = re.split(r'\s+Hbf|\s+Hauptbahnhof|\(|,|\s+Süd|\s+Nord|\s+Messe', name)[0].strip()
    upd.append((city,sid))
cur.executemany("UPDATE station SET stadt=? WHERE station_id=?", upd)
con.commit()
print('Städte:', len(set(u[0] for u in upd)))
for r in cur.execute("SELECT stadt,COUNT(*) FROM station WHERE land_iso='DE' GROUP BY 1 HAVING COUNT(*)>1 ORDER BY 2 DESC"): print(' ',r)
con.close()
