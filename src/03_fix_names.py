import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, re, collections, os
con=sqlite3.connect(DB); cur=con.cursor()
kids=collections.defaultdict(list)
for p,n in cur.execute("SELECT parent,name FROM stop WHERE parent IS NOT NULL"): kids[p].append(n)

def norm(n):
    n=n.strip()
    m=re.match(r'^(.*),\s*Hauptbahnhof$', n)
    if m: return m.group(1)+' Hbf'
    m=re.match(r'^Bahnhof,\s*(.*)$', n)
    if m: return m.group(1)
    m=re.match(r'^(.*),\s*Hbf$', n)
    if m: return m.group(1)+' Hbf'
    n=re.sub(r'\(S\)$','',n)
    return n

OVER={'416646':'Erfurt Hbf','659783':'Kiel Hbf','526634':'Freiburg(Breisgau) Hbf'}
upd=[]
for p,ns in kids.items():
    if p in OVER: upd.append((OVER[p],p)); continue
    c=collections.Counter(norm(x) for x in ns)
    best=sorted(c.items(), key=lambda kv:(-kv[1], len(kv[0])))[0][0]
    upd.append((best,p))
cur.executemany("UPDATE station SET name=? WHERE station_id=?", upd)
con.commit()
print('renamed', len(upd))
bad=[r for r in cur.execute("SELECT station_id,name,bundesland FROM station WHERE land_iso='DE' AND (name LIKE '%Hauptbahnhof%' OR name LIKE 'Bahnhof%' OR name LIKE '%,%')")]
print('verdächtig:', bad)
con.close()
