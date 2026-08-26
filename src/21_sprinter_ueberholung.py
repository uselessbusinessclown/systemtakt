import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, collections, os
con=sqlite3.connect(DB); cur=con.cursor()
PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
TSOLL={}
for a,b,ts in cur.execute("SELECT a,b,t_soll FROM itf_ergebnis"): TSOLL[(a,b)]=ts; TSOLL[(b,a)]=ts
s2st=dict(cur.execute("SELECT stop_id,station_id FROM stop_station")); nm=dict(cur.execute("SELECT station_id,name FROM station"))
seq=collections.defaultdict(list)
for tid,sq,sid in cur.execute("SELECT trip_id,stop_seq,stop_id FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append(nm[s2st[sid]])
TS={r[0]:r[1:] for r in cur.execute("SELECT trip_id,kategorie,sprinter_korridor,von_stadt,nach_stadt,dauer_min,verkehrstage FROM trip_summary")}

# ---------- Sprinter-Soll: Summe der Soll-Kantenzeiten entlang des Laufwegs ----------
KN={'SPR-1':'Hamburg – Hannover – Frankfurt','SPR-2':'Hamburg – Ruhr – Köln','SPR-3':'Berlin – Köln/Bonn',
 'SPR-4':'Berlin – Erfurt – Nürnberg – München','SPR-5':'Berlin – Erfurt – Frankfurt',
 'SPR-6':'Saarbrücken – Paris','SPR-7':'Stuttgart – Nürnberg – Berlin'}
best={}
for tid,(kat,korr,vs,ns,dur,vt) in TS.items():
    if kat!='ICE-SPRINTER' or not dur: continue
    if korr not in best or dur<best[korr][0]: best[korr]=(dur,tid)
cur.execute("DELETE FROM sprinter_soll"); rows=[]
for k,(dur,tid) in sorted(best.items()):
    path=[x for x in seq[tid] if x in PHI]
    if len(path)<2: continue
    tot=0; ok=True; missing=[]
    for i in range(len(path)-1):
        t=TSOLL.get((path[i],path[i+1]))
        if t is None: ok=False; missing.append(path[i]+'/'+path[i+1]); continue
        tot+=t
        if i<len(path)-2: tot+=6
    a,b=path[0],path[-1]
    d=tot-dur
    bew=("taktkonform ohne Eingriff" if abs(d)<=1 else
         (f"{-d} min schneller als heute – Beschleunigung nötig" if d<0 else
          f"{d} min langsamer als heute ({100*d/dur:.0f} % Systemzuschlag)"))
    if not ok: bew="Laufweg nicht vollständig im Knotennetz: "+', '.join(missing[:2])
    rows.append((k,KN.get(k,k),a,PHI[a],b,PHI[b],f":{(PHI[a]+3)%60:02d}",f":{(PHI[b]-3)%60:02d}",dur,tot,d,bew))
cur.executemany("INSERT INTO sprinter_soll VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)

# ---------- Sprinter-Überholbedarf: nur streckengleiche Vergleiche ----------
byrel=collections.defaultdict(list)
for tid,(kat,korr,vs,ns,dur,vt) in TS.items():
    if dur and vs and ns: byrel[tuple(sorted((vs,ns)))].append((tid,kat,korr,dur))
cur.execute("DELETE FROM sprinter_ueberholung"); ur=[]
for rel,lst in byrel.items():
    sprs=[x for x in lst if x[1]=='ICE-SPRINTER']; ices=[x for x in lst if x[1]=='ICE']
    if not sprs or not ices: continue
    s=min(sprs,key=lambda x:x[3]); sp=set(seq[s[0]])
    cands=[x for x in ices if sp.issubset(set(seq[x[0]]))]
    if not cands: continue
    i=min(cands,key=lambda x:x[3]); gew=i[3]-s[3]
    ur.append((KN.get(s[2],s[2]),' – '.join(rel),s[3],i[3],gew,
               ', '.join(sorted((set(seq[i[0]])-sp)&set(PHI))[:14]), max(0,gew//30), max(0,gew//60)))
ur.sort(key=lambda r:-r[4])
cur.executemany("INSERT INTO sprinter_ueberholung VALUES(?,?,?,?,?,?,?,?)", ur)
con.commit()
print("=== Sprinter Soll-Fahrzeiten (Summe der Soll-Kantenzeiten)")
for r in rows: print(f"  {r[0]} {r[2][:20]:20s}->{r[4][:20]:20s} ab{r[6]} an{r[7]}  heute {r[8]:4d} -> Soll {r[9]:4d} ({r[10]:+d})  {r[11]}")
print("\n=== Überholbedarf")
for r in ur: print(f"  {r[1][:28]:28s} Spr{r[2]:4d} ICE{r[3]:4d} Δ{r[4]:4d} Üb{r[6]}")
con.close()
