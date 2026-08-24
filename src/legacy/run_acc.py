import opt2, pesp2, json, time
rows=opt2.load()
for acc in (3,6):
    t=time.time()
    r=pesp2.solve(rows, anchor='Berlin Hbf', max_acc=acc, acc_cost=4.0, time_limit=1000, mip_gap=0.003)
    if not r: print(acc,'keine Lösung',flush=True); continue
    print(f"max. Beschleunigung {acc} min: Kosten {r['kosten']} ({r['kosten_je_gewicht']}/Gewicht) "
          f"Sollband {r['sollband_pct']} % Ø Reserve {r['reserve_pct']} % Kanten mit Verkürzung {r['beschl']} "
          f"{'optimal' if r['optimal'] else 'Zeitlimit'} {round(time.time()-t)} s", flush=True)
    json.dump(r, open(f'/root/bahn/pesp_acc{acc}.json','w'), ensure_ascii=False)
