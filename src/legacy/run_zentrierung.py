import json, opt2, statistics as st
rows=opt2.load()
CAND=['Frankfurt(Main)Hbf','Hannover Hbf','Mannheim Hbf','Köln Hbf','Nürnberg Hbf','Kassel-Wilhelmshöhe',
      'Fulda','Berlin Hbf','München Hbf','Würzburg Hbf','Erfurt Hbf','Hamburg Hbf']
base=opt2.solve(rows, allow_acc=False, runs=700)
def quality(res, node):
    e=[k for k in res['kanten'] if k[0]==node or k[1]==node]
    w=sum(x[7] for x in e)
    return {'kanten':len(e),'gewicht':round(w,1),
            'mittlere_reserve':round(sum(x[7]*max(x[6],0) for x in e)/w,2),
            'max_zuschlag':max(x[5] for x in e),
            'im_sollband_pct':round(100*sum(x[7] for x in e if 0<=x[6]<=7)/w,1)}
out={'basis':{'kosten':base['kosten'],'kosten_je_gewicht':base['kosten_je_gewicht'],
              'sollband_pct':base['sollband_pct'],'reserve_pct':base['reserve_pct'],
              'knoten':{n:quality(base,n) for n in CAND}}, 'zentriert':{}}
print(f"Basis (keine Zentrierung): Kosten/Gewicht {base['kosten_je_gewicht']}  Sollband {base['sollband_pct']} %  Ø Reserve {base['reserve_pct']} %", flush=True)
for n in CAND:
    r=opt2.solve(rows, allow_acc=False, prio=n, prio_factor=6.0, runs=350)
    q=quality(r,n)
    # Kosten des Restnetzes mit Originalgewichten neu bewerten
    w=sum(x[7] for x in r['kanten']); wres=sum(x[7]*max(x[6],0) for x in r['kanten'])
    band=sum(x[7] for x in r['kanten'] if 0<=x[6]<=7)
    out['zentriert'][n]={'knoten':q,'netz_reserve_pct':round(wres/w,2),'netz_sollband_pct':round(100*band/w,1)}
    print(f"{n[:28]:28s} Knoten: Ø Reserve {q['mittlere_reserve']:5.2f} % (Basis {out['basis']['knoten'][n]['mittlere_reserve']:5.2f} %) "
          f"Sollband {q['im_sollband_pct']:5.1f} % (Basis {out['basis']['knoten'][n]['im_sollband_pct']:5.1f} %) | "
          f"Netz: Ø Reserve {out['zentriert'][n]['netz_reserve_pct']:5.2f} % (Basis {base['reserve_pct']:5.2f} %)", flush=True)
json.dump(out, open('zentrierung.json','w'), ensure_ascii=False, indent=1)
