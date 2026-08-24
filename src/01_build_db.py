import csv, sqlite3, os, datetime, collections

G = os.path.expanduser('~/bahn/data/gtfs_fv')
DB = os.path.expanduser('~/bahn/bahn.db')
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB); cur = con.cursor()

def load(name):
    with open(os.path.join(G, name+'.txt'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

agency  = load('agency')
routes  = load('routes')
trips   = load('trips')
stops   = load('stops')
stimes  = load('stop_times')
cal     = load('calendar')
caldts  = load('calendar_dates')

cur.executescript("""
CREATE TABLE agency(agency_id TEXT PRIMARY KEY, agency_name TEXT);
CREATE TABLE route(route_id TEXT PRIMARY KEY, short_name TEXT, agency_id TEXT,
                   gattung TEXT, linie TEXT, produkt TEXT);
CREATE TABLE stop(stop_id TEXT PRIMARY KEY, name TEXT, parent TEXT,
                  lat REAL, lon REAL, location_type TEXT, platform TEXT);
CREATE TABLE trip(trip_id TEXT PRIMARY KEY, route_id TEXT, service_id TEXT);
CREATE TABLE stop_time(trip_id TEXT, stop_seq INTEGER, stop_id TEXT,
                       arr INTEGER, dep INTEGER, headsign TEXT);
CREATE TABLE calendar(service_id TEXT PRIMARY KEY, mo INT,di INT,mi INT,"do" INT,fr INT,sa INT,so INT,
                      start_date TEXT,end_date TEXT);
CREATE TABLE calendar_date(service_id TEXT, date TEXT, exception_type INT);
""")

cur.executemany("INSERT INTO agency VALUES(?,?)", [(a['agency_id'],a['agency_name']) for a in agency])

def split_route(sn):
    sn = (sn or '').strip()
    parts = sn.split()
    gat = parts[0] if parts else ''
    lin = parts[1] if len(parts)>1 else None
    if gat in ('ICE','ECE'): prod='ICE'
    elif gat in ('IC','EC'): prod='IC'
    elif gat in ('RJ','EN'): prod='SONSTIGE'
    else: prod='SONSTIGE'
    return gat, lin, prod

cur.executemany("INSERT INTO route VALUES(?,?,?,?,?,?)",
    [(r['route_id'], r['route_short_name'], r['agency_id'], *split_route(r['route_short_name'])) for r in routes])

cur.executemany("INSERT INTO stop VALUES(?,?,?,?,?,?,?)",
    [(s['stop_id'], s['stop_name'], s['parent_station'] or None,
      float(s['stop_lat']) if s['stop_lat'] else None,
      float(s['stop_lon']) if s['stop_lon'] else None,
      s['location_type'], s['platform_code']) for s in stops])

cur.executemany("INSERT INTO trip VALUES(?,?,?)", [(t['trip_id'],t['route_id'],t['service_id']) for t in trips])

def hms(t):
    if not t: return None
    h,m,s = t.split(':'); return int(h)*3600+int(m)*60+int(s)

cur.executemany("INSERT INTO stop_time VALUES(?,?,?,?,?,?)",
    [(x['trip_id'], int(x['stop_sequence']), x['stop_id'], hms(x['arrival_time']), hms(x['departure_time']), x['stop_headsign']) for x in stimes])

cur.executemany("INSERT INTO calendar VALUES(?,?,?,?,?,?,?,?,?,?)",
    [(c['service_id'],int(c['monday']),int(c['tuesday']),int(c['wednesday']),int(c['thursday']),
      int(c['friday']),int(c['saturday']),int(c['sunday']),c['start_date'],c['end_date']) for c in cal])
cur.executemany("INSERT INTO calendar_date VALUES(?,?,?)",
    [(c['service_id'],c['date'],int(c['exception_type'])) for c in caldts])

cur.executescript("""
CREATE INDEX ix_st_trip ON stop_time(trip_id, stop_seq);
CREATE INDEX ix_st_stop ON stop_time(stop_id);
CREATE INDEX ix_trip_route ON trip(route_id);
""")
con.commit()

# --- service calendar expansion -> which trips run on which date
cal_by_id = {c['service_id']: c for c in cal}
exc = collections.defaultdict(dict)
for c in caldts:
    exc[c['service_id']][c['date']] = int(c['exception_type'])

def runs(service_id, d):
    ds = d.strftime('%Y%m%d')
    e = exc.get(service_id, {}).get(ds)
    if e == 1: return True
    if e == 2: return False
    c = cal_by_id.get(service_id)
    if not c: return False
    if not (c['start_date'] <= ds <= c['end_date']): return False
    return int([c['monday'],c['tuesday'],c['wednesday'],c['thursday'],c['friday'],c['saturday'],c['sunday']][d.weekday()]) == 1

cur.execute("CREATE TABLE trip_date(trip_id TEXT, date TEXT, dow INT)")
d0 = datetime.date(2026,8,22); d1 = datetime.date(2026,9,21)
rows=[]
day = d0
while day <= d1:
    for t in trips:
        if runs(t['service_id'], day):
            rows.append((t['trip_id'], day.strftime('%Y%m%d'), day.weekday()))
    day += datetime.timedelta(days=1)
cur.executemany("INSERT INTO trip_date VALUES(?,?,?)", rows)
cur.execute("CREATE INDEX ix_td ON trip_date(date)")
cur.execute("CREATE INDEX ix_td_trip ON trip_date(trip_id)")
con.commit()

print("trip_date rows", len(rows))
for q,label in [("SELECT date,COUNT(*) FROM trip_date GROUP BY date ORDER BY date LIMIT 10","first 10 days")]:
    print(label); [print('  ',r) for r in cur.execute(q)]
print("produkt counts:", list(cur.execute("SELECT produkt,COUNT(*) FROM route GROUP BY produkt")))
con.close()
