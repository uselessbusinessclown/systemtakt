import sqlite3, os, collections
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
cur.execute("ALTER TABLE trip_summary ADD COLUMN kategorie TEXT")
cur.execute("ALTER TABLE trip_summary ADD COLUMN sprinter_korridor TEXT")

# offizielle ICE-Sprinter-Relationen (bahn.de, Stand Fahrplan 2026)
KORR = {
 'HH-FFM':   (('Hamburg','Hannover'), ('Frankfurt(Main)','Frankfurt(M) Flughafen')),
 'HH-RUHR':  (('Hamburg',), ('Essen','Duisburg','Düsseldorf','Köln')),
 'B-KOELN':  (('Berlin',), ('Köln','Bonn')),
 'B-MUC':    (('Berlin','Halle(Saale)','Erfurt'), ('Nürnberg','München')),
 'B-FFM':    (('Berlin','Halle(Saale)','Erfurt'), ('Frankfurt(Main)','Frankfurt(M) Flughafen')),
 'FFM-PARIS':(('Frankfurt(Main)','Mannheim','Karlsruhe','Frankfurt(M) Flughafen'), ('Paris',)),
 'S-B':      (('Stuttgart',), ('Berlin',)),
}
def match(a,b):
    for k,(A,B) in KORR.items():
        if (any(a.startswith(x) for x in A) and any(b.startswith(x) for x in B)) or \
           (any(b.startswith(x) for x in A) and any(a.startswith(x) for x in B)):
            return k
    return None

rows=list(cur.execute("SELECT trip_id,produkt,von,nach,km_luftlinie,halt_je_100km,vschnitt_kmh,dauer_min,halte FROM trip_summary"))
upd=[]
for tid,prod,von,nach,km,hj,v,dur,halte in rows:
    kat=prod
    korr=None
    if prod=='ICE':
        struktur = (km or 0)>=200 and hj is not None and hj<=0.75 and (v or 0)>=95
        korr = match(von,nach)
        if struktur and korr: kat='ICE-SPRINTER'
        elif struktur:        kat='ICE-SCHNELL'   # sprinterartig, nicht offiziell vermarktet
    upd.append((kat,korr,tid))
cur.executemany("UPDATE trip_summary SET kategorie=?, sprinter_korridor=? WHERE trip_id=?", upd)
con.commit()

print("Fahrten pro Kategorie (Fahrten je Verkehrstag-Summe / Monat):")
for r in cur.execute("""SELECT kategorie, COUNT(*) fahrplantrassen, SUM(verkehrstage) fahrten_monat,
   ROUND(SUM(verkehrstage)/31.0,1) je_tag FROM trip_summary GROUP BY kategorie ORDER BY 3 DESC"""): print('  ',r)
print("\nSprinter je Korridor (Fahrten/Tag, beide Richtungen):")
for r in cur.execute("""SELECT sprinter_korridor, ROUND(SUM(verkehrstage)/31.0,1), COUNT(*) FROM trip_summary
   WHERE kategorie='ICE-SPRINTER' GROUP BY 1 ORDER BY 2 DESC"""): print('  ',r)
print("\nICE-SCHNELL (sprinterartig, ohne offizielle Vermarktung) Top-Relationen:")
for r in cur.execute("""SELECT von,nach,ROUND(SUM(verkehrstage)/31.0,1) t,ROUND(AVG(dauer_min)) d,ROUND(AVG(halte),1)
   FROM trip_summary WHERE kategorie='ICE-SCHNELL' GROUP BY von,nach ORDER BY t DESC LIMIT 15"""): print('  ',r)
con.close()
