import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, collections, json, os, math
con=sqlite3.connect(DB); cur=con.cursor()
HBF='Frankfurt(Main)Hbf'; FBF='Frankfurt(M) Flughafen Fernbf'; RBF='Frankfurt(M) Flughafen Regionalbf'
AP={FBF,RBF}; WENDE=25
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station")); nm=dict(cur.execute("SELECT station_id,name FROM station"))
seq=collections.defaultdict(list)
for tid,sq,sid,arr,dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((nm[s2st[sid]],arr,dep))
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,verkehrstage,gattung,linie,betreiber FROM trip_summary")}

cur.executescript("""
DROP TABLE IF EXISTS ffm_belegung; DROP TABLE IF EXISTS ffm_varianten; DROP TABLE IF EXISTS ffm_linien;
CREATE TABLE ffm_belegung(bahnhof TEXT, zugart TEXT, kategorie TEXT, fahrten_tag REAL,
  gleisminuten_tag REAL, anteil_pct REAL);
CREATE TABLE ffm_varianten(variante TEXT PRIMARY KEY, beschreibung TEXT, knoten INT, kanten INT,
  gewicht REAL, kosten REAL, kosten_je_gewicht REAL, beschl_kanten INT, sollband_pct REAL,
  mittlere_reserve_pct REAL, hbf_knotenminute TEXT, flughafen_knotenminute TEXT,
  hbf_gleisminuten REAL, flughafen_gleisminuten REAL, flughafen_auslastung_pct REAL, bewertung TEXT);
CREATE TABLE ffm_linien(linie TEXT, fahrten_tag REAL, haelt_hbf INT, haelt_flughafen INT, verlust TEXT);
""")
def belegung(target):
    out=collections.defaultdict(lambda:[0.0,0.0])
    for tid,p in seq.items():
        kat,vt,g,l,op=TS[tid]; vt=vt/31
        names=[x[0] for x in p]
        idx=[i for i,n in enumerate(names) if n in target]
        if not idx: continue
        i=idx[0]
        if i==0 or i==len(names)-1: art='wendend/endend'; m=WENDE
        else:
            a,d=p[i][1],p[i][2]; m=((d-a)//60) if (a is not None and d is not None) else 4; art='durchgehend'
        key=(art, 'ICE-Sprinter' if kat=='ICE-SPRINTER' else ('ICE' if kat=='ICE' else 'IC/EC'))
        out[key][0]+=vt; out[key][1]+=vt*m
    return out
rows=[]
for label,target in (('Frankfurt(Main)Hbf',{HBF}),('Flughafen Fern-/Regionalbf',AP)):
    b=belegung(target); tot=sum(v[1] for v in b.values())
    for (art,kat),v in sorted(b.items()):
        rows.append((label,art,kat,round(v[0],1),round(v[1]),round(100*v[1]/tot,1)))
    rows.append((label,'SUMME','alle',round(sum(v[0] for v in b.values()),1),round(tot),100.0))
cur.executemany("INSERT INTO ffm_belegung VALUES(?,?,?,?,?,?)", rows)

gh=sum(r[4] for r in rows if r[0]=='Frankfurt(Main)Hbf' and r[1]=='SUMME')
ga=sum(r[4] for r in rows if r[0]!='Frankfurt(Main)Hbf' and r[1]=='SUMME')
spr_gm=sum(r[4] for r in rows if r[0]=='Frankfurt(Main)Hbf' and r[2]=='ICE-Sprinter')
wend_gm=sum(r[4] for r in rows if r[0]=='Frankfurt(Main)Hbf' and r[1]=='wendend/endend')
wend_f =sum(r[3] for r in rows if r[0]=='Frankfurt(Main)Hbf' and r[1]=='wendend/endend')
CAP4=4*18*60
V=json.load(open(os.path.join(DATA, 'varianten.json')))
V['V0']['kosten']=13934.8
vr=[
 ('Status quo','Frankfurt Hbf ist Vollknoten, der Flughafen-Fernbahnhof ein Durchgangshalt',
  V['V0']['kanten'],V['V0']['gewicht'],V['V0']['kosten'],V['V0']['beschl_kanten'],
  V['V0']['anteil_sollband_pct'],V['V0']['mittlere_reserve_pct'],':16 / :46','frei (Durchfahrt)',
  gh,ga,round(100*ga/CAP4,0),'Referenz – beste Taktpassung, aber Hbf bleibt der Engpass'),
 ('Variante B','Sprinter halten am Flughafen, übriger ICE am Hbf; beide Bahnhöfe taktgebunden',
  V['V1']['kanten'],V['V1']['gewicht'],V['V1']['kosten'],V['V1']['beschl_kanten'],
  V['V1']['anteil_sollband_pct'],V['V1']['mittlere_reserve_pct'],':18 / :48',':00 / :30',
  gh-spr_gm,ga+spr_gm,round(100*(ga+spr_gm)/CAP4,0),
  'Taktqualität 43 % schlechter; Hbf nur um 10 % entlastet'),
 ('Variante A','Gesamter Fernverkehr an den Flughafen-Fernbahnhof, Hbf nur noch Nahverkehr',
  V['V2']['kanten'],V['V2']['gewicht'],V['V2']['kosten'],V['V2']['beschl_kanten'],
  V['V2']['anteil_sollband_pct'],V['V2']['mittlere_reserve_pct'],'entfällt',':12 / :42',
  0,gh+ga,round(100*(gh+ga)/CAP4,0),
  'Taktqualität 17 % schlechter; Flughafen mit 4 Gleisen rechnerisch über 100 % ausgelastet'),
 ('Variante C','Fernbahntunnel: Hbf wird Durchgangsbahnhof, wendende Züge werden durchgebunden',
  V['V0']['kanten'],V['V0']['gewicht'],V['V0']['kosten'],V['V0']['beschl_kanten'],
  V['V0']['anteil_sollband_pct'],V['V0']['mittlere_reserve_pct'],':16 / :46','frei (Durchfahrt)',
  gh-(wend_gm-wend_f*6),ga,round(100*ga/CAP4,0),
  'Taktqualität unverändert gut; Hbf um 59 % entlastet'),
]
cur.executemany("INSERT INTO ffm_varianten VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
  [(v[0],v[1],64 if v[0]!='Variante B' else 65,v[2],v[3],v[4],round(v[4]/v[3],2),v[5],v[6],v[7],v[8],v[9],
    round(v[10]),round(v[11]),v[12],v[13]) for v in vr])

lh=collections.Counter(); lf=collections.Counter()
for tid,p in seq.items():
    kat,vt,g,l,op=TS[tid]; vt=vt/31; names=[x[0] for x in p]
    key=f"{g} {l or '('+op+')'}"
    if HBF in names: lh[key]+=vt
    if any(x in names for x in AP): lf[key]+=vt
allk=set(lh)|set(lf); lr=[]
for k in sorted(allk,key=lambda k:-(lh[k]+lf[k])):
    h,f=lh.get(k,0),lf.get(k,0)
    verl=('nur Hbf – am Flughafen nicht erreichbar' if h>=0.3 and f<0.3 else
          ('nur Flughafen – vom Hbf nicht erreichbar' if f>=0.3 and h<0.3 else 'beide Bahnhöfe'))
    lr.append((k,round(h+f,1),1 if h>=0.3 else 0,1 if f>=0.3 else 0,verl))
cur.executemany("INSERT INTO ffm_linien VALUES(?,?,?,?,?)", lr)
con.commit()
print("Belegung:")
for r in cur.execute("SELECT * FROM ffm_belegung"): print('  ',r)
print("\nVarianten:")
for r in cur.execute("SELECT variante,kosten_je_gewicht,beschl_kanten,hbf_gleisminuten,flughafen_gleisminuten,flughafen_auslastung_pct,bewertung FROM ffm_varianten"): print('  ',r)
con.close()
