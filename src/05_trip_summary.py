import sqlite3, math, os, collections, statistics as st
con = sqlite3.connect(os.path.expanduser('~/bahn/bahn.db')); cur=con.cursor()
cur.execute("UPDATE station SET land_iso='FR' WHERE land='France'")

def hav(a,b,c,d):
    R=6371.0088; p=math.pi/180
    return 2*R*math.asin(math.sqrt(math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2))

S = {r[0]:(r[1],r[2],r[3],r[4]) for r in cur.execute("SELECT station_id,name,lat,lon,land_iso FROM station")}
s2st = dict(cur.execute("SELECT stop_id,station_id FROM stop_station"))

seq = collections.defaultdict(list)
for tid, sq, sid, arr, dep in cur.execute("SELECT trip_id,stop_seq,stop_id,arr,dep FROM stop_time ORDER BY trip_id,stop_seq"):
    seq[tid].append((sq, s2st[sid], arr, dep))

rinfo = {r[0]:(r[1],r[2],r[3],r[4],r[5]) for r in cur.execute("SELECT route_id,short_name,gattung,linie,produkt,agency_id FROM route")}
ag = dict(cur.execute("SELECT agency_id,agency_name FROM agency"))
tr = {t[0]:(t[1],t[2]) for t in cur.execute("SELECT trip_id,route_id,service_id FROM trip")}
days = collections.Counter(); wd = collections.defaultdict(set)
for tid,date,dow in cur.execute("SELECT trip_id,date,dow FROM trip_date"):
    days[tid]+=1; wd[tid].add(dow)

cur.executescript("""
DROP TABLE IF EXISTS trip_summary;
CREATE TABLE trip_summary(
 trip_id TEXT PRIMARY KEY, route_id TEXT, linie TEXT, gattung TEXT, produkt TEXT,
 betreiber TEXT, von_id TEXT, von TEXT, nach_id TEXT, nach TEXT,
 abfahrt INT, ankunft INT, dauer_min INT, halte INT,
 km_luftlinie REAL, vschnitt_kmh REAL, halt_je_100km REAL,
 verkehrstage INT, wochentage TEXT, de_anteil REAL, inland INT);
""")
rows=[]
for tid, sts in seq.items():
    if len(sts) < 2: continue
    rid, svc = tr[tid]
    sn, gat, lin, prod, agid = rinfo[rid]
    a = sts[0]; z = sts[-1]
    dep = a[3] if a[3] is not None else a[2]
    arr = z[2] if z[2] is not None else z[3]
    dur = (arr-dep)//60 if (arr is not None and dep is not None) else None
    dist=0.0
    for i in range(len(sts)-1):
        p=S[sts[i][1]]; q=S[sts[i+1][1]]
        dist += hav(p[1],p[2],q[1],q[2])
    de = sum(1 for x in sts if S[x[1]][3]=='DE')/len(sts)
    v = round(dist/(dur/60),1) if dur and dur>0 else None
    rows.append((tid, rid, lin, gat, prod, ag.get(agid,''),
                 a[1], S[a[1]][0], z[1], S[z[1]][0],
                 dep, arr, dur, len(sts), round(dist,1), v,
                 round((len(sts)-2)/(dist/100),2) if dist>30 else None,
                 days[tid], ''.join(str(d) for d in sorted(wd[tid])),
                 round(de,3), 1 if de==1.0 else 0))
cur.executemany("INSERT INTO trip_summary VALUES(%s)" % ','.join('?'*21), rows)
con.commit()
print('trips summarised', len(rows))
print('\nICE-Fahrten nach Linie (Top 20, tägl. Fahrten):')
for r in cur.execute("""SELECT linie, gattung, COUNT(*) n, ROUND(AVG(dauer_min)) d, ROUND(AVG(halte),1) h, ROUND(AVG(vschnitt_kmh),1) v
 FROM trip_summary WHERE produkt='ICE' GROUP BY linie,gattung ORDER BY n DESC LIMIT 25"""): print('  ',r)
con.close()
