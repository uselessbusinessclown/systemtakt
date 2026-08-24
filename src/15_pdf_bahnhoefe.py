
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, collections, os, sys
from pdfbase import *
from reportlab.lib.colors import HexColor
con=sqlite3.connect(DB); cur=con.cursor()
PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
KZ=dict(cur.execute("SELECT name,knotenzeit FROM itf_knotenzeit"))
KAN=dict(cur.execute("SELECT name,ankunft FROM itf_knotenzeit"))
KAB=dict(cur.execute("SELECT name,abfahrt FROM itf_knotenzeit"))
META={r[0]:r[1:] for r in cur.execute("SELECT name,bundesland,land,stadt FROM bahnhof_bedienung")}
GROSS={n for n,h in cur.execute("SELECT name,halte_tag FROM bahnhof_bedienung") if h>=25}
OUT=os.path.join(ROOT, 'Bahnhofsfahrplaene.pdf')
D=Doc(OUT, landscape_=False, title='Systemtakt Deutschland – Bahnhofsfahrpläne',
      subject='Abfahrts- und Ankunftstafeln, Szenario A, 5–23 Uhr')
c=D.c; W,H=D.W,D.H; LM,RM,TM=26,26,26

paths=collections.defaultdict(list)
for zid,f,s,a,b in cur.execute("SELECT zug_id,folge,station,an,ab FROM fahrplan_halt ORDER BY zug_id,folge"):
    paths[zid].append((s,a,b))
ZUG={r[0]:r[1:] for r in cur.execute("SELECT zug_id,linie,kategorie,von,nach,takt FROM fahrplan_zug")}
byst=collections.defaultdict(list)
for zid,hs in paths.items():
    lin,kat,von,nach,takt=ZUG[zid]
    for i,(s,a,b) in enumerate(hs):
        ueber=[x[0] for x in hs[i+1:] if x[0] in PHI or x[0] in GROSS][:3]
        byst[s].append((b,a,lin,kat,hs[-1][0],ueber,i==len(hs)-1,i==0,hs[0][0]))
STATIONS=sorted(byst, key=lambda s:(META.get(s,('','',''))[1]!='DE', s))
def stationhead(s, nab, nan):
    bl,land,stadt=META.get(s,('','',''))
    c.setFillColor(NAVY); c.rect(LM,H-TM-26,W-LM-RM,26,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont('Helvetica-Bold',14); c.drawString(LM+8,H-TM-18,s[:52])
    c.setFont('Helvetica',8)
    c.drawRightString(W-RM-8,H-TM-17, f"{nab} Abfahrten · {nan} Ankünfte am Tag")
    c.setFillColor(MUT); c.setFont('Helvetica',7.5)
    sub=f"{bl or land or ''}"
    if s in PHI: sub+=f"   ·   Vollknoten  Knotenzeit {KZ[s]}   ·   Ankunft {KAN[s]}   ·   Abfahrt {KAB[s]}"
    else: sub+="   ·   Durchgangshalt ohne Knotenbindung"
    c.drawString(LM+2,H-TM-38,sub)
    c.setStrokeColor(LINE); c.setLineWidth(.6); c.line(LM,H-TM-44,W-RM,H-TM-44)
# --- Vorlauf: Seitenzahlen
def pages_for(s):
    ent=byst[s]
    ab=[e for e in ent if e[0] is not None]; an=[e for e in ent if e[6]]
    rh=9.6; y_top=H-TM-58; rpc=int((y_top-46)/rh); pp=rpc*2
    items=len(ab)+(1 if an else 0)+len(an)
    return max(1,(items+pp-1)//pp)
PP=[(s,pages_for(s)) for s in STATIONS]
IDXROWS=62
INHALT=max(1,(len(PP)+IDXROWS*2-1)//(IDXROWS*2))
VOR=2+INHALT
def titel():
    D.newpage()
    c.setFillColor(NAVY); c.rect(0,H-230,W,230,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont('Helvetica-Bold',30); c.drawString(LM,H-110,'Bahnhofsfahrpläne')
    c.setFont('Helvetica',13); c.setFillColor(HexColor('#B9C7DA'))
    c.drawString(LM,H-136,'Systemtakt Deutschland · Abfahrt und Ankunft an jedem Bahnhof')
    c.setFont('Helvetica',9.5)
    c.drawString(LM,H-162,'Szenario A – Taktordnung · Betriebszeit 5 bis 23 Uhr · 20 Vollknoten · neubaufrei')
    c.setFillColor(INK); c.setFont('Helvetica',9.5); y=H-275
    for t in ['Dieser Band enthält für jeden vom Fernverkehr bedienten Bahnhof den vollständigen Tagesfahrplan',
              'des entworfenen Systemtakts: alle Abfahrten mit Linie, Ziel und Fahrweg, darunter alle Ankünfte',
              'endender Züge.','',
              'An den zwanzig Vollknoten erkennt man die Taktstruktur unmittelbar: Die Abfahrten sammeln sich',
              'in zwei kurzen Fenstern je Stunde, weil dort alle Linien gleichzeitig stehen und jeder Anschluss',
              'in jede Richtung besteht. An Durchgangshalten verteilen sich die Abfahrten frei über die Stunde.']:
        c.drawString(LM,y,t); y-=14
    c.setFont('Helvetica',7.5); c.setFillColor(MUT)
    c.drawString(LM,58,'Datengrundlage: DELFI e. V. / gtfs.de, Fahrplan 22.08.–21.09.2026 · Knotenplan exakt gelöst (MILP, HiGHS)')
    c.drawString(LM,46,'Stand 23. August 2026 · Alle Zeiten sind Sollzeiten des Entwurfs, kein gültiger Fahrplan')
    D.footer('Systemtakt Deutschland · Bahnhofsfahrpläne')
def legende2():
    D.newpage()
    c.setFillColor(NAVY); c.setFont('Helvetica-Bold',17); c.drawString(LM,H-58,'So lesen Sie die Tafeln')
    c.setFillColor(INK); c.setFont('Helvetica',9.5); y=H-90
    for t in ['Der Kopf nennt den Bahnhof, das Bundesland und die Rolle im Takt. Bei Vollknoten stehen dort',
              'die Knotenzeit sowie die Ankunfts- und Abfahrtsfenster beider Richtungen.','',
              'Die Tafel liest sich in zwei Spalten von links oben nach rechts unten, nach Uhrzeit geordnet.',
              'Jede Zeile nennt Abfahrtszeit, Linie, Ziel und die wichtigsten Unterwegshalte.','',
              'Farben kennzeichnen die Produktebene: rot ICE-Sprinter, blau ICE, braun IC und EC.',
              'Nach dem Block ANKÜNFTE folgen die Züge, die hier enden; dort steht statt des Ziels der Startbahnhof.',
              'Zeiten nach Mitternacht sind als 24:xx und 25:xx angegeben.']:
        c.drawString(LM,y,t); y-=14
    D.footer('Systemtakt Deutschland · Bahnhofsfahrpläne')
def inhalt2():
    off=0; i=0
    while i<len(PP):
        D.newpage()
        c.setFillColor(NAVY); c.setFont('Helvetica-Bold',17); c.drawString(LM,H-58,'Bahnhöfe von A bis Z')
        c.setFont('Helvetica-Bold',6); c.setFillColor(MUT)
        c.drawString(LM,H-78,'BAHNHOF'); c.drawString(LM+250,H-78,'BAHNHOF'); c.drawRightString(W-RM,H-78,'SEITE')
        c.setStrokeColor(LINE); c.line(LM,H-83,W-RM,H-83)
        chunk=PP[i:i+IDXROWS*2]
        for j,(st,np_) in enumerate(chunk):
            col=j//IDXROWS; row=j%IDXROWS
            x=LM+col*250; y=H-96-row*10.6
            page=VOR+sum(p for _,p in PP[:i+j])+1
            c.setFillColor(INK if st in PHI else HexColor('#3A434D'))
            c.setFont('Helvetica-Bold' if st in PHI else 'Helvetica',7)
            c.drawString(x,y,(('● ' if st in PHI else '   ')+st)[:34])
            c.setFillColor(MUT); c.setFont('Helvetica',7)
            c.drawRightString(x+238,y,str(page))
        i+=IDXROWS*2
        D.footer('Systemtakt Deutschland · Bahnhofsfahrpläne')
titel(); legende2(); inhalt2()
for s in STATIONS:
    ent=byst[s]
    ab=sorted([e for e in ent if e[0] is not None], key=lambda e:e[0])
    an=sorted([e for e in ent if e[6]], key=lambda e:(e[1] or 0))
    D.bookmark(s,0)
    colw=(W-LM-RM-10)/2; rh=9.6
    y_top=H-TM-58
    rows_per_col=int((y_top-46)/rh)
    per_page=rows_per_col*2
    items=[('ab',e) for e in ab]+([('--',None)] if an else [])+[('an',e) for e in an]
    pages=[items[i:i+per_page] for i in range(0,len(items),per_page)] or [[]]
    for pi,pg in enumerate(pages):
        D.newpage(); stationhead(s,len(ab),len(an))
        for ci in range(2):
            chunk=pg[ci*rows_per_col:(ci+1)*rows_per_col]
            if not chunk: continue
            x=LM+ci*(colw+10); y=y_top
            c.setFont('Helvetica-Bold',6); c.setFillColor(MUT)
            c.drawString(x,y+4,'ZEIT'); c.drawString(x+34,y+4,'ZUG'); c.drawString(x+92,y+4,'RICHTUNG / ÜBER')
            c.setStrokeColor(LINE2); c.line(x,y,x+colw,y)
            for k,(typ,e) in enumerate(chunk):
                yy=y-rh*(k+1)+2.5
                if typ=='--':
                    c.setFillColor(NAVY); c.setFont('Helvetica-Bold',7)
                    c.drawString(x,yy,'ANKÜNFTE'); continue
                t,a,lin,kat,ziel,ueber,isend,isstart,start=e
                if k%2==1:
                    c.setFillColor(ZEBRA); c.rect(x,yy-2.4,colw,rh,fill=1,stroke=0)
                c.setFillColor(INK); c.setFont('Helvetica-Bold',7.2)
                c.drawString(x, yy, hm(t if typ=='ab' else a))
                c.setFillColor(CATCOL.get(kat,ICE)); c.setFont('Helvetica-Bold',6.4)
                c.drawString(x+34, yy, lin[:14])
                c.setFillColor(INK); c.setFont('Helvetica',6.6)
                dest = ziel if typ=='ab' else start
                c.drawString(x+92, yy, dest[:26])
                if typ=='ab' and ueber:
                    c.setFillColor(MUT); c.setFont('Helvetica',5.6)
                    txt='über '+', '.join(u.replace(' Hbf','') for u in ueber)
                    c.drawString(x+92+c.stringWidth(dest[:26],'Helvetica',6.6)+5, yy, txt[:44])
        c.setFont('Helvetica',5.8); c.setFillColor(MUT)
        c.drawString(LM,34,'Farbcode: rot = ICE-Sprinter · blau = ICE · braun = IC/EC.   Zeiten nach Mitternacht als 24:xx.')
        D.footer(f"{s}" + (f"   ({pi+1}/{len(pages)})" if len(pages)>1 else ""))
D.save()
print('Bahnhöfe',len(STATIONS),'Seiten',D.page, os.path.getsize(OUT)//1024,'KB')
