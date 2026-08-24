import opt2, pesp, json, time, sqlite3, collections, os
rows=opt2.load()
res={}
# --- Zentrierung: Prioritätsknoten (exakt, moderates Zeitlimit)
CAND=['Frankfurt(Main)Hbf','Hannover Hbf','Mannheim Hbf','Köln Hbf','Nürnberg Hbf','Kassel-Wilhelmshöhe','Fulda','Berlin Hbf']
base=json.load(open('/root/bahn/pesp_N1.json'))
def qual(kanten,node,wkey=7):
    e=[k for k in kanten if k[0]==node or k[1]==node]; w=sum(x[wkey] for x in e)
    return {'kanten':len(e),'gewicht':round(w,1),
            'reserve':round(sum(x[wkey]*max(x[6],0) for x in e)/w,2),
            'sollband':round(100*sum(x[wkey] for x in e if 0<=x[6]<=7)/w,1),
            'max_zuschlag':max(x[5] for x in e)}
res['basis']={'kosten_je_gewicht':base['kosten_je_gewicht'],'reserve_pct':base['reserve_pct'],
              'sollband_pct':base['sollband_pct'],
              'knoten':{n:qual(base['kanten'],n) for n in CAND}}
print('Basis (exakt):',res['basis']['kosten_je_gewicht'], res['basis']['reserve_pct'],'%',flush=True)
res['zentriert']={}
for n in CAND:
    t=time.time()
    r=pesp.solve_exact(rows, anchor='Berlin Hbf', max_acc=0, prio=n, prio_factor=6.0,
                       time_limit=260, mip_gap=0.004)
    if r is None: continue
    w=sum(x[7] for x in r['kanten']); wres=sum(x[7]*max(x[6],0) for x in r['kanten'])
    band=sum(x[7] for x in r['kanten'] if 0<=x[6]<=7)
    res['zentriert'][n]={'knoten':qual(r['kanten'],n),'netz_reserve':round(wres/w,2),
                         'netz_sollband':round(100*band/w,1),'optimal':r['status']==0}
    b=res['basis']['knoten'][n]
    print(f"{n[:26]:26s} Knoten Reserve {res['zentriert'][n]['knoten']['reserve']:5.2f} % (Basis {b['reserve']:5.2f} %) | "
          f"Netz {res['zentriert'][n]['netz_reserve']:5.2f} % (Basis {base['reserve_pct']:5.2f} %) | "
          f"{'optimal' if r['status']==0 else 'Zeitlimit'} {round(time.time()-t)} s", flush=True)
json.dump(res, open('/root/bahn/zentrierung_exakt.json','w'), ensure_ascii=False, indent=1)
