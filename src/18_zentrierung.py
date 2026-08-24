import sqlite3, json, os
con=sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
Z=json.load(open('/root/bahn/zentrierung_exakt.json'))
C=json.load(open('/root/bahn/zentralitaet.json'))
cur.executescript("""DROP TABLE IF EXISTS zentralitaet; DROP TABLE IF EXISTS zentrierung;
CREATE TABLE zentralitaet(bahnhof TEXT PRIMARY KEY, grad INT, gewicht REAL, halte_tag REAL,
  zwischenzentralitaet REAL, mittlere_fahrzeit_zum_netz REAL, rang_zentralitaet INT, rang_erreichbarkeit INT);
CREATE TABLE zentrierung(bahnhof TEXT PRIMARY KEY, kanten INT, gewicht REAL,
  reserve_basis REAL, reserve_zentriert REAL, gewinn_knoten REAL,
  sollband_basis REAL, sollband_zentriert REAL,
  netz_reserve_basis REAL, netz_reserve_zentriert REAL, netz_kosten_effekt REAL, optimal TEXT, bewertung TEXT);""")
rows=sorted(C.items(), key=lambda kv:-kv[1]['bc'])
rb={k:i+1 for i,(k,v) in enumerate(rows)}
ra={k:i+1 for i,(k,v) in enumerate(sorted(C.items(), key=lambda kv:kv[1]['acc']))}
cur.executemany("INSERT INTO zentralitaet VALUES(?,?,?,?,?,?,?,?)",
  [(k,v['grad'],v['gewicht'],v['halte'],v['bc'],v['acc'],rb[k],ra[k]) for k,v in C.items()])
base=Z['basis']; nb=base['reserve_pct']
zr=[]
for n,d in Z['zentriert'].items():
    b=base['knoten'][n]; g=round(b['reserve']-d['knoten']['reserve'],2)
    eff=round(d['netz_reserve']-nb,2)
    bew=('Zentrierung lohnt: Knoten wird deutlich besser, das Netz nicht schlechter' if g>=1.0 and eff<=0.05 else
         ('Zentrierung lohnt eingeschränkt: Knotengewinn erkauft mit Nachteilen im Netz' if g>=1.0 else
          ('kein Knotengewinn – Zentrierung bringt nichts' if g<0.5 else 'geringer Effekt')))
    zr.append((n,b['kanten'],b['gewicht'],b['reserve'],d['knoten']['reserve'],g,
               b['sollband'],d['knoten']['sollband'],nb,d['netz_reserve'],eff,
               'ja' if d.get('optimal') else 'Zeitlimit',bew))
zr.sort(key=lambda r:-r[5])
cur.executemany("INSERT INTO zentrierung VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", zr)
con.commit()
print(f"{'Bahnhof':28s} {'Reserve Basis':>13s} {'zentriert':>10s} {'Gewinn':>7s} {'Netz-Effekt':>12s}  Bewertung")
for r in zr: print(f"{r[0][:28]:28s} {r[3]:12.2f}% {r[4]:9.2f}% {r[5]:+6.2f} {r[10]:+11.2f}  {r[12]}")
con.close()
